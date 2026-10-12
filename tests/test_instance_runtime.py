"""Pinned selection and failure recovery never restore old user records."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import instance_runtime as runtime


def command(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, stderr=subprocess.STDOUT, text=True).strip()


def commit(root):
    command('git', 'add', '.', cwd=root)
    command('git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
            'commit', '-qm', 'fixture', cwd=root)


def repo(root, kind, version='A', reject=False):
    root.mkdir()
    command('git', 'init', '-q', cwd=root)
    if kind == 'brain':
        (root / 'board').mkdir()
        for name in ['_theme.py', '_state.py']:
            (root / 'board' / name).write_text('# fixture '+version+'\n')
    else:
        (root / 'scripts').mkdir()
        (root / 'scripts/organism_board.py').write_text(f'''import sys, os, json
from pathlib import Path
profile = json.loads(Path(sys.argv[sys.argv.index('--instance') + 1]).read_text())
assert not profile.get('unsupported'), 'incompatible current configuration'
assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
assert Path(os.environ['PYAUTO_BRAIN'], 'board/_state.py').is_file()
if {reject!r}: raise SystemExit('candidate rejected')
print({'Runtime '+version!r})
''')
    commit(root)
    return root


@pytest.fixture
def pilot(tmp_path):
    data = tmp_path / 'data'; data.mkdir()
    profile = data / 'instance.json'; profile.write_text('{"name":"Mira"}')
    (data / 'projects.json').write_text('{"Spectra":"existing"}')
    records = tmp_path / 'records'; records.mkdir()
    for name in ['mind-task.md','research.md','broca-receipt.json']:
        (records / name).write_text('Keep baseline-A: '+name)
    repos = tmp_path / 'repos.yaml'; repos.write_text('repos: {}')
    brain = repo(tmp_path / 'brain', 'brain')
    old = repo(tmp_path / 'old', 'scientist', 'A')
    new = repo(tmp_path / 'new', 'scientist', 'B')
    manifest = data / 'runtime.json'
    prepared = runtime.prepare('initialize',manifest,instance=profile,repos=repos,
                               scientist=old,brain=brain,protect=[records])
    return manifest, profile, repos, records, brain, old, new, prepared


def test_initialize_upgrade_rollback_and_launcher_preserve_current_records(pilot, capsys):
    manifest, profile, repos, records, brain, old, new, prepared = pilot
    assert not manifest.exists()
    before = runtime.fingerprints([profile.parent, repos, records], [manifest])
    assert runtime.apply(prepared)
    assert runtime.main(['check','--manifest',str(manifest)]) == 0
    assert 'Runtime A' in capsys.readouterr().out
    upgrade = runtime.prepare('upgrade',manifest,scientist=new,brain=brain)
    assert json.loads(manifest.read_text())['current']['scientist']['path'] == str(old)
    assert runtime.apply(upgrade)
    assert runtime.main(['render','--manifest',str(manifest)]) == 0
    assert 'Runtime B' in capsys.readouterr().out
    assert runtime.fingerprints([profile.parent,repos,records],[manifest]) == before
    (records / 'research.md').write_text('Newer baseline-B after upgrade')
    later = runtime.fingerprints([profile.parent,repos,records],[manifest])
    assert runtime.apply(runtime.prepare('rollback',manifest))
    assert runtime.fingerprints([profile.parent,repos,records],[manifest]) == later
    assert runtime.main(['check','--manifest',str(manifest)]) == 0
    assert 'Runtime A' in capsys.readouterr().out
    assert not runtime.apply(runtime.prepare('upgrade',manifest,scientist=old,brain=brain))


def test_bad_candidate_never_changes_selection_or_records(pilot):
    manifest, profile, repos, records, brain, old, new, prepared = pilot
    runtime.apply(prepared)
    before = runtime.fingerprints([profile.parent,repos,records])
    script=new/'scripts/organism_board.py'; script.write_text("raise SystemExit('invalid candidate')\n"); commit(new)
    with pytest.raises(ValueError,match='invalid candidate'):
        runtime.prepare('upgrade',manifest,scientist=new,brain=brain)
    assert runtime.fingerprints([profile.parent,repos,records]) == before


def test_dirty_or_changed_pin_is_refused(pilot):
    manifest, _, _, _, brain, old, new, prepared = pilot
    runtime.apply(prepared)
    (new/'untracked.txt').write_text('unreviewed')
    with pytest.raises(ValueError,match='dirty'):
        runtime.prepare('upgrade',manifest,scientist=new,brain=brain)
    (old/'version.txt').write_text('changed revision');commit(old)
    with pytest.raises(ValueError,match='revision changed'):
        runtime.observe(runtime.load(manifest),manifest,runtime.load(manifest)['current'])


@pytest.mark.parametrize('which',['manifest','profile','record','pin'])
def test_stale_plan_never_applies(pilot,which):
    manifest, profile, _, records, brain, old, new, prepared=pilot
    runtime.apply(prepared)
    change=runtime.prepare('upgrade',manifest,scientist=new,brain=brain)
    target={'manifest':manifest,'profile':profile,'record':records/'research.md','pin':new/'new.txt'}[which]
    target.write_bytes(target.read_bytes()+b'\n' if target.exists() else b'new')
    before=manifest.read_bytes()
    with pytest.raises(ValueError): runtime.apply(change)
    assert manifest.read_bytes()==before
    assert not list(manifest.parent.glob('.scientist-runtime-*'))


def test_failed_atomic_replace_preserves_manifest(pilot,monkeypatch):
    manifest, _, _, _, brain, _, new, prepared=pilot
    runtime.apply(prepared)
    change=runtime.prepare('upgrade',manifest,scientist=new,brain=brain); before=manifest.read_bytes()
    def fail(*args): raise OSError('write refused')
    monkeypatch.setattr(runtime.os,'replace',fail)
    with pytest.raises(OSError): runtime.apply(change)
    assert manifest.read_bytes()==before
    assert not list(manifest.parent.glob('.scientist-runtime-*'))


def test_rollback_requires_previous_compatible_with_current_data(pilot):
    manifest, profile, _, _, brain, old, new, prepared=pilot
    runtime.apply(prepared)
    with pytest.raises(ValueError,match='no previous'): runtime.prepare('rollback',manifest)
    runtime.apply(runtime.prepare('upgrade',manifest,scientist=new,brain=brain))
    profile.write_text('{"unsupported":true}')
    before=manifest.read_bytes()
    with pytest.raises(ValueError,match='incompatible'): runtime.prepare('rollback',manifest)
    assert manifest.read_bytes()==before and profile.read_text()=='{"unsupported":true}'
    profile.write_text('{}')
    (old/'scripts/organism_board.py').unlink()
    with pytest.raises(ValueError): runtime.prepare('rollback',manifest)
    assert manifest.read_bytes()==before


def test_rollback_can_recover_from_broken_current_runtime(pilot):
    manifest, _, _, _, brain, _, new, prepared=pilot
    runtime.apply(prepared)
    runtime.apply(runtime.prepare('upgrade',manifest,scientist=new,brain=brain))
    (new/'scripts/organism_board.py').unlink()
    assert runtime.apply(runtime.prepare('rollback',manifest))


def test_mutating_candidate_is_detected_not_silently_restored(pilot):
    manifest, _, _, records, brain, _, new, prepared=pilot
    runtime.apply(prepared);before=manifest.read_bytes()
    (new/'scripts/organism_board.py').write_text(f"from pathlib import Path\nPath({str(records/'research.md')!r}).write_text('unexpected edit')\n")
    commit(new)
    with pytest.raises(ValueError,match='protected records changed'):
        runtime.prepare('upgrade',manifest,scientist=new,brain=brain)
    assert manifest.read_bytes()==before
    assert (records/'research.md').read_text()=='unexpected edit'


def test_protected_symlinks_and_framework_overlap_refused(pilot):
    manifest, profile, _, records, brain, _, new, prepared=pilot
    runtime.apply(prepared)
    (records/'link').symlink_to(profile)
    with pytest.raises(ValueError,match='symlink'):
        runtime.prepare('upgrade',manifest,scientist=new,brain=brain)
    data=runtime.load(manifest);data['protected'].append(str(new))
    with pytest.raises(ValueError,match='separate'):
        runtime.boundaries(data,manifest,{'scientist':runtime.pin(new,'scientist'),'brain':runtime.pin(brain,'brain')})


def test_real_owner_validator_with_independent_configuration(tmp_path):
    import organism_board
    source=Path(__file__).resolve().parents[1]
    brain_source=Path(organism_board.theme().__file__).resolve().parents[1]
    scientist=tmp_path/'scientist';brain=tmp_path/'brain'
    for src,dst in [(source,scientist),(brain_source,brain)]:
        command('git','clone','--quiet','--shared',str(src),str(dst))
    data=tmp_path/'config';data.mkdir()
    (data/'instance.json').write_text(json.dumps({'schema_version':1,'name':'Mira','repo':'scientist',
        'pages_url':'https://example.invalid/mira/','projects':'projects.json','organs':{}}))
    (data/'projects.json').write_text('{"schema_version":1,"resources":{},"projects":{}}')
    repos=tmp_path/'repos.yaml';repos.write_text('repos:\n  scientist:\n    github: Research/Mira\n')
    manifest=data/'runtime.json'
    p=runtime.prepare('initialize',manifest,instance=data/'instance.json',repos=repos,scientist=scientist,brain=brain)
    assert 'configuration valid' in p['validation']
    assert runtime.apply(p)
    before=runtime.fingerprints([data,repos],[manifest])
    _,html=runtime.observe(runtime.load(manifest),manifest,p['data']['current'],render=True)
    assert 'Mira Dashboard' in html
    assert runtime.fingerprints([data,repos],[manifest])==before
    # A second revision retains the real owner validator. Create it locally so
    # this test also works on CI's shallow checkout without fetching history.
    older=tmp_path/'older-scientist'
    command('git','clone','--quiet','--shared',str(source),str(older))
    (older/'runtime-fixture-revision.txt').write_text('second local framework revision')
    commit(older)
    assert runtime.apply(runtime.prepare('upgrade',manifest,scientist=older,brain=brain))
    assert runtime.apply(runtime.prepare('rollback',manifest))
    assert runtime.fingerprints([data,repos],[manifest])==before


def test_changed_recovery_pair_blocks_upgrade_save(pilot):
    manifest, _, _, _, brain, old, new, prepared=pilot
    runtime.apply(prepared)
    upgrade=runtime.prepare('upgrade',manifest,scientist=new,brain=brain)
    (old/'new.txt').write_text('changed after preview')
    before=manifest.read_bytes()
    with pytest.raises(ValueError,match='dirty'): runtime.apply(upgrade)
    assert manifest.read_bytes()==before


def test_manifest_mutation_during_check_is_detected(pilot):
    manifest, _, _, _, brain, old, _, prepared=pilot
    runtime.apply(prepared)
    script=old/'scripts/organism_board.py'
    script.write_text(f"from pathlib import Path\nPath({str(manifest)!r}).write_text('{{}}')\n")
    commit(old)
    data=runtime.load(manifest)
    data['current']['scientist']=runtime.pin(old,'scientist')
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='manifest changed'):
        runtime.observe(data,manifest,data['current'])


def test_identical_selection_keeps_previous_even_if_it_is_no_longer_available(pilot):
    manifest, _, _, _, brain, old, new, prepared=pilot
    runtime.apply(prepared)
    runtime.apply(runtime.prepare('upgrade',manifest,scientist=new,brain=brain))
    (old/'scripts/organism_board.py').unlink()
    before=manifest.read_bytes()
    assert not runtime.apply(runtime.prepare('upgrade',manifest,scientist=new,brain=brain))
    assert manifest.read_bytes()==before

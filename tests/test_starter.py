"""Initialization preserves user records and uses the existing render contract."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import starter
import instance_profile
import organism_board


@pytest.fixture
def inputs(tmp_path):
    repos = tmp_path / 'repos.yaml'
    repos.write_text('repos:\n  researcher:\n    github: ExampleResearch/IndependentScience\n')
    return tmp_path / 'my scientist', repos


def args(inputs):
    destination, repos = inputs
    return [str(destination), '--repos', str(repos), '--name', 'Independent Science',
            '--repo', 'researcher', '--pages-url', 'https://example.invalid/science/']


def test_preview_then_apply_and_repeat_preserves_records(inputs):
    destination, repos = inputs
    original = repos.read_bytes()
    starter.main(args(inputs))
    assert not destination.exists()
    starter.main(args(inputs) + ['--apply'])
    assert set(p.name for p in destination.iterdir()) == {'instance.json', 'projects.json', 'SETUP.md'}
    profile = json.loads((destination / 'instance.json').read_text())
    assert profile['name'] == 'Independent Science'
    assert profile['organs'] == {}
    (destination / 'projects.json').write_text('user records')
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    with pytest.raises(SystemExit) as exc:
        starter.main(args(inputs) + ['--apply'])
    assert exc.value.code == 2
    assert before == {p.name: p.read_bytes() for p in destination.iterdir()}
    assert repos.read_bytes() == original


@pytest.mark.parametrize('key,value', [('--repo', 'missing'), ('--pages-url', 'http://bad'), ('--name', '\n')])
def test_invalid_input_leaves_no_directory(inputs, key, value):
    argv = args(inputs)
    argv[argv.index(key) + 1] = value
    with pytest.raises(SystemExit):
        starter.main(argv + ['--apply'])
    assert not inputs[0].exists()


def test_symlink_destination_refused(inputs):
    destination, repos = inputs
    destination.symlink_to(destination.parent / 'absent', target_is_directory=True)
    with pytest.raises(SystemExit):
        starter.main(args(inputs) + ['--apply'])
    assert destination.is_symlink()
    assert not destination.exists()


def test_creation_race_does_not_overwrite(inputs):
    destination, repos = inputs
    files = starter.plan(destination, repos, 'Independent', 'researcher', 'https://example.invalid')
    destination.mkdir()
    record = destination / 'instance.json'
    record.write_text('existing')
    with pytest.raises(FileExistsError):
        starter.initialize(destination, files)
    assert record.read_text() == 'existing'


def test_resume_commands_and_profile_contract(inputs):
    destination, repos = inputs
    starter.main(args(inputs) + ['--apply'])
    # Real loader and renderer consume the generated files, without feed requests.
    theme = organism_board.theme()
    profile, projects = instance_profile.load(destination / 'instance.json', repos, theme)
    assert profile['boards'] == []
    assert projects == destination / 'projects.json'
    assert json.loads(projects.read_text())['projects'] == {}
    setup = (destination / 'SETUP.md').read_text()
    assert str(repos) in setup
    assert '--check-instance' in setup
    assert 'not a full Scientist installation' in setup

"""Navigation preserves instance isolation and the existing onboarding wording."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from instance_navigation import inactive_content, render
import organism_board as ob


def test_content_is_verbatim_for_available_and_pending():
    organ = {'key': 'brain', 'name': 'Brain', 'role': 'Orchestration'}
    expected = ('Help me add Brain (Orchestration) to this Scientist. '
                'Read my existing profile, canonical map and Mind task. Confirm the purpose, repository '
                'identity and public board location; preview organ_lifecycle.py setup before applying. '
                'Keep it setup incomplete until connect_organ.py validates its published feed.')
    assert f'>{expected}</textarea>' in inactive_content(organ)
    pending = ('Resume setup for Brain in my existing Mind task. '
               'Read my profile and canonical map first. Validate the owner setup and published feed, '
               'then preview connect_organ.py before applying. Preserve existing records.')
    assert f'>{pending}</textarea>' in inactive_content(organ, pending=True)


def test_navigation_uses_only_explicit_connections_and_cockpit_order():
    instance = {'available': [{'key': 'brain', 'name': 'Brain', 'role': 'Orchestration'},
                              {'key': 'broca', 'name': 'Broca', 'role': 'Assistants'}],
                'setup': [{'key': 'heart', 'name': 'Heart', 'role': 'Tests',
                           'url': 'https://pending.invalid/'}],
                'boards': [{'key': 'mind', 'name': 'Mind', 'url': 'https://owner.invalid/plans/',
                            'paused': True}]}
    nav, views = render(instance)
    assert nav.index('#scientist') < nav.index('#organ-brain') < nav.index('#organ-mind') < nav.index('#organ-broca')
    assert 'data-board-src="https://owner.invalid/plans/"' in views
    assert views.count('<iframe') == 1
    assert '<p class="organ-state">Paused</p>' in views
    assert 'pending.invalid' not in views
    assert 'pyautolabs.github.io' not in nav + views
    assert 'src="https://owner.invalid/plans/"' not in views.replace('data-board-src=', '')


def test_overview_and_inactive_page_share_exact_content():
    organ = {'key': 'brain', 'name': 'Brain & <example>', 'role': 'Coordination & <tasks>'}
    instance = {'name': 'Test', 'source_url': 'https://github.com/Example/Scientist', 'boards': [],
                'available': [organ], 'setup': []}
    snapshot = {'instance': instance, 'boards': [], 'generated': '2026-10-13T12:00:00Z'}
    page = ob.render(snapshot, 'html')
    assert page.count(inactive_content(organ)) == 2
    assert 'Brain &amp; &lt;example&gt;' in page
    assert '<example>' not in page
    assert page.index('class="instance-nav"') < page.index('<main id="scientist">')


def test_collected_connected_and_paused_boards_remain_in_navigation(monkeypatch):
    instance = {'name': 'Test', 'source_url': 'https://github.com/Example/Scientist',
                'available': [], 'setup': [], 'boards': [
                    {'key': 'mind', 'name': 'Mind', 'repo': 'Plans',
                     'url': 'https://example.invalid/plans/', 'paused': True},
                    {'key': 'heart', 'name': 'Heart', 'repo': 'Checks',
                     'url': 'https://example.invalid/checks/'}]}
    monkeypatch.setattr(ob, '_get', lambda *_: '{}')
    page = ob.render(ob.collect(instance=instance), 'html')
    assert 'href="#organ-mind"' in page
    assert 'href="#organ-heart"' in page
    assert page.count('<iframe') == 2


def test_shell_uses_instance_identity_and_safe_local_toolbar_defaults():
    nav, _ = render({'repo': 'Mira & <Lab>', 'available': [], 'setup': [], 'boards': []})
    assert 'Mira &amp; &lt;Lab&gt; <span>/ Cockpit</span>' in nav
    assert 'disabled title="Awaiting work"' in nav
    assert '>●</span> IDLE</button>' in nav
    assert nav.index('cockpit-topbar') < nav.index('instance-nav') < nav.index('cockpit-toolbar')
    assert 'id="cockpit-reload"' in nav
    assert 'id="cockpit-external" href="#scientist" target="_blank"' in nav
    assert 'pyautolabs.github.io' not in nav


def test_unprofiled_dashboard_does_not_gain_cockpit_shell():
    page = ob.render({'owner': 'Example', 'boards': [], 'generated': None}, 'html')
    assert 'class="instance-cockpit"' not in page
    assert 'class="instance-shell-header"' not in page
    assert 'id="cockpit-reload"' not in page

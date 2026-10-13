"""Instance-owned cockpit navigation; optional organs never gain implicit URLs."""
from html import escape

# Match the existing cockpit's icon/label order (including Scientist first).
# This is presentation only: membership and destinations come from the profile.
ICONS = {
    'scientist': '🔭', 'brain': '🧠', 'mind': '💭', 'cortex': '🔬',
    'broca': '🗣️', 'memory': '📚', 'eyes': '👁️', 'ears': '👂',
    'heart': '❤️', 'hands': '🛠️', 'pulse': '⏱️', 'insight': '💡',
    'dna': '🧬', 'nerves': '⚡', 'gut': '♻️',
}


def inactive_content(organ, *, pending=False):
    """One verbatim description/prompt for both the overview and organ page."""
    key = organ['key']
    if pending:
        prompt = (f"Resume setup for {organ['name']} in my existing Mind task. "
                  "Read my profile and canonical map first. Validate the owner setup and published feed, "
                  "then preview connect_organ.py before applying. Preserve existing records.")
        label = f'Resume {key} setup'
    else:
        prompt = (f"Help me add {organ['name']} ({organ['role']}) to this Scientist. "
                  "Read my existing profile, canonical map and Mind task. Confirm the purpose, repository "
                  "identity and public board location; preview organ_lifecycle.py setup before applying. "
                  "Keep it setup incomplete until connect_organ.py validates its published feed.")
        label = f'Add {key}'
    note = '<p>Not connected. No feed requested.</p>' if pending else ''
    return (f'{note}<p>{escape(organ["role"])}</p>'
            f'<textarea readonly aria-label="{escape(label, quote=True)}">{escape(prompt)}</textarea>'
            f'<button type="button" class="copy organ-setup-copy" data-cmd="{escape(prompt, quote=True)}" '
            f'aria-label="Copy {escape(label, quote=True)} prompt">Copy setup prompt</button>')


def render(instance):
    """Return navigation and local destinations without contacting any board."""
    entries = {o['key']: (o, state) for state in ('boards', 'setup', 'available')
               for o in instance.get(state, [])}
    links = ['<li><a class="board-link" href="#scientist" aria-current="page">'
             '<span class="nav-icon" aria-hidden="true">🔭</span><span>Scientist</span></a></li>']
    panels = []
    for key in dict.fromkeys([*ICONS, *entries]):
        if key not in entries:
            continue
        organ, state = entries[key]
        name = escape(organ['name'])
        status = ('Paused' if organ.get('paused') else 'Connected') if state == 'boards' else (
            'Setup incomplete' if state == 'setup' else 'Available to add')
        links.append(f'<li><a class="board-link" href="#organ-{key}" title="{name} · {status}">'
                     f'<span class="nav-icon" aria-hidden="true">{ICONS.get(key, "◉")}</span>'
                     f'<span>{name}</span></a></li>')
        if state == 'boards':
            url = escape(organ['url'], quote=True)
            content = (f'<p><a href="{url}" target="_blank" rel="noopener">Open {name} in a new tab →</a></p>'
                       f'<iframe title="{name} board" data-board-src="{url}" loading="lazy"></iframe>')
        else:
            content = inactive_content(organ, pending=state == 'setup')
        panels.append(f'<section class="instance-view" id="organ-{key}" hidden '
                      f'aria-labelledby="organ-{key}-heading"><h1 id="organ-{key}-heading" tabindex="-1">'
                      f'{name}</h1><p class="organ-state">{status}</p>{content}</section>')
    nav = ('<nav class="instance-nav" aria-label="Organ boards"><div class="nav-scroll"><ul>'
           + ''.join(links) + '</ul></div></nav>')
    return nav, ''.join(panels)


CSS = """
.instance-nav{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--line);margin-bottom:1rem}
.instance-nav .nav-scroll{overflow-x:auto;overscroll-behavior-x:contain;scrollbar-width:thin;padding:.45rem .5rem}
.instance-nav ul{display:flex;gap:.3rem;list-style:none;width:max-content;margin:0 auto;padding:0}
.instance-nav .board-link{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.15rem;min-width:76px;min-height:64px;padding:.4rem .65rem;border:1px solid transparent;border-radius:12px;color:var(--muted);font-size:.8rem;font-weight:650;text-decoration:none;box-sizing:border-box}
.instance-nav .board-link:hover{background:var(--panel,var(--bg));color:var(--fg)}
.instance-nav .board-link[aria-current=page]{color:var(--accent);border-color:var(--accent)}
.instance-nav .nav-icon{font-size:1.55rem;line-height:1.25}
.instance-nav :focus-visible,.instance-view :focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.instance-view[hidden],#scientist[hidden]{display:none!important}
.instance-view,#scientist{scroll-margin-top:7rem}
.instance-view h1{font-size:1.8rem;margin-bottom:.3rem}
.organ-state{color:var(--muted)}
.instance-view textarea{width:100%;box-sizing:border-box;min-height:10rem;font:inherit;padding:.75rem;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;resize:vertical}
button.organ-setup-copy{width:auto;height:auto;min-height:44px;padding:.5rem .8rem;margin-top:.5rem;font:inherit}
.instance-view iframe{display:block;width:100%;height:75vh;height:75dvh;min-height:360px;border:1px solid var(--line);background:var(--bg)}
"""

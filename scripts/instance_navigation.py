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
        panels.append(f'<section class="instance-view{' embedded-board' if state == 'boards' else ''}" id="organ-{key}" hidden '
                      f'aria-labelledby="organ-{key}-heading"><h1 id="organ-{key}-heading" tabindex="-1">'
                      f'{name}</h1><p class="organ-state">{status}</p>{content}</section>')
    identity = escape(instance.get('repo') or instance.get('name') or 'Scientist')
    nav = ('<nav class="instance-nav" aria-label="Organ boards"><div class="nav-scroll"><ul>'
           + ''.join(links) + '</ul></div><p class="nav-hint" hidden>Scroll for more boards →</p></nav>')
    nav = (f'<header class="instance-shell-header"><div class="cockpit-topbar"><div class="cockpit-wrap">'
           f'<a class="cockpit-home" href="#scientist">{identity} <span>/ Cockpit</span></a>'
           '<button class="cockpit-idle" type="button" disabled title="Awaiting work" '
           'aria-label="Idle — awaiting work"><span aria-hidden="true">●</span> IDLE</button>'
           f'</div></div>{nav}</header>'
           '<div class="cockpit-toolbar"><div><h1 id="cockpit-heading" tabindex="-1">Scientist</h1>'
           '<p id="cockpit-status" role="status">Overview</p></div><div class="cockpit-actions">'
           '<button class="cockpit-action" id="cockpit-reload" type="button" aria-label="Reload board" '
           'title="Reload board">↻<span>Reload</span></button>'
           '<a class="cockpit-action" id="cockpit-external" href="#scientist" target="_blank" '
           'rel="noopener" aria-label="Open board in a new tab" title="Open board in a new tab">'
           '↗<span>New tab</span></a></div></div>')
    return nav, ''.join(panels)


CSS = """
body.instance-cockpit{max-width:none;width:100%;height:100vh;height:100dvh;padding:0;margin:0;display:flex;flex-direction:column;overflow:hidden;--shell-bg:#fff;--shell-alt:#f6f6fa;--shell-text:#1c1e26;--shell-soft:#555a6e;--shell-line:#e4e4ee;--shell-brand:#7c4dff;--shell-grey:#9095a8}
@media(prefers-color-scheme:dark){body.instance-cockpit{--shell-bg:#14151a;--shell-alt:#1b1d24;--shell-text:#e8e8ef;--shell-soft:#a0a4b8;--shell-line:#2a2d38;--shell-brand:#9d7aff;--shell-grey:#6b7085}}
.instance-shell-header,.cockpit-toolbar{flex:none;background:var(--shell-bg);color:var(--shell-text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.instance-shell-header{padding-top:env(safe-area-inset-top)}
.cockpit-topbar{border-bottom:1px solid var(--shell-line)}
.cockpit-wrap{max-width:1160px;margin:0 auto;padding:0 1rem;min-height:3.25rem;display:flex;align-items:center;justify-content:space-between;gap:.5rem;box-sizing:border-box}
.cockpit-home{color:var(--shell-text);font-size:.95rem;font-weight:750;text-decoration:none;min-height:44px;display:flex;align-items:center;gap:.3em;min-width:0;overflow-wrap:anywhere}
.cockpit-home span{color:var(--shell-soft);font-weight:600;white-space:nowrap}
.cockpit-idle{border:1px solid var(--shell-line);border-radius:8px;background:var(--shell-alt);color:var(--shell-soft);min-height:44px;padding:.35rem .65rem;font-family:inherit;font-size:.78rem;font-weight:700;letter-spacing:.04em;white-space:nowrap;opacity:.7}
.cockpit-idle span{color:var(--shell-grey);margin-right:.35em}
.instance-nav{background:var(--shell-alt);border-bottom:1px solid var(--shell-line)}
.instance-nav .nav-scroll{overflow-x:auto;overscroll-behavior-x:contain;scrollbar-width:thin;padding:.45rem .5rem;box-sizing:border-box}
.instance-nav ul{display:flex;gap:.3rem;list-style:none;width:max-content;margin:0 auto;padding:0}
.instance-nav .board-link{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.15rem;min-width:76px;min-height:64px;padding:.4rem .65rem;border:1px solid transparent;border-radius:12px;color:var(--shell-soft);font-size:.8rem;font-weight:650;text-decoration:none;box-sizing:border-box}
.instance-nav .board-link:hover{background:var(--shell-bg);color:var(--shell-text)}
.instance-nav .board-link[aria-current=page]{background:var(--shell-bg);color:var(--shell-brand);border-color:var(--shell-brand)}
.instance-nav .nav-icon{font-size:1.55rem;line-height:1.25}
.instance-nav .nav-hint{text-align:right;color:var(--shell-soft);font-size:.7rem;padding:0 .75rem .2rem;margin:0}
.instance-cockpit :focus-visible{outline:3px solid var(--shell-brand);outline-offset:3px}
.cockpit-toolbar{display:flex;align-items:center;justify-content:space-between;gap:.5rem;padding:.3rem max(.65rem,env(safe-area-inset-left));border-bottom:1px solid var(--shell-line)}
.cockpit-toolbar h1{font-size:1rem;margin:0;line-height:1.5}
.cockpit-toolbar p{font-size:.75rem;color:var(--shell-soft);margin:0}
.cockpit-actions{display:flex;gap:.35rem;flex:none}
.cockpit-action{display:inline-flex;align-items:center;justify-content:center;gap:.35rem;min-width:44px;min-height:44px;padding:.35rem .6rem;border:1px solid var(--shell-line);border-radius:8px;background:var(--shell-bg);color:var(--shell-text);font:inherit;font-size:.8rem;cursor:pointer;text-decoration:none;box-sizing:border-box}
.cockpit-action:hover{border-color:var(--shell-brand);text-decoration:none}
.instance-stage{flex:1;min-height:0;min-width:0;display:flex;overflow:hidden;padding-bottom:env(safe-area-inset-bottom)}
.instance-stage>#scientist,.instance-stage>.instance-view{width:100%;max-width:var(--board-max);margin:0 auto;overflow-y:auto;box-sizing:border-box;padding:1rem var(--board-gutter) 4rem;scroll-margin:0}
.instance-stage>[hidden]{display:none!important}
.instance-view h1{font-size:1.8rem;margin-bottom:.3rem}
.organ-state{color:var(--muted)}
.instance-view textarea{width:100%;box-sizing:border-box;min-height:10rem;font:inherit;padding:.75rem;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;resize:vertical}
button.organ-setup-copy{width:auto;height:auto;min-height:44px;padding:.5rem .8rem;margin-top:.5rem;font:inherit}
.instance-stage>.embedded-board{max-width:none;padding:0;overflow:hidden;display:flex}
.embedded-board>h1,.embedded-board>p{display:none}
.instance-view iframe{display:block;flex:1;width:100%;height:100%;min-width:0;border:0;background:var(--bg)}
@media(max-width:420px){.cockpit-wrap{padding-inline:.65rem}.instance-nav .board-link{min-width:70px}.cockpit-action span{display:none}}
"""

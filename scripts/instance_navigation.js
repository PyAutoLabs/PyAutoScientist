// Instance-owned cockpit shell. Selecting/reloading a view never activates an organ.
(() => {
  const nav = document.querySelector('.instance-nav');
  if (!nav) return;
  const overview = document.getElementById('scientist');
  const views = [...document.querySelectorAll('.instance-view')];
  const links = [...nav.querySelectorAll('a')];
  const heading = document.getElementById('cockpit-heading');
  const status = document.getElementById('cockpit-status');
  const external = document.getElementById('cockpit-external');
  const scroller = nav.querySelector('.nav-scroll');
  function selectedView() { return views.find(v => '#' + v.id === location.hash); }
  function hint() {
    nav.querySelector('.nav-hint').hidden = scroller.scrollWidth <= scroller.clientWidth;
  }
  function select(focus = false) {
    const view = selectedView();
    overview.hidden = !!view;
    for (const panel of views) panel.hidden = panel !== view;
    const selected = view ? '#' + view.id : '#scientist';
    for (const link of links) {
      if (link.hash === selected) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    const frame = view && view.querySelector('iframe');
    heading.textContent = view ? view.querySelector('h1').textContent : 'Scientist';
    status.textContent = view ? view.querySelector('.organ-state').textContent : 'Overview';
    const local = new URL(location.href); local.hash = selected;
    external.href = frame ? frame.dataset.boardSrc : local.href;
    external.setAttribute('aria-label', `Open ${heading.textContent} in a new tab`);
    if (frame && !frame.dataset.loaded) {
      // Replace the child entry so Back/Forward belongs to the shell routes.
      frame.contentWindow.location.replace(frame.dataset.boardSrc);
      frame.dataset.loaded = 'true';
    }
    if (focus) {
      const target = frame ? heading : (view || overview).querySelector('h1');
      if (target) { target.setAttribute('tabindex', '-1'); target.focus({preventScroll: true}); }
      (view || overview).scrollTop = 0;
    }
    nav.querySelector('[aria-current="page"]').scrollIntoView({block: 'nearest', inline: 'nearest'});
    hint();
  }
  history.scrollRestoration = 'manual';
  window.addEventListener('hashchange', () => select(true));
  window.addEventListener('popstate', () => select(true));
  document.querySelector('.instance-shell-header').addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    event.stopPropagation(); // Shared section-link handling must not scroll the shell.
    if (link.hash !== location.hash) history.pushState(null, '', link.hash);
    select(true);
  });
  document.getElementById('cockpit-reload').addEventListener('click', () => {
    const view = selectedView(), frame = view && view.querySelector('iframe');
    if (frame) frame.contentWindow.location.replace(frame.dataset.boardSrc);
    else location.reload();
  });
  window.addEventListener('resize', hint);
  select();
})();

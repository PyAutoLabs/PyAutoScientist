// The shell keeps its navigation while selecting an instance-owned destination.
(() => {
  const nav = document.querySelector('.instance-nav');
  if (!nav) return;
  const overview = document.getElementById('scientist');
  const views = [...document.querySelectorAll('.instance-view')];
  const links = [...nav.querySelectorAll('a')];
  function select(focus = false) {
    const view = views.find(v => '#' + v.id === location.hash);
    overview.hidden = !!view;
    for (const panel of views) panel.hidden = panel !== view;
    const selected = view ? '#' + view.id : '#scientist';
    for (const link of links) {
      if (link.hash === selected) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    const frame = view && view.querySelector('iframe');
    if (frame && !frame.dataset.loaded) {
      // Replace the child entry so Back/Forward belongs to the shell routes.
      frame.contentWindow.location.replace(frame.dataset.boardSrc);
      frame.dataset.loaded = 'true';
    }
    if (focus) {
      const heading = view ? view.querySelector('h1') : overview.querySelector('h1');
      if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus({preventScroll: true}); }
      window.scrollTo(0, 0);
    }
    nav.querySelector('[aria-current="page"]').scrollIntoView({block: 'nearest', inline: 'nearest'});
  }
  history.scrollRestoration = 'manual';
  window.addEventListener('hashchange', () => select(true));
  window.addEventListener('popstate', () => select(true));
  nav.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    event.stopPropagation(); // The shared section-link handler must not scroll behind the shell.
    if (link.hash !== location.hash) history.pushState(null, '', link.hash);
    select(true);
  });
  select();
})();

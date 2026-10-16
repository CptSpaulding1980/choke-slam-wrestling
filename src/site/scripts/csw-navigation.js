(() => {
  const nav = document.querySelector('.csw-navigation');
  const toggle = nav?.querySelector('.menu-toggle');
  if (!toggle) return;
  const mobile = window.matchMedia('(max-width: 768px)');
  function close(returnFocus = false) {
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    if (returnFocus) toggle.focus();
  }
  function sync() {
    toggle.hidden = !mobile.matches;
    close();
  }
  nav.classList.add('nav-enhanced');
  sync();
  mobile.addEventListener('change', sync);
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  });
  nav.addEventListener('keydown', event => {
    if (event.key === 'Escape' && nav.classList.contains('is-open')) {
      close(true);
    }
  });
  nav.addEventListener('focusout', event => {
    if (!nav.contains(event.relatedTarget)) close();
  });
  const filters = document.querySelector('.hl-filter');
  if (filters) {
    filters.hidden = false;
    filters.addEventListener('click', event => {
      const button = event.target.closest('button[data-filter]');
      if (!button) return;
      const type = button.dataset.filter;
      for (const item of filters.querySelectorAll('button')) {
        const selected = item === button;
        item.classList.toggle('active', selected);
        item.setAttribute('aria-pressed', String(selected));
      }
      for (const card of document.querySelectorAll('.hl-card')) {
        card.hidden = type !== 'all' && card.dataset.type !== type && card.dataset.season !== type;
      }
      for (const section of document.querySelectorAll('.hl-season')) {
        section.hidden = ![...section.querySelectorAll('.hl-card')].some(card => !card.hidden);
      }
    });
  }
})();

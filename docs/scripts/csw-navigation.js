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
      let shown = 0;
      for (const card of document.querySelectorAll('.hl-card:not([hidden])')) {
        card.classList.remove('hl-enter');
        void card.offsetWidth;
        card.style.setProperty('--enter-delay', `${Math.min(shown++, 9) * 45}ms`);
        card.classList.add('hl-enter');
      }
      for (const section of document.querySelectorAll('.hl-season')) {
        section.hidden = ![...section.querySelectorAll('.hl-card')].some(card => !card.hidden);
      }
    });
  }
})();

// Motion layer: sticky-nav state, scroll progress, scroll reveal, count-up.
(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const nav = document.querySelector('.csw-navigation');
  if (nav) {
    let ticking = false;
    const update = () => {
      ticking = false;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      nav.style.setProperty('--scroll', max > 0 ? Math.min(1, window.scrollY / max).toFixed(4) : 0);
      nav.classList.toggle('is-stuck', nav.getBoundingClientRect().top <= 0 && window.scrollY > 0);
    };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener('resize', update, { passive: true });
    update();
  }
  if (reduce || !('IntersectionObserver' in window)) return;

  const season = document.querySelector('.season-panel strong');
  const target = season && parseInt(season.textContent, 10);
  if (target > 0) {
    const width = season.textContent.trim().length;
    const start = performance.now() + 550;
    const tick = now => {
      const t = Math.min(1, Math.max(0, (now - start) / 900));
      const value = Math.round(target * (1 - Math.pow(1 - t, 3)));
      season.textContent = String(value).padStart(width, '0');
      if (t < 1) requestAnimationFrame(tick);
    };
    season.textContent = '0'.padStart(width, '0');
    requestAnimationFrame(tick);
  }

  const selector = [
    '.league-team', '.hub-card', '.home-panel', '.league-teams .section-heading', '.league-hubs .section-heading',
    '.champ-card', '.team-member-card', '.team-profile', '.hl-card', '.faction-card', '.draft-cta', '.mask-box',
    '.champion-status', '.event-poster', '.event-video', '.table-scroll', '.note-content > h2', '.hl-season > h2'
  ].join(',');
  const items = [...document.querySelectorAll(selector)].filter(el => !el.closest('.league-intro'));
  if (!items.length) return;
  const observer = new IntersectionObserver(entries => {
    let i = 0;
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.style.setProperty('--reveal-delay', `${Math.min(i++, 8) * 70}ms`);
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px -6% 0px', threshold: 0 });
  for (const el of items) { el.setAttribute('data-reveal', ''); observer.observe(el); }
  document.documentElement.classList.add('motion-ready');
})();

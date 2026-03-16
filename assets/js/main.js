/* ═══════════════════════════════════════════════════════════
   main.js — Shared JS for all pages
   Include in every HTML page with: <script src="main.js"></script>
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── 1. SMOOTH SCROLL for same-page anchor links ────────────────────────
     Overrides the browser's instant jump with a smooth eased scroll.
     Works even when the browser's own smooth-scroll is disabled.          */
  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function smoothScrollTo(targetY, duration) {
    const startY  = window.scrollY;
    const diff    = targetY - startY;
    let   startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      const elapsed  = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      window.scrollTo(0, startY + diff * easeInOutCubic(progress));
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  const NAV_H = 64; // px — matches --nav-h in style.css

  document.addEventListener('click', function (e) {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;
    const id     = link.getAttribute('href').slice(1);
    const target = document.getElementById(id);
    if (!target) return;
    e.preventDefault();
    const top = target.getBoundingClientRect().top + window.scrollY - NAV_H;
    smoothScrollTo(top, 680); // 680ms — feels snappy but visible
    // update URL hash without jumping
    history.pushState(null, '', '#' + id);
    // close mobile menu if open
    const menu = document.getElementById('nav-menu');
    if (menu) menu.classList.remove('open');
  });

  /* ── 2. ACTIVE NAV HIGHLIGHT on scroll (same-page only) ─────────────── */
  function initScrollSpy() {
    const sections = Array.from(document.querySelectorAll('section[id]'));
    const navLinks = Array.from(document.querySelectorAll('.nav-links a[href^="#"]'));
    if (!sections.length || !navLinks.length) return;

    function updateActive() {
      const scrollMid = window.scrollY + window.innerHeight * 0.35;
      let active = sections[0];
      for (const s of sections) {
        if (s.offsetTop <= scrollMid) active = s;
      }
      navLinks.forEach(l =>
        l.classList.toggle('active', l.getAttribute('href') === '#' + active.id)
      );
    }

    window.addEventListener('scroll', updateActive, { passive: true });
    updateActive();
  }

  /* ── 3. ACTIVE NAV for multi-page (highlights link matching current URL) */
  function initPageNav() {
    const current = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a').forEach(link => {
      const href = link.getAttribute('href') || '';
      // match by filename e.g. "talks.html" or root ""
      const linkPage = href.split('/').pop().split('#')[0] || 'index.html';
      if (linkPage === current) link.classList.add('active');
    });
  }

  /* ── 4. MOBILE NAV TOGGLE ─────────────────────────────────────────────── */
  function initMobileNav() {
    const toggle = document.getElementById('nav-toggle');
    const menu   = document.getElementById('nav-menu');
    if (!toggle || !menu) return;

    toggle.addEventListener('click', () => {
      const open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open);
    });

    // close on outside click
    document.addEventListener('click', e => {
      if (!toggle.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ── 5. SCROLL-REVEAL for cards (IntersectionObserver) ──────────────────
     Adds .revealed class when an element enters the viewport.
     CSS handles the actual fade-up animation via .scroll-reveal rule.     */
  function initScrollReveal() {
    const items = document.querySelectorAll(
      '.pub-card, .award-card, .project-card, .news-item, ' +
      '.talk-card, .course-card, .stat'
    );
    if (!items.length) return;

    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    items.forEach((el, i) => {
      el.classList.add('scroll-reveal');
      // stagger delay capped at 300ms so long lists don't wait forever
      el.style.transitionDelay = Math.min(i % 6 * 60, 300) + 'ms';
      obs.observe(el);
    });
  }

  /* ── 6. PAGE TRANSITION (cross-page links) ───────────────────────────────
     Fades the page out before navigating to another .html page,
     and fades in on load. Feels smooth without a framework.               */
  function initPageTransitions() {
    // fade in on load
    document.body.classList.add('page-enter');
    requestAnimationFrame(() => {
      requestAnimationFrame(() => document.body.classList.add('page-enter-active'));
    });

    // fade out on cross-page navigation
    document.addEventListener('click', e => {
      const link = e.target.closest('a[href]');
      if (!link) return;
      const href = link.getAttribute('href');
      // only intercept relative links to .html pages (not anchors, not external)
      if (!href || href.startsWith('#') || href.startsWith('http') ||
          href.startsWith('mailto') || link.target === '_blank') return;
      if (!href.endsWith('.html') && !href.endsWith('/')) return;

      e.preventDefault();
      document.body.classList.add('page-exit');
      setTimeout(() => { window.location.href = href; }, 280);
    });
  }

  /* ── INIT ────────────────────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    initMobileNav();
    initScrollSpy();
    initPageNav();
    initScrollReveal();
    initPageTransitions();
  });

})();

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Elements
  const burgerBtn = document.getElementById('burger-btn');
  const mobileOverlay = document.getElementById('mobile-overlay');
  const mobileMenu = document.getElementById('mobile-menu');

  function openMenu() {
    if (!burgerBtn || !mobileOverlay || !mobileMenu) return;
    burgerBtn.setAttribute('aria-expanded', 'true');
    mobileOverlay.removeAttribute('hidden');
    mobileMenu.removeAttribute('hidden');
    document.body.classList.add('menu-open');
  }

  function closeMenu() {
    if (!burgerBtn || !mobileOverlay || !mobileMenu) return;
    burgerBtn.setAttribute('aria-expanded', 'false');
    mobileOverlay.setAttribute('hidden', '');
    mobileMenu.setAttribute('hidden', '');
    document.body.classList.remove('menu-open');
  }

  function toggleMenu() {
    const isExpanded = burgerBtn?.getAttribute('aria-expanded') === 'true';
    if (isExpanded) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  if (burgerBtn) {
    burgerBtn.addEventListener('click', toggleMenu);
  }

  if (mobileOverlay) {
    mobileOverlay.addEventListener('click', closeMenu);
  }

  // Close menu on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMenu();
    }
  });

  // Close menu when viewport resized beyond 720px
  window.addEventListener('resize', () => {
    if (window.innerWidth > 720) {
      closeMenu();
    }
  });

  // 2. Video Playback Guarantee
  const video = document.querySelector('.bg-video');
  if (video) {
    const playPromise = video.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {
        video.muted = true;
        video.play().catch(() => {});
      });
    }
  }

  // 3. Stats Count-up Animation
  const statsSection = document.querySelector('.stats');
  const statNumbers = document.querySelectorAll('.stat-number');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function easeOutCubic(x) {
    return 1 - Math.pow(1 - x, 3);
  }

  function startCountUp() {
    statNumbers.forEach((el, i) => {
      const target = parseFloat(el.getAttribute('data-target') || '0');
      const decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
      const duration = 1400 + i * 80;
      const startOffset = 400 + i * 90;

      if (prefersReducedMotion) {
        el.textContent = target.toFixed(decimals);
        return;
      }

      setTimeout(() => {
        const startTime = performance.now();

        function update(currentTime) {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const easedProgress = easeOutCubic(progress);
          const currentValue = easedProgress * target;

          el.textContent = currentValue.toFixed(decimals);

          if (progress < 1) {
            requestAnimationFrame(update);
          } else {
            el.textContent = target.toFixed(decimals);
          }
        }

        requestAnimationFrame(update);
      }, startOffset);
    });
  }

  if (statsSection) {
    let triggered = false;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !triggered) {
            triggered = true;
            startCountUp();
            observer.disconnect();
          }
        });
      },
      { threshold: 0.25 }
    );
    observer.observe(statsSection);

    setTimeout(() => {
      if (!triggered) {
        triggered = true;
        startCountUp();
        observer.disconnect();
      }
    }, 300);
  }

  // 4. Quick Sample Inserters for Text Check
  window.fillSample = function(type) {
    const headlineInput = document.getElementById('headline');
    const articleInput = document.getElementById('article_text');
    if (!headlineInput || !articleInput) return;

    if (type === 'real') {
      headlineInput.value = "NASA James Webb Space Telescope Discovers Distant Primitive Galaxy";
      articleInput.value = "Astronomers using the James Webb Space Telescope confirmed the detection of a galaxy formed just 300 million years after the Big Bang. The peer-reviewed research published in Nature Astronomy revealed spectroscopic redshift measurements confirming primitive stellar populations.";
    } else if (type === 'fake') {
      headlineInput.value = "SHOCKING: Secret Miracle Lemon Tonic Cures All Stage 4 Cancer Overnight - Doctors BANNED It!";
      articleInput.value = "Doctors and big pharma billionaires are terrified! Drinking boiled lemon water with baking soda and secret volcanic minerals completely cures all terminal diseases in 24 hours! Government whistleblowers leaked the classified formula before their laboratory was raided. Share this immediately before it gets taken down!";
    }
  };
});

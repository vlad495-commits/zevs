document.addEventListener('DOMContentLoaded', function () {

  // ── Navbar scroll ──
  var navbar = document.getElementById('navbar');
  if (navbar) {
    window.addEventListener('scroll', function () {
      navbar.classList.toggle('scrolled', window.scrollY > 20);
    });
  }

  // ── Mobile menu ──
  var ham = document.getElementById('hamburger');
  var mMenu = document.getElementById('mobileMenu');
  if (ham && mMenu) {
    ham.addEventListener('click', function () {
      ham.classList.toggle('open');
      mMenu.classList.toggle('open');
      document.body.style.overflow = mMenu.classList.contains('open') ? 'hidden' : '';
    });
  }
  window.closeMenu = function () {
    if (ham) ham.classList.remove('open');
    if (mMenu) mMenu.classList.remove('open');
    document.body.style.overflow = '';
  };

  // ── Nav dropdowns (выносим в body, чтобы backdrop-filter не обрезал) ──
  document.querySelectorAll('.nav-dropdown').forEach(function (dd) {
    var panel = dd.querySelector('.dropdown-panel');
    if (!panel) return;

    document.body.appendChild(panel);

    var closeTimer = null;

    function openPanel() {
      clearTimeout(closeTimer);
      var rect = dd.getBoundingClientRect();
      panel.style.top  = (rect.bottom + 4) + 'px';
      panel.style.left = rect.left + 'px';
      dd.classList.add('open');
      panel.classList.add('open');
    }

    function scheduleClose() {
      closeTimer = setTimeout(function () {
        dd.classList.remove('open');
        panel.classList.remove('open');
      }, 150);
    }

    dd.addEventListener('mouseenter', openPanel);
    dd.addEventListener('mouseleave', scheduleClose);
    panel.addEventListener('mouseenter', function () { clearTimeout(closeTimer); });
    panel.addEventListener('mouseleave', scheduleClose);
  });

});

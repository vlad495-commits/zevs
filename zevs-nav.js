document.addEventListener('DOMContentLoaded', function () {

  // Navbar scroll effect
  var navbar = document.getElementById('navbar');
  if (navbar) {
    window.addEventListener('scroll', function () {
      navbar.classList.toggle('scrolled', window.scrollY > 20);
    });
  }

  // Mobile menu toggle
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

  // Nav dropdowns — открытие при наведении мыши
  document.querySelectorAll('.nav-dropdown').forEach(function (dd) {
    var menu = dd.querySelector('.nav-drop-menu');
    if (!menu) return;

    var closeTimer = null;

    // Переносим меню в body, чтобы backdrop-filter navbar не создавал новый stacking context
    document.body.appendChild(menu);

    function openDrop() {
      clearTimeout(closeTimer);
      var rect = dd.getBoundingClientRect();
      menu.style.top  = (rect.bottom + 4) + 'px';
      menu.style.left = rect.left + 'px';
      dd.classList.add('open');
      menu.classList.add('open');
    }

    function scheduleClose() {
      closeTimer = setTimeout(function () {
        dd.classList.remove('open');
        menu.classList.remove('open');
      }, 150);
    }

    dd.addEventListener('mouseenter', openDrop);
    dd.addEventListener('mouseleave', scheduleClose);
    menu.addEventListener('mouseenter', function () { clearTimeout(closeTimer); });
    menu.addEventListener('mouseleave', scheduleClose);
  });

});

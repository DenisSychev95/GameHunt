
document.addEventListener('DOMContentLoaded', function () {
  // Если библиотека не подгрузилась (например, на другой странице) — просто выходим без ошибок
  if (typeof GLightbox === 'undefined') return;

  // Если на странице нет триггеров — тоже выходим
  if (!document.querySelector('.js-profile-lightbox')) return;

  GLightbox({
    selector: '.js-profile-lightbox',
    touchNavigation: true,
    loop: false,
    zoomable: true,
    closeButton: true
  });
});


document.addEventListener('DOMContentLoaded', function () {
  // Если библиотека не подгрузилась (например, на другой странице) —  выход без ошибок
  if (typeof GLightbox === 'undefined') return;

  // Если на странице нет триггеров — тоже выход
  if (!document.querySelector('.js-profile-lightbox')) return;

  GLightbox({
    selector: '.js-profile-lightbox',
    touchNavigation: true,
    loop: false,
    zoomable: true,
    closeButton: true
  });
});

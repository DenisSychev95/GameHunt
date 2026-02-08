document.addEventListener("DOMContentLoaded", function () {
  if (typeof GLightbox === "undefined") return;

  GLightbox({
    selector: ".js-file-lightbox",
    touchNavigation: true,
    loop: false,
    zoomable: true,
    closeButton: true
  });
});
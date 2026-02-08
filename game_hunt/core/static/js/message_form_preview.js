document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("id_image");

  const current = document.getElementById("msg-image-current");
  const nameEl = document.getElementById("msg-image-name");

  const preview = document.getElementById("msg-image-preview");
  const previewLink = document.getElementById("msg-image-preview-link");

  if (!input || !current || !nameEl || !preview || !previewLink) return;

  let blobUrl = null;
  let lb = null;

  function cleanupBlob() {
    if (blobUrl) {
      URL.revokeObjectURL(blobUrl);
      blobUrl = null;
    }
  }

  function resetUI() {
    cleanupBlob();
    current.style.display = "none";
    nameEl.textContent = "";
    preview.removeAttribute("src");
    preview.style.display = "none";
    previewLink.href = "#";
    previewLink.style.display = "none";
  }

  function ensureLightbox() {
    if (typeof GLightbox === "undefined") return;
    if (!lb) {
      lb = GLightbox({
        selector: ".js-image-preview-lightbox",
        loop: false,
        touchNavigation: false,
        keyboardNavigation: true,
        closeButton: true,
        zoomable: true
      });
    } else {
      lb.reload();
    }
  }

  input.addEventListener("change", function () {
    cleanupBlob();

    const file = input.files && input.files[0];
    if (!file) {
      resetUI();
      return;
    }

    blobUrl = URL.createObjectURL(file);

    // "Выбрано: ..."
    nameEl.textContent = file.name;
    current.style.display = "";

    // превью
    preview.src = blobUrl;
    preview.style.display = "block";

    // ссылка на lightbox (кликаем по превью)
    previewLink.href = blobUrl;
    previewLink.setAttribute("data-glightbox", "type: image");
    previewLink.style.display = "inline-block";

    ensureLightbox();
  });

  // чтобы не прыгало на #
  previewLink.addEventListener("click", function (e) {
    if (previewLink.href.endsWith("#")) e.preventDefault();
  });

  resetUI();
});
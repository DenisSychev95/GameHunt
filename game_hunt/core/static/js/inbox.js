document.addEventListener("DOMContentLoaded", function () {
  // защита от двойной инициализации
  if (window.__inboxInit) return;
  window.__inboxInit = true;

  const list = document.getElementById("inbox-list");
  const modal = document.getElementById("inbox-modal");
  if (!list || !modal) return;

  // ===== helpers =====
  function openModal() {
    modal.classList.add("modal--open");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-lock");
  }

  function closeModal() {
    modal.classList.remove("modal--open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-lock");
  }

  modal.addEventListener("click", (e) => {
    if (e.target.matches("[data-close]")) closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  function getCookie(name) {
    const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : null;
  }

  async function post(url) {
    const csrftoken = getCookie("csrftoken");
    return fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken || "",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    });
  }

  async function markRead(readUrl) {
    if (!readUrl) return;
    await post(readUrl);
  }

  // ===== lightbox only for modal image =====
  let modalLb = null;
  function ensureModalLightbox() {
    if (typeof GLightbox === "undefined") return;
    if (!modalLb) {
      modalLb = GLightbox({
        selector: ".js-modal-image",
        loop: false,
        touchNavigation: false,
        keyboardNavigation: true,
        closeButton: true,
        zoomable: true,
      });
    } else {
      modalLb.reload();
    }
  }

  function fillModal(data) {
    const sentEl = document.getElementById("modal-sent");
    const fromEl = document.getElementById("modal-from");
    const topicEl = document.getElementById("modal-topic");
    const textEl = document.getElementById("modal-text");

    if (sentEl) sentEl.textContent = data.created_at || "";
    if (fromEl) fromEl.textContent = data.from || "";
    if (topicEl) topicEl.textContent = data.topic || "";
    if (textEl) textEl.textContent = data.body || "";

    // email (only for guest)
    const emailRow = document.getElementById("modal-email-row");
    const emailEl = document.getElementById("modal-email");
    if (emailRow && emailEl) {
      const em = (data.email || "").trim();
      if (em) {
        emailEl.textContent = em;
        emailRow.style.display = "";
      } else {
        emailRow.style.display = "none";
      }
    }

    // short (title/topic_custom)
    const shortRow = document.getElementById("modal-short-row");
    const shortEl = document.getElementById("modal-short");
    if (shortRow && shortEl) {
      const s = (data.short || "").trim();
      if (s) {
        shortEl.textContent = s;
        shortRow.style.display = "";
      } else {
        shortRow.style.display = "none";
      }
    }

    // link (only for UserMessages)
    const linkRow = document.getElementById("modal-link-row");
    const linkA = document.getElementById("modal-link");
    if (linkRow && linkA) {
      const l = (data.link || "").trim();
      if (l) {
        linkA.href = l;
        linkRow.style.display = "";
      } else {
        linkRow.style.display = "none";
      }
    }

    // image (clickable only in modal)
    const imgBox = document.getElementById("modal-image");
    if (imgBox) {
      if (data.image_url) {
        imgBox.innerHTML = `
          <a href="${data.image_url}" class="js-modal-image" data-gallery="modal-${data.id}">
            <img src="${data.image_url}" alt="" class="modal__img">
          </a>
        `;
        ensureModalLightbox();
      } else {
        imgBox.innerHTML = "";
      }
    }
  }

  // ===== single click handler for inbox list =====
  list.addEventListener("click", async (e) => {
    // 1) hide button (cross)
    const hideBtn = e.target.closest(".msg__hide");
    if (hideBtn) {
      e.stopPropagation();
      e.preventDefault();

      const url = hideBtn.dataset.hideUrl;
      if (!url) return;

      try {
        const res = await post(url);
        if (res.ok) {
          const card = hideBtn.closest(".msg");
          if (card) card.remove();
        }
      } catch (err) {
        console.error("Hide failed:", err);
      }
      return;
    }

    // 2) do not open modal if clicked on link inside card
    if (e.target.closest(".msg__link-a")) return;

    // 3) open card
    const card = e.target.closest(".msg");
    if (!card) return;

    const detailUrl = card.dataset.detailUrl;
    const readUrl = card.dataset.readUrl;
    if (!detailUrl) return;

    let data;
    try {
      const res = await fetch(detailUrl, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      data = await res.json();
    } catch (err) {
      console.error("Failed to load message detail:", err);
      return;
    }

    fillModal(data);
    openModal();

    // auto mark as read
    if (card.classList.contains("msg--unread")) {
      card.classList.remove("msg--unread");
      try { await markRead(readUrl); } catch (_) {}
    }
  });
});
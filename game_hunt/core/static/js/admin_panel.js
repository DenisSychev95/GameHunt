function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
  const csrftoken = getCookie("csrftoken");

  document.querySelectorAll(".js-toggle-ban").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const userId = btn.dataset.userId;
      if (!userId) return;

      try {
        const res = await fetch(`/admin-panel/users/${userId}/toggle-ban-ajax/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: "{}",
        });

        const data = await res.json();
        if (!data.ok) return;

        const row = document.querySelector(`[data-user-row="${userId}"]`);
        if (!row) return;

        const label = row.querySelector("[data-ban-label]");
          if (data.is_active) {
            btn.textContent = "Забанить";
            btn.classList.add("is-ban");
            btn.classList.remove("is-unban");

          if (label) { label.textContent = "активен"; label.className = "st-ok"; }
        } else {
            btn.textContent = "Разбанить";
            btn.classList.add("is-unban");
            btn.classList.remove("is-ban");

          if (label) { label.textContent = "забанен"; label.className = "st-warn"; }
}
      } catch (e) {
        console.error(e);
      }
    });
  });
// ====== Comments page: auto-submit radios ======
  const filtersForm = document.querySelector(".js-comments-filters");
  if (filtersForm) {
    filtersForm.addEventListener("change", (e) => {
      if (e.target && e.target.matches('input[type="radio"][name="kind"]')) {
        filtersForm.submit();
      }
    });
  }

  // ====== Comments page: show/hide comment text ======
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".js-comment-toggle");
    if (!btn) return;

    const cell = btn.closest(".admin-comment-cell");
    if (!cell) return;

    const body = cell.querySelector(".js-comment-body");
    if (!body) return;

    const isOpen = !body.hasAttribute("hidden");
    if (isOpen) {
      body.setAttribute("hidden", "");
      btn.textContent = "Показать";
      btn.setAttribute("aria-expanded", "false");
    } else {
      body.removeAttribute("hidden");
      btn.textContent = "Скрыть";
      btn.setAttribute("aria-expanded", "true");
    }
  });

});
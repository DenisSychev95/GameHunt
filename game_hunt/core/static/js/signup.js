document.addEventListener("DOMContentLoaded", function () {
  const phoneInput = document.getElementById("id_phone");
  if (!phoneInput) return;

  if (window.IMask) {
    IMask(phoneInput, { mask: "+{7} (000) 000-00-00" });
  }
});


document.addEventListener("DOMContentLoaded", () => {
  const bd = document.getElementById("id_birth_date");
  if (!bd || !window.IMask) return;

  IMask(bd, {
    mask: Date,
    pattern: 'd.`m.`Y',
    lazy: true,          
    autofix: true,        

    blocks: {
      d: {
        mask: IMask.MaskedRange,
        from: 1,
        to: 31,
        maxLength: 2,
      },
      m: {
        mask: IMask.MaskedRange,
        from: 1,
        to: 12,
        maxLength: 2,
      },
      Y: {
        mask: IMask.MaskedRange,
        from: 1900,
        to: new Date().getFullYear(),
        maxLength: 4,
      }
    }
  });
});


document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-toggle-pass]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const wrap = btn.closest(".gd-pass-wrap");
      const input = wrap?.querySelector("input");
      if (!input) return;

      const openIcon = btn.querySelector(".gd-eye-open");
      const offIcon  = btn.querySelector(".gd-eye-off");

      const show = input.type === "password";
      input.type = show ? "text" : "password";

      if (openIcon) openIcon.style.display = show ? "none" : "inline-block";
      if (offIcon)  offIcon.style.display  = show ? "inline-block" : "none";
    });
  });
});
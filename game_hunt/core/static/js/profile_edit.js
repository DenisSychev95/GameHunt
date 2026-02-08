document.addEventListener("DOMContentLoaded", function () {
  const phoneInput = document.getElementById("id_phone");
  if (!phoneInput) return;

  if (window.IMask) {
    IMask(phoneInput, { mask: "+{7} (000) 000-00-00" });
  }
});
document.addEventListener("DOMContentLoaded", function () {
  const sendTo = document.getElementById("id_send_to");
  const wrapOne = document.getElementById("wrap-recipient");
  const wrapMany = document.getElementById("wrap-recipients");
  const one = document.getElementById("id_recipient");
  const many = document.getElementById("id_recipients");

  function apply() {
    const v = sendTo ? sendTo.value : "all";

    if (v === "one") {
      wrapOne.style.display = "";
      wrapMany.style.display = "none";
      if (one) one.disabled = false;
      if (many) many.disabled = true;
    } else if (v === "many") {
      wrapOne.style.display = "none";
      wrapMany.style.display = "";
      if (one) one.disabled = true;
      if (many) many.disabled = false;
    } else { // all
      wrapOne.style.display = "none";
      wrapMany.style.display = "none";
      if (one) one.disabled = true;
      if (many) many.disabled = true;
    }
  }

  if (sendTo) {
    sendTo.addEventListener("change", apply);
    apply();
  }
});
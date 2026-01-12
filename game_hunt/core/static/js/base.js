document.addEventListener('click', (e) => {
  const closeBtn = e.target.closest('.gh-message-close');
  if (!closeBtn) return;

  const message = closeBtn.closest('.gh-message');
  if (!message) return;

  message.remove();
});
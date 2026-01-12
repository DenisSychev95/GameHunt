// Этот файл безопасен: он не ломает django-ckeditor, но помогает,
// если CKEditor подключается вручную (ckeditor4) и нужен replace по id.
document.addEventListener('DOMContentLoaded', () => {
  if (!window.CKEDITOR) return;

  const ids = ['id_summary', 'id_text', 'id_conclusion'];
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el && !CKEDITOR.instances[id]) {
      CKEDITOR.replace(id);
    }
  });
});

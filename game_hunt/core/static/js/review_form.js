// Этот файл безопасен: он не ломает django-ckeditor, но помогает,
// если CKEditor подключается вручную (ckeditor4) и нужен replace по id.



document.addEventListener('DOMContentLoaded', () => {
  

  const root = document.querySelector('[data-formset]');
  
  if (!root) return;

  const formsWrap = root.querySelector('[data-forms]');
  const tpl = root.querySelector('template[data-empty-form]');
  const addBtn = root.querySelector('[data-add-form]');
  const totalInput = root.querySelector('input[name$="-TOTAL_FORMS"]');



  if (!formsWrap || !tpl || !addBtn || !totalInput) {
    
    return;
  }

  addBtn.addEventListener('click', () => {
    

    const index = parseInt(totalInput.value || '0', 10);
    

    let html = tpl.innerHTML.trim();
    if (!html) {
      
      return;
    }

    html = html.replaceAll('__prefix__', String(index));
    formsWrap.insertAdjacentHTML('beforeend', html);

    totalInput.value = String(index + 1);
    
  });
});


document.addEventListener('change', (e) => {
  const input = e.target;
  if (!input.matches('.gd-file-pick input[type="file"]')) return;

  const root = input.closest('.gd-file');
  const out = root?.querySelector('[data-file-name]');
  if (!out) return;

  out.textContent = input.files?.length ? input.files[0].name : 'Изображение не выбрано';
});



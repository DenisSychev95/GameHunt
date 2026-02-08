document.addEventListener('DOMContentLoaded', () => {
   document.documentElement.classList.add('js');
  //  Инициализация
  const lightbox = GLightbox({
    selector: '.glightbox',
    closeButton: true,
    loop: false,
    touchNavigation: true
  });

  const root = document.querySelector('[data-gallery]');
  if (!root) return;
  root.classList.add('is-js');

  const pageSize = parseInt(root.dataset.pageSize || '5', 10);
  const thumbs = Array.from(root.querySelectorAll('.gd-thumb'));
  const prev = root.querySelector('[data-prev]');
  const next = root.querySelector('[data-next]');

  let page = 0;

  function totalPages() {
    return Math.ceil(thumbs.length / pageSize);
  }

function render() {
  const start = page * pageSize;
  const end = start + pageSize;

  thumbs.forEach((el, i) => {
    el.classList.toggle('is-visible', i >= start && i < end);
  });

  const lastPage = totalPages() - 1;

  // ⬅️ показать левую только если есть предыдущая страница
  if (prev) {
    prev.classList.toggle('is-hidden', page === 0);
    prev.disabled = page === 0; // можно оставить
  }

  // ➡️ показать правую только если есть следующая страница
  if (next) {
    next.classList.toggle('is-hidden', page === lastPage);
    next.disabled = page === lastPage; // можно оставить
  }
  if (thumbs.length <= pageSize) {
  prev?.classList.add('is-hidden');
  next?.classList.add('is-hidden');
}
}

  // 🧠 ВАЖНО: при клике открываем нужный индекс
  thumbs.forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      const idx = parseInt(el.dataset.index, 10);
      lightbox.openAt(idx);
    });
  });

  prev?.addEventListener('click', () => {
    if (page > 0) {
      page--;
      render();
    }
  });

  next?.addEventListener('click', () => {
    if (page < totalPages() - 1) {
      page++;
      render();
    }
  });

  render();
});


document.addEventListener('DOMContentLoaded', () => {
  const shareBtn = document.querySelector('[data-share]');
  if (!shareBtn) return;

  function showToast(text) {
    let toast = document.querySelector('.gh-toast');

    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'gh-toast';
      document.body.appendChild(toast);
    }

    toast.textContent = text;
    toast.classList.add('show');

    setTimeout(() => {
      toast.classList.remove('show');
    }, 2000);
  }

  shareBtn.addEventListener('click', async () => {
    const url = window.location.href;

    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(url);
        showToast('Ссылка скопирована в буфер обмена');
        return;
      }

      // fallback
      prompt('Скопируй ссылку:', url);
    } catch (e) {
      console.error('Share failed:', e);
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const voteForm = document.querySelector('.gd-vote-row');
  if (!voteForm) return;

  const toast = document.querySelector('.gd-vote-toast');

  function showToast(text, type='ok') {
    if (!toast) return;
    toast.textContent = text;
    toast.classList.remove('is-ok','is-err');
    toast.classList.add('is-show', type === 'err' ? 'is-err' : 'is-ok');
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove('is-show'), 2000);
  }

  voteForm.addEventListener('click', async (e) => {
    const btn = e.target.closest('button[name="value"]');
    if (!btn) return;

    e.preventDefault();

    const csrfToken = voteForm.querySelector('[name=csrfmiddlewaretoken]').value;
    const formData = new FormData();
    formData.append('value', btn.value);

    const resp = await fetch(voteForm.action, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: formData
    });

    if (!resp.ok) {
      showToast('Не удалось отправить голос. Попробуйте ещё раз.', 'err');
      return;
    }

    // успех: подсветка кнопок
    voteForm.querySelectorAll('.gd-vote-btn').forEach(b => {
      b.classList.remove('is-active');
      b.setAttribute('aria-pressed', 'false');
    });
    btn.classList.add('is-active');
    btn.setAttribute('aria-pressed', 'true');

    // скрыть подсказку (если есть)
    const hint = document.querySelector('.gd-vote .gd-hint');
    if (hint) hint.style.display = 'none';

    showToast('Спасибо, ваш голос учтён', 'ok');
  });
});



document.addEventListener('DOMContentLoaded', () => {

  // ---------- TOAST ----------
  function showToast(text) {
    let toast = document.querySelector('.gh-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'gh-toast';
      document.body.appendChild(toast);
    }

    toast.textContent = text;
    toast.classList.add('show');

    setTimeout(() => {
      toast.classList.remove('show');
    }, 2500);
  }

  // ---------- COMMENT FORM ----------
  const form = document.querySelector('.gd-comment-form');
  if (!form) return;

  const textarea = form.querySelector('textarea');
  const submitBtn = form.querySelector('button[type="submit"]');

  // счетчик
  const counter = document.createElement('div');
  counter.style.fontSize = '12px';
  counter.style.marginTop = '4px';
  counter.textContent = '0 / 500';
  textarea.after(counter);

  // блокировка кнопки
  submitBtn.disabled = true;

  textarea.addEventListener('input', () => {
    const len = textarea.value.length;
    counter.textContent = len + ' / 500';
    submitBtn.disabled = (len === 0 || len > 500);
  });

  // ✅ Enter без Shift отправляет
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (submitBtn.disabled) return;
      form.requestSubmit();
    }
  });

  // ---------- AJAX SEND ----------
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    submitBtn.disabled = true;

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const data = await response.json();

      if (!response.ok) {
        showToast(data.error || 'Ошибка отправки');
        submitBtn.disabled = false;
        return;
      }

      // вставляем HTML комментария
      const list = document.querySelector('.gd-comment-list');
      list.insertAdjacentHTML('afterbegin', data.html);

      textarea.value = '';
      counter.textContent = '0 / 500';
      submitBtn.disabled = true;

      showToast('Комментарий добавлен');

    } catch (err) {
      showToast('Ошибка сети');
      submitBtn.disabled = false;
    }
  });

  // ---------- AJAX DELETE (delegation) ----------
  const list = document.querySelector('.gd-comment-list');

  list?.addEventListener('submit', async (e) => {
    /* Возможно не потребуется ==> */
    const delForm = e.target.closest('.gd-comment-delete-form');
    /* <== Возможно не потребуется == */
    if (!delForm) return;

    e.preventDefault();

    try {
  // страховка: если вдруг форма почему-то указывает на reviews
  let url = delForm.action;
  if (
    url.includes('/reviews/comments/') &&
    window.location.pathname.startsWith('/games/')
  ) {
    url = url.replace('/reviews/comments/', '/games/comments/');
  }

  const resp = await fetch(url, {
    method: 'POST',
    body: new FormData(delForm),
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  });

  // ❗️КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ
  const contentType = resp.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await resp.json()
    : null;

  if (!resp.ok || !data || !data.ok) {
    showToast(data?.error || 'Не удалось удалить');
    return;
  }

  const article = delForm.closest('.gd-comment');
  if (article) article.remove();

  showToast('Комментарий удалён');

} catch (err) {
  showToast('Ошибка сети');
}
  });

});
document.addEventListener('DOMContentLoaded', () => {
  // 🔥 Инициализация ОДИН раз
  const lightbox = GLightbox({
    selector: '.glightbox',
    closeButton: true,
    loop: false,
    touchNavigation: true
  });

  const root = document.querySelector('[data-gallery]');
  if (!root) return;

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
    }, 3000);
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
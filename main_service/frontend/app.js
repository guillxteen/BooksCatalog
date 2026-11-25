const $ = (selector) => document.querySelector(selector);

const elements = {
  books: $('#books'),
  resultCount: $('#result-count'),
  bookDialog: $('#book-dialog'),
  authorsDialog: $('#authors-dialog'),
  detailDialog: $('#detail-dialog'),
  toast: $('#toast'),
};

const state = { books: [], authors: [], toastTimer: null };
const reportUrl = `${window.location.protocol}//${window.location.hostname}:8001/api/report`;

async function api(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body) headers['Content-Type'] = 'application/json';
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `Не удалось выполнить запрос (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
    } catch (_) {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function escapeHtml(value = '') {
  const node = document.createElement('div');
  node.textContent = value;
  return node.innerHTML;
}

function showToast(message, type = 'success') {
  clearTimeout(state.toastTimer);
  elements.toast.textContent = message;
  elements.toast.className = `toast visible${type === 'error' ? ' error' : ''}`;
  state.toastTimer = setTimeout(() => { elements.toast.className = 'toast'; }, 3200);
}

function pluralizeBooks(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} книга`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${count} книги`;
  return `${count} книг`;
}

function pluralizeAuthors(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} автор`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${count} автора`;
  return `${count} авторов`;
}

function renderAuthorOptions(selectedIds = []) {
  const selected = new Set(selectedIds.map(Number));
  $('#author-options').innerHTML = state.authors.length
    ? state.authors.map(author => `
        <label class="author-option">
          <input type="checkbox" name="author" value="${author.id}" ${selected.has(author.id) ? 'checked' : ''}>
          <span>${escapeHtml(author.name)}</span>
        </label>`).join('')
    : '<span>Сначала добавьте автора в каталог.</span>';
}

function renderAuthors() {
  $('#author-count').textContent = state.authors.length ? pluralizeAuthors(state.authors.length) : 'Нет авторов';
  $('#authors-list').innerHTML = state.authors.length
    ? state.authors.map(author => `
        <div class="author-row">
          <div>
            <div class="author-name">${escapeHtml(author.name)}</div>
            <div class="author-bio">${escapeHtml(author.biography) || 'Справка не добавлена'}</div>
          </div>
          <div class="author-actions">
            <button class="button button-secondary button-small" type="button" data-edit-author="${author.id}">Изменить</button>
            <button class="button button-danger button-small" type="button" data-delete-author="${author.id}">Удалить</button>
          </div>
        </div>`).join('')
    : '<div class="empty-state"><h3>Авторов пока нет</h3><p>Добавьте первого автора с помощью формы выше.</p></div>';
}

async function loadAuthors() {
  state.authors = await api('/api/authors');
  renderAuthors();
  renderAuthorOptions();
}

function renderBooks() {
  elements.resultCount.textContent = pluralizeBooks(state.books.length);
  elements.books.setAttribute('aria-busy', 'false');

  if (!state.books.length) {
    elements.books.innerHTML = `
      <div class="empty-state">
        <h3>Книги не найдены</h3>
        <p>Измените параметры поиска или добавьте новую книгу.</p>
        <button class="button button-primary" type="button" data-empty-add>Добавить книгу</button>
      </div>`;
    return;
  }

  elements.books.innerHTML = state.books.map(book => `
    <article class="book-card">
      <div class="card-top">
        <span class="status ${book.is_read ? '' : 'planned'}">${book.is_read ? 'Прочитано' : 'В планах'}</span>
        <span class="book-year">${book.publication_year}</span>
      </div>
      <h3>${escapeHtml(book.title)}</h3>
      <div class="book-authors">${book.authors.map(author => escapeHtml(author.name)).join(', ')}</div>
      <div class="book-description">${escapeHtml(book.description) || 'Описание не добавлено.'}</div>
      <div class="card-actions">
        <button class="button button-secondary button-small" type="button" data-view="${book.id}">Открыть</button>
        <button class="button button-secondary button-small" type="button" data-edit="${book.id}">Изменить</button>
        <button class="button button-danger button-small" type="button" data-delete="${book.id}">Удалить</button>
        <button class="text-button status-action" type="button" data-toggle="${book.id}">${book.is_read ? 'Вернуть в планы' : 'Отметить прочитанной'}</button>
      </div>
    </article>`).join('');
}

async function loadBooks() {
  elements.books.setAttribute('aria-busy', 'true');
  elements.books.innerHTML = '<div class="loading-state">Загрузка каталога…</div>';
  const params = new URLSearchParams();
  if ($('#search').value.trim()) params.set('search', $('#search').value.trim());
  if ($('#year-filter').value) params.set('year', $('#year-filter').value);
  if ($('#status-filter').value) params.set('is_read', $('#status-filter').value);
  state.books = await api(`/api/books?${params.toString()}`);
  renderBooks();
}

async function loadReport(showSuccess = false) {
  try {
    const report = await api(reportUrl);
    $('#total').textContent = report.total;
    $('#read').textContent = report.read;
    $('#unread').textContent = report.unread;
    if (showSuccess) showToast('Статистика обновлена');
  } catch (error) {
    $('#total').textContent = $('#read').textContent = $('#unread').textContent = '—';
    showToast(`Не удалось получить статистику: ${error.message}`, 'error');
  }
}

function resetAuthorForm() {
  $('#author-form').reset();
  $('#author-id').value = '';
  $('#save-author').textContent = 'Добавить автора';
  $('#cancel-author-edit').classList.add('hidden');
}

function openAuthorsCatalog() {
  resetAuthorForm();
  elements.authorsDialog.showModal();
  setTimeout(() => $('#author-name').focus(), 0);
}

function openBookForm(book = null) {
  if (!state.authors.length) {
    showToast('Сначала добавьте автора', 'error');
    openAuthorsCatalog();
    return;
  }

  $('#book-form').reset();
  $('#book-id').value = book?.id ?? '';
  $('#book-form-title').textContent = book ? 'Изменение книги' : 'Новая книга';
  renderAuthorOptions(book?.authors.map(author => author.id) || []);

  if (book) {
    $('#title').value = book.title;
    $('#publication-year').value = book.publication_year;
    $('#description').value = book.description;
    $('#is-read').checked = book.is_read;
  }
  elements.bookDialog.showModal();
  setTimeout(() => $('#title').focus(), 0);
}

function openBookDetails(book) {
  $('#detail-status').textContent = book.is_read ? 'Прочитано' : 'В планах';
  $('#detail-status').className = `status ${book.is_read ? '' : 'planned'}`;
  $('#detail-title').textContent = book.title;
  $('#detail-content').innerHTML = `
    <div class="detail-meta">${book.authors.map(author => escapeHtml(author.name)).join(', ')} · ${book.publication_year}</div>
    <p class="detail-description">${escapeHtml(book.description) || 'Описание не добавлено.'}</p>`;
  elements.detailDialog.showModal();
}

$('#book-form').addEventListener('submit', async event => {
  event.preventDefault();
  const id = $('#book-id').value;
  const authorIds = [...document.querySelectorAll('input[name="author"]:checked')].map(input => Number(input.value));
  if (!authorIds.length) {
    showToast('Выберите хотя бы одного автора', 'error');
    return;
  }

  const payload = {
    title: $('#title').value,
    publication_year: Number($('#publication-year').value),
    description: $('#description').value,
    is_read: $('#is-read').checked,
    author_ids: authorIds,
  };

  try {
    await api(id ? `/api/books/${id}` : '/api/books', {
      method: id ? 'PUT' : 'POST',
      body: JSON.stringify(payload),
    });
    elements.bookDialog.close();
    await Promise.all([loadBooks(), loadReport()]);
    showToast(id ? 'Книга обновлена' : 'Книга добавлена');
  } catch (error) {
    showToast(error.message, 'error');
  }
});

$('#author-form').addEventListener('submit', async event => {
  event.preventDefault();
  const id = $('#author-id').value;
  try {
    await api(id ? `/api/authors/${id}` : '/api/authors', {
      method: id ? 'PUT' : 'POST',
      body: JSON.stringify({ name: $('#author-name').value, biography: $('#biography').value }),
    });
    resetAuthorForm();
    await loadAuthors();
    showToast(id ? 'Автор обновлён' : 'Автор добавлен');
  } catch (error) {
    showToast(error.message, 'error');
  }
});

elements.books.addEventListener('click', async event => {
  if (event.target.closest('[data-empty-add]')) return openBookForm();
  const button = event.target.closest('button');
  if (!button) return;
  const id = Number(button.dataset.view || button.dataset.edit || button.dataset.toggle || button.dataset.delete);
  const book = state.books.find(item => item.id === id);
  if (!book) return;

  try {
    if (button.dataset.view) openBookDetails(book);
    if (button.dataset.edit) openBookForm(book);
    if (button.dataset.toggle) {
      await api(`/api/books/${id}/read-status`, {
        method: 'PATCH',
        body: JSON.stringify({ is_read: !book.is_read }),
      });
      await Promise.all([loadBooks(), loadReport()]);
      showToast('Статус книги изменён');
    }
    if (button.dataset.delete && confirm(`Удалить книгу «${book.title}»?`)) {
      await api(`/api/books/${id}`, { method: 'DELETE' });
      await Promise.all([loadBooks(), loadReport()]);
      showToast('Книга удалена');
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
});

$('#authors-list').addEventListener('click', async event => {
  const editId = Number(event.target.dataset.editAuthor);
  const deleteId = Number(event.target.dataset.deleteAuthor);

  if (editId) {
    const author = state.authors.find(item => item.id === editId);
    $('#author-id').value = author.id;
    $('#author-name').value = author.name;
    $('#biography').value = author.biography;
    $('#save-author').textContent = 'Сохранить изменения';
    $('#cancel-author-edit').classList.remove('hidden');
    $('#author-name').focus();
  }

  if (deleteId) {
    const author = state.authors.find(item => item.id === deleteId);
    if (!confirm(`Удалить автора «${author.name}»?`)) return;
    try {
      await api(`/api/authors/${deleteId}`, { method: 'DELETE' });
      resetAuthorForm();
      await loadAuthors();
      showToast('Автор удалён');
    } catch (error) {
      showToast(error.message, 'error');
    }
  }
});

let searchTimer;
['#search', '#year-filter'].forEach(selector => {
  $(selector).addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadBooks().catch(error => showToast(error.message, 'error')), 250);
  });
});

$('#status-filter').addEventListener('change', () => loadBooks().catch(error => showToast(error.message, 'error')));
$('#reset-filters').addEventListener('click', () => {
  $('#search').value = '';
  $('#year-filter').value = '';
  $('#status-filter').value = '';
  loadBooks().catch(error => showToast(error.message, 'error'));
});
$('#add-book').addEventListener('click', () => openBookForm());
$('#catalog-authors').addEventListener('click', openAuthorsCatalog);
$('#cancel-author-edit').addEventListener('click', resetAuthorForm);
$('#refresh-report').addEventListener('click', () => loadReport(true));

document.querySelectorAll('dialog .close').forEach(button => {
  button.addEventListener('click', () => button.closest('dialog').close());
});
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  });
});

async function initialize() {
  try {
    await loadAuthors();
    await Promise.all([loadBooks(), loadReport()]);
  } catch (error) {
    elements.books.innerHTML = '<div class="empty-state"><h3>Не удалось загрузить каталог</h3><p>Проверьте, запущен ли основной сервис.</p></div>';
    showToast(error.message, 'error');
  }
}

initialize();


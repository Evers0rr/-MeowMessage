document.addEventListener('DOMContentLoaded', () => {
  const requestsList = document.getElementById('requests-list');
  if (!requestsList) return;

  function getCsrf() {
    const cookie = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }
  const csrftoken = getCsrf();

  requestsList.addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-request-id]');
    if (!btn) return;

    const reqId = btn.getAttribute('data-request-id');
    const action = btn.getAttribute('data-action');
    const groupPk = window.location.pathname.split('/').filter(Boolean)[1];
    btn.disabled = true;
    btn.textContent = action === 'accept' ? 'Обробка...' : 'Відхилення...';

    try {
      const resp = await fetch(`${window.location.pathname}${reqId}/action/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `action=${encodeURIComponent(action)}`
      });

      if (!resp.ok) {
        const txt = await resp.text();
        alert('Помилка: ' + resp.status + '\n' + txt);
        btn.disabled = false;
        btn.textContent = action === 'accept' ? 'Прийняти' : 'Відхилити';
        return;
      }

      const data = await resp.json();
      if (data.status === 'accepted' || data.status === 'declined') {
        const card = document.getElementById(`request-${reqId}`);
        if (card) card.remove();
      } else if (data.status === 'forbidden') {
        alert('У вас немає прав виконати цю дію.');
        btn.disabled = false;
      } else {
        alert('Сталась невідома відповідь від сервера.');
        btn.disabled = false;
      }
    } catch (err) {
      console.error(err);
      alert('Помилка мережі.');
      btn.disabled = false;
      btn.textContent = action === 'accept' ? 'Прийняти' : 'Відхилити';
    }
  });
});

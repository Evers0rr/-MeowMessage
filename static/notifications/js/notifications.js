document.addEventListener('DOMContentLoaded', function() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    function showNotification(message, type = 'success') {
        const containerId = 'page-toast-container';
        let container = document.getElementById(containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = containerId;
            container.style.position = 'fixed';
            container.style.top = '20px';
            container.style.right = '20px';
            container.style.zIndex = 11000;
            document.body.appendChild(container);
        }

        const notification = document.createElement('div');
        notification.className = `page-toast ${type}`;
        notification.style.cssText = `
            margin-bottom:10px;
            padding:12px 18px;
            border-radius:10px;
            color:#fff;
            box-shadow:0 6px 18px rgba(0,0,0,0.12);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width:360px;
            opacity:1;
            transition:opacity 0.35s ease, transform 0.35s ease;
        `;
        notification.textContent = message;
        if (type === 'success') notification.style.background = '#27ae60';
        if (type === 'error') notification.style.background = '#e74c3c';
        if (type === 'info') notification.style.background = '#3498db';

        container.appendChild(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(20px)';
            setTimeout(() => notification.remove(), 400);
        }, 3000);
    }

    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', async function(e) {
            if (e.target.closest('.notification-actions') || e.target.closest('form') || e.target.tagName === 'BUTTON') {
                return;
            }
            const markUrl = this.dataset.markUrl;
            if (!markUrl) return;
            if (this.classList.contains('read')) return;

            try {
                const resp = await fetch(markUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (!resp.ok) throw new Error('Помилка сервера');
                const data = await resp.json();
                if (data.success) {
                    this.classList.remove('unread');
                    this.classList.add('read');
                    showNotification('Позначено як прочитане', 'info');
                } else {
                    showNotification(data.message || data.error || 'Невідома помилка', 'error');
                }
            } catch (err) {
                showNotification(err.message || 'Помилка зв\'язку', 'error');
                console.error(err);
            }
        });
    });

    document.querySelectorAll('.action-form.notify-action').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const url = this.action;
            try {
                const resp = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (!resp.ok) {
                    const txt = await resp.text();
                    throw new Error('Сервер повернув помилку: ' + resp.status + ' ' + txt);
                }
                const data = await resp.json();
                if (data.success) {
                    const root = this.closest('.notification-item');
                    if (root) root.remove();
                    showNotification(data.message || 'Успішно', 'success');
                } else if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification('Невідома відповідь сервера', 'error');
                }
            } catch (err) {
                showNotification(err.message || 'Помилка', 'error');
                console.error(err);
            }
        });
    });
});

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

    function showNotification(message, type='success') {
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

    const inviteForm = document.getElementById('invite-form');
    if (inviteForm) {
        inviteForm.addEventListener('submit', async function(event){
            event.preventDefault();
            const usernameInput = this.querySelector('input[name="username"]');
            if(!usernameInput.value.trim()){
                showNotification("Будь ласка, введіть нікнейм користувача.", 'error');
                return;
            }

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Відправка...';

            try {
                const formData = new FormData(this);
                const resp = await fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                if (!resp.ok) {
                    const txt = await resp.text();
                    showNotification(`Помилка сервера: ${resp.status}\n${txt}`, 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                    return;
                }

                const data = await resp.json();
                if (data.success) {
                    showNotification(data.message, 'success');
                    usernameInput.value = '';
                } else if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification('Невідома відповідь сервера', 'error');
                }

            } catch (err) {
                console.error(err);
                showNotification('Помилка мережі', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
});

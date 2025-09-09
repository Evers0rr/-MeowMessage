document.addEventListener('DOMContentLoaded', function() {
    const actionForms = document.querySelectorAll('.action-form');

    actionForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const url = form.action;
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const contentType = response.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    const data = await response.json();

                    if (data.success || data.request_sent || data.is_subscribed !== undefined) {
                        showNotification(data.message, 'success');

                        if (form.classList.contains('subscribe-form') && data.is_subscribed !== undefined) {
                            const btn = form.querySelector('.subscribe-btn');
                            btn.textContent = data.is_subscribed ? 'Відписатися' : 'Підписатися';
                            btn.classList.toggle('subscribed', data.is_subscribed);

                            const subscriberCount = document.querySelector('.profile-stats span');
                            if (subscriberCount && data.subscribers_count !== undefined) {
                                subscriberCount.textContent = data.subscribers_count + ' підписників';
                            }
                        }

                        if (form.classList.contains('friend-form') && data.is_friend !== undefined) {
                            const btn = form.querySelector('.friend-btn');
                            if (data.is_friend) {
                                btn.textContent = 'Видалити з друзів';
                                btn.classList.add('friend');
                                form.action = `/friends/remove/${btn.dataset.username}/`;
                            } else {
                                btn.textContent = 'Додати в друзі';
                                btn.classList.remove('friend');
                                form.action = `/friends/request/${btn.dataset.username}/`;
                            }
                        }                      
                    } else if (data.error) {
                        showNotification(data.error, 'error');
                    }
                } else {
                    showNotification('Сервер повернув невірний формат відповіді', 'error');
                    console.error('HTML response:', await response.text());
                }
            } catch (err) {
                showNotification(err.message, 'error');
                console.error(err);
            }
        });
    });

    function showNotification(message, type='success') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#4CAF50' : '#f44336'};
            color: white;
            border-radius: 8px;
            z-index: 10000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            opacity: 1;
            transition: opacity 0.5s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 500);
        }, 3000);
    }
});

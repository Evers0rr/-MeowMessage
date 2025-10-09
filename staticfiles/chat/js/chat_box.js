document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;

    const chatType = chatContainer.dataset.chatType;
    const chatId = chatContainer.dataset.chatId;
    const username = chatContainer.dataset.username;
    const form = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-text');
    const fileInput = document.getElementById('message-file');
    const fileName = document.getElementById('file-name');
    const messagesContainer = document.getElementById('chat-messages');
    const noMessages = document.getElementById('no-messages');

    fileInput.addEventListener('change', () => {
        fileName.textContent = fileInput.files.length ? fileInput.files[0].name : '';
    });

    const attachBtn = document.getElementById('attach-btn');
    attachBtn.addEventListener('click', (e) => {
        e.preventDefault();
        fileInput.click();
    });

    function getCSRF() {
        const el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const text = messageInput.value.trim();
        const file = fileInput.files[0];
        if (!text && !file) return;

        const formData = new FormData();
        formData.append('text', text);
        if (file) formData.append('file', file);
        formData.append('content_type', file ? 'file' : 'text');

        let url = '';
        if (chatType === 'group') {
            url = `/chat/group/${chatId}/send/`;
        } else {
            url = `/chat/private/${username}/send/`;
        }

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRF()
                },
                body: formData
            });

            if (!res.ok) {
                const txt = await res.text();
                console.error('Server returned not ok:', res.status, txt);
                alert('Окак... Диви консоль');
                return;
            }

            const data = await res.json();

            if (data.success) {
                const msgDiv = document.createElement('div');
                msgDiv.classList.add('message', 'my-message', 'new-message');

                if (data.file) {
                    const link = document.createElement('a');
                    link.href = data.file;
                    link.textContent = "📎 " + (file ? file.name : "Файл");
                    link.target = "_blank";
                    msgDiv.appendChild(link);
                    if (text) {
                        const textElem = document.createElement('div');
                        textElem.textContent = text;
                        msgDiv.appendChild(textElem);
                    }
                } else {
                    msgDiv.textContent = text;
                }

                messagesContainer.appendChild(msgDiv);
                messageInput.value = '';
                fileInput.value = '';
                fileName.textContent = '';
                if (noMessages) noMessages.style.display = 'none';
                messagesContainer.scrollTop = messagesContainer.scrollHeight;

                setTimeout(() => msgDiv.classList.remove('new-message'), 400);
            } else if (data.error) {
                alert('Окак: ' + data.error);
            }
        } catch (err) {
            console.error('Fetch error:', err);
            alert('Сталася помилка при відправці повідомлення');
        }
    });

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });
});

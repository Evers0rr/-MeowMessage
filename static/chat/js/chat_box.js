document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.getElementById("chat-container");
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const messageText = document.getElementById("message-text");
    const messageFile = document.getElementById("message-file");
    const attachBtn = document.getElementById("attach-btn");
    const filePreview = document.getElementById("file-preview");
    const fileNameSpan = document.getElementById("file-name");
    const removeFileBtn = document.getElementById("remove-file");

    let chatType = chatContainer.dataset.chatType;
    let sendUrl = "";

    if (chatType === "group") {
        sendUrl = `/chat/group/${chatContainer.dataset.chatId}/send/`;
    } else {
        sendUrl = `/chat/private/${chatContainer.dataset.username}/send/`;
    }

    // Прикрепление файла
    attachBtn.addEventListener("click", () => {
        messageFile.click();
    });

    messageFile.addEventListener("change", () => {
        if (messageFile.files.length > 0) {
            fileNameSpan.textContent = messageFile.files[0].name;
            filePreview.style.display = "inline-flex";
        }
    });

    // Удаление файла
    removeFileBtn.addEventListener("click", () => {
        messageFile.value = "";
        filePreview.style.display = "none";
        fileNameSpan.textContent = "";
    });

    // Отправка формы
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formData = new FormData();
        formData.append("text", messageText.value);
        if (messageFile.files[0]) {
            formData.append("file", messageFile.files[0]);
        }

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            const res = await fetch(sendUrl, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                appendMessage(data);
                messageText.value = "";
                messageFile.value = "";
                filePreview.style.display = "none";
                fileNameSpan.textContent = "";
            } else if (data.error) {
                alert(data.error);
            }
        } catch (err) {
            console.error(err);
        }
    });

    function appendMessage(msg) {
        const div = document.createElement("div");
        div.className = `message ${msg.sender === chatContainer.dataset.username ? "other-message" : "my-message"}`;
        div.innerHTML = `
            <div class="message-header">
                <img src="/media/avatars/default.jpg" alt="avatar" class="msg-avatar">
                <span class="sender">${msg.sender}</span>
                <span class="timestamp">${msg.created_at}</span>
            </div>
            ${msg.text ? `<div class="text">${msg.text}</div>` : ""}
            ${msg.file ? `<div class="attachment">
                ${renderFile(msg.file)}
            </div>` : ""}
        `;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function renderFile(fileUrl) {
        const ext = fileUrl.toLowerCase();
        if ([".jpg", ".jpeg", ".png", ".gif", ".webp"].some(e => ext.endsWith(e))) {
            return `<img src="${fileUrl}" alt="Image" class="chat-image">`;
        } else if ([".mp4", ".mov", ".avi", ".webm"].some(e => ext.endsWith(e))) {
            return `<video src="${fileUrl}" controls class="chat-video"></video>`;
        } else {
            return `<a href="${fileUrl}" target="_blank"><i class="bi bi-paperclip"></i> ${fileUrl.split("/").pop()}</a>`;
        }
    }
});

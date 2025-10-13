document.addEventListener("DOMContentLoaded", function () {
    const avatarImg = document.getElementById("avatar-img");
    const avatarInput = document.getElementById("avatarInput");
    const clearAvatarBtn = document.getElementById("clear-avatar-btn");

    const coverImageInput = document.getElementById("coverImageInput");
    const clearCoverBtn = document.getElementById("clear-cover-btn");
    const coverContainer = document.querySelector(".cover-preview-container");

    if (avatarInput) {
        avatarInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file && file.type.startsWith("image/")) {
                avatarImg.src = URL.createObjectURL(file);
                if (clearAvatarBtn) clearAvatarBtn.style.display = "inline-block";
            }
        });
    }

    if (clearAvatarBtn) {
        clearAvatarBtn.addEventListener("click", () => {
            fetch("/users/clear-avatar/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                    Accept: "application/json",
                },
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        avatarImg.src = data.default_avatar_url;
                        clearAvatarBtn.style.display = "none";
                        alert("Аватар очищено!");
                    }
                })
                .catch(err => console.error("Помилка очищення аватара:", err));
        });
    }

    if (coverImageInput) {
        coverImageInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file || !file.type.startsWith("image/")) return;

            const reader = new FileReader();
            reader.onload = (ev) => {
                let coverPreview = document.getElementById("cover-preview");
                if (coverPreview) coverPreview.remove();

                const img = document.createElement("img");
                img.src = ev.target.result;
                img.alt = "Обкладинка";
                img.id = "cover-preview";
                coverContainer.appendChild(img);

                if (clearCoverBtn) clearCoverBtn.style.display = "inline-block";
            };
            reader.readAsDataURL(file);
        });
    }

    if (clearCoverBtn) {
        clearCoverBtn.addEventListener("click", () => {
            if (!confirm("Видалити обкладинку профілю?")) return;

            fetch("/users/clear-cover/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                    Accept: "application/json",
                },
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        if (coverImageInput) coverImageInput.value = "";

                        clearCoverBtn.style.display = "none";

                        let coverPreview = document.getElementById("cover-preview");
                        if (coverPreview) coverPreview.remove();

                        alert("Обкладинку успішно видалено!");
                    }
                })
                .catch(err => console.error("Помилка очищення обкладинки:", err));
        });
    }
});

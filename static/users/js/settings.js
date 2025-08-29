document.addEventListener('DOMContentLoaded', function() {
    const clearBtn = document.getElementById('clear-avatar-btn');
    const avatarImg = document.getElementById('avatar-img');
    const avatarInput = document.getElementById('avatarInput');

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            fetch('/users/clear-avatar/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Accept': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    avatarImg.src = data.default_avatar_url;
                    clearBtn.style.display = 'none';
                    alert('Аватар очищено!');
                } else {
                    alert('Помилка при очищенні аватара.');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Помилка при відправці запиту.');
            });
        });
    }

    if (avatarInput) {
        avatarInput.addEventListener('change', function(event) {
            const [file] = event.target.files;
            if (file) {
                avatarImg.src = URL.createObjectURL(file);
                clearBtn.style.display = 'inline-block';
            }
        });
    }
});

    form.addEventListener('submit', function(e){
        e.preventDefault();
        const formData = new FormData(form);

        fetch("{% url 'settings' %}", {
            method: "POST",
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(res => res.json())
        .then(data => {
            if(data.success){
                alert(data.message);
            } else {
                let errors = "";
                for(const field in data.errors){
                    errors += field + ": " + data.errors[field].join(", ") + "\n";
                }
                alert("Помилки:\n" + errors);
            }
        });
    });


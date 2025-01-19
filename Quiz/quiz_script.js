function toggleDropdown() {
    const dropdown = document.querySelector('.options-container');
    dropdown.classList.toggle('show');
    const box = document.querySelector('.select-box');
    box.classList.toggle('open');
}

function selectOption(element, value) {
    const box = document.querySelector('.select-box');
    box.textContent = value;
    box.dataset.value = value;
    box.style.color = element.style.color;
    toggleDropdown();
}

async function startQuiz() {
    const name = document.getElementById('name').value;
    const difficulty = document.querySelector('.select-box').dataset.value;

    if (!name || !difficulty) {
        alert('Заповніть усі поля!');
        return;
    }

    localStorage.setItem("userName", name);
    localStorage.setItem("difficulty", difficulty);

    const response = await fetch('/api/start-quiz', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, difficulty })
    });

    if (response.ok) {
        const result = await response.json();
        window.location.href = result.redirect_to;
    } else {
        alert('Упс... Щось пішло не так =(');
    }
}

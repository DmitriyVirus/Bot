let timer;
let timeLeft = 7;
let buttonsEnabled = true;

async function loadQuestion() {
    const loadingIndicator = document.getElementById("loading");
    const questionContainer = document.getElementById("question-container");
    const timerElement = document.getElementById("timer");
    const optionsContainer = document.getElementById("options");

    try {
        loadingIndicator.style.display = "block";
        questionContainer.style.display = "none";
        optionsContainer.innerHTML = "";

        const response = await fetch("/api/get-question");
        const data = await response.json();

        if (data.status === "success") {
            displayQuestionWithOptions(data.question, data.options);
        } else if (data.status === "manual_input") {
            displayManualInputQuestion(data.question);
        } else {
            displayError("Зачекайте пару секунд і перезавантажте.");
        }
    } catch (error) {
        console.error("Помилка:", error);
        displayError("Помилка завантаження питання. Спробуйте ще раз.");
    } finally {
        loadingIndicator.style.display = "none";
        questionContainer.style.display = "block";
        resetTimer();
    }
}

function resetTimer() {
    timeLeft = 7;
    const timerElement = document.getElementById("timer");
    timerElement.textContent = timeLeft;
    timerElement.style.visibility = "visible";
    buttonsEnabled = false;
    disableButtons();

    if (timer) clearInterval(timer);
    startTimer(timerElement);
}

function startTimer(timerElement) {
    timer = setInterval(() => {
        timeLeft--;
        timerElement.textContent = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(timer);
            buttonsEnabled = true;
            enableButtons();
            timerElement.style.visibility = "hidden";
        }
    }, 1000);
}

function enableButtons() {
    const buttons = document.querySelectorAll("button");
    buttons.forEach(button => {
        button.disabled = false;
    });
}

function disableButtons() {
    const buttons = document.querySelectorAll("button");
    buttons.forEach(button => {
        button.disabled = true;
    });
}

function displayQuestionWithOptions(questionText, options) {
    const questionTextElement = document.getElementById("question-text");
    const optionsContainer = document.getElementById("options");

    questionTextElement.textContent = `Дайте відповідь на питання: ${questionText}`;
    optionsContainer.innerHTML = "";

    options.forEach(option => {
        const button = document.createElement("button");
        button.textContent = option;
        button.disabled = true;
        button.onclick = async () => {
            await checkAnswer(questionText, option);
        };
        optionsContainer.appendChild(button);
    });
}

function displayManualInputQuestion(questionText) {
    const questionTextElement = document.getElementById("question-text");
    const optionsContainer = document.getElementById("options");

    questionTextElement.textContent = `Дайте відповідь на питання: ${questionText}`;
    optionsContainer.innerHTML = "";

    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Введіть вашу відповідь";
    const submitButton = document.createElement("button");
    submitButton.textContent = "Відповісти";
    submitButton.onclick = async () => {
        const userAnswer = input.value.trim();
        if (!userAnswer) {
            alert("Введіть відповідь!");
            input.focus();
            return;
        }
        await checkAnswer(questionText, userAnswer);
    };

    optionsContainer.appendChild(input);
    optionsContainer.appendChild(submitButton);
    input.focus();
}

function displayError(message) {
    document.getElementById("question-container").innerHTML = `<h1>${message}</h1>`;
}

async function checkAnswer(questionText, userAnswer) {
    try {
        const response = await fetch("/api/check-answer-and-update", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question: questionText, user_answer: userAnswer })
        });

        const result = await response.json();
        if (result.status === "success") {
            if (result.finished) {
                window.location.href = "/quiz-results";
            } else {
                alert(result.is_correct ? "Все вірно!" : `Неправильно! Правильна відповідь: ${result.correct_answer}`);
                await loadQuestion();
            }
        } else {
            alert("Помилка перевірки: " + result.message);
        }
    } catch (error) {
        console.error("Помилка:", error);
        alert("Щось пішло не так. Спробуйте ще раз.");
    }
}

loadQuestion();

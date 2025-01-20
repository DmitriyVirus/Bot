async function loadQuizResults() {
    try {
        const response = await fetch("/api/quiz-table-data");
        const data = await response.json();

        if (data.status === "success") {
            const tableBody = document.getElementById("results-table-body");
            const rows = tableBody.getElementsByTagName('tr');

            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];

                if (data.table_data[i]) {
                    const rowData = data.table_data[i];
                    row.cells[0].textContent = rowData[0] || '-';
                    row.cells[1].textContent = rowData[1] || '-';
                    row.cells[2].textContent = rowData[2] || '-';
                    row.cells[2].classList.add('result');
                    const score = parseInt(rowData[2], 10);

                    if (score >= 8) {
                        row.cells[2].classList.add('green-result');
                    } else if (score >= 5) {
                        row.cells[2].classList.add('blue-result');
                    } else if (score >= 0) {
                        row.cells[2].classList.add('maroon-result');
                    }
                } else {
                    row.cells[0].textContent = '-';
                    row.cells[1].textContent = '-';
                    row.cells[2].textContent = '-';
                }

                // Выделение строки с результатами текущего участника
                if (row.cells[0].textContent === data.last_user_result.name) {
                    row.classList.add('highlighted-row');
                }
            }

            const lastUserResult = data.last_user_result;
            if (lastUserResult) {
                document.getElementById("user-name").textContent = `Ім'я: ${lastUserResult.name}`;
                document.getElementById("user-level").textContent = `Рівень: ${lastUserResult.difficulty}`;
                document.getElementById("user-result").textContent = `Ваш результат: ${lastUserResult.score}`;
            } else {
                document.getElementById("user-name").textContent = "Ім'я: -";
                document.getElementById("user-level").textContent = "Рівень: -";
                document.getElementById("user-result").textContent = "Ваш результат: -";
            }
        } else {
            alert("Помилка: " + data.message);
        }
    } catch (error) {
        console.error("Помилка завантаження:", error);
        alert("Спробуйте пізніше.");
    }
}

document.addEventListener("DOMContentLoaded", loadQuizResults);

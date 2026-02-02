// Количество строк на странице
const PAGE_SIZE = 5;
let currentPage = 0;

// Загружаем данные из Google Sheets через API бота
// Здесь пример: данные берутся из JSON API (можно реализовать на сервере)
let sheetData = []; // сюда попадут все строки таблицы

async function fetchSheetData() {
    try {
        // Здесь сделаем fetch к эндпоинту бота или серверу
        const res = await fetch('/api/get_sheet'); // нужно сделать такой эндпоинт на сервере
        sheetData = await res.json();
        renderPage();
    } catch (err) {
        console.error("Ошибка при загрузке данных:", err);
        alert("Не удалось загрузить данные таблицы.");
    }
}

// Отображаем текущую страницу
function renderPage() {
    const inputsDiv = document.getElementById("inputs");
    inputsDiv.innerHTML = "";

    const start = currentPage * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, sheetData.length);
    const rowsToShow = sheetData.slice(start, end);

    rowsToShow.forEach((row, rowIndex) => {
        const rowDiv = document.createElement("div");
        rowDiv.className = "row-block";
        rowDiv.dataset.rowIndex = start + rowIndex;

        for (const key in row) {
            const label = document.createElement("label");
            label.innerText = key;
            const input = document.createElement("input");
            input.type = "text";
            input.value = row[key];
            input.dataset.key = key;
            input.dataset.rowIndex = start + rowIndex;

            rowDiv.appendChild(label);
            rowDiv.appendChild(input);
            rowDiv.appendChild(document.createElement("br"));
        }

        inputsDiv.appendChild(rowDiv);
        inputsDiv.appendChild(document.createElement("hr"));
    });
}

// Кнопки перехода между страницами
document.getElementById("prevBtn").addEventListener("click", () => {
    if (currentPage > 0) {
        currentPage--;
        renderPage();
    }
});
document.getElementById("nextBtn").addEventListener("click", () => {
    if ((currentPage + 1) * PAGE_SIZE < sheetData.length) {
        currentPage++;
        renderPage();
    }
});

// Сохранение изменений
document.getElementById("editForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const updatedData = [];

    const inputs = document.querySelectorAll("#inputs input");
    const tempRows = {};

    inputs.forEach(input => {
        const rowIndex = input.dataset.rowIndex;
        const key = input.dataset.key;
        if (!tempRows[rowIndex]) tempRows[rowIndex] = {};
        tempRows[rowIndex][key] = input.value;
    });

    for (const index in tempRows) {
        updatedData.push(tempRows[index]);
    }

    console.log("Данные для отправки:", updatedData);

    try {
        // Отправляем изменения на сервер
        const res = await fetch('/api/update_sheet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedData)
        });
        const result = await res.json();
        alert(result.message || "Данные сохранены!");
        // Можно перезагрузить страницу
        await fetchSheetData();
    } catch (err) {
        console.error("Ошибка при сохранении:", err);
        alert("Ошибка при сохранении данных.");
    }
});

// Инициализация
fetchSheetData();

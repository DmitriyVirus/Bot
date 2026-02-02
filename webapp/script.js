// Количество строк на странице
const PAGE_SIZE = 5;
let currentPage = 0;

// Данные из таблицы
let sheetData = [];

// Соответствие ключей и отображаемых названий
const columnMap = {
    "user_id": "ID",
    "username": "@ имя в ТГ",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "name": "Ник+Имя",
    "aliases": "Прозвища",
    "about": "Инфа"
};

// Поля, которые можно редактировать
const editableFields = ["name", "aliases", "about"];

async function fetchSheetData() {
    try {
        const res = await fetch('/api/get_sheet');
        sheetData = await res.json();
        renderPage();
    } catch (err) {
        console.error("Ошибка при загрузке данных:", err);
        alert("Не удалось загрузить данные таблицы.");
    }
}

function renderPage() {
    const inputsDiv = document.getElementById("inputs");
    inputsDiv.innerHTML = "";

    const start = currentPage * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, sheetData.length);
    const rowsToShow = sheetData.slice(start, end);

    rowsToShow.forEach((row, rowIndex) => {
        const rowDiv = document.createElement("div");
        rowDiv.className = "row-block";

        for (const key in row) {
            const label = document.createElement("span");
            label.innerText = columnMap[key] || key;

            if (editableFields.includes(key)) {
                const input = document.createElement("input");
                input.type = "text";
                input.value = row[key];
                input.dataset.key = key;
                input.dataset.rowIndex = start + rowIndex;
                rowDiv.appendChild(label);
                rowDiv.appendChild(input);
            } else {
                const span = document.createElement("div");
                span.className = "readonly-field";
                span.innerText = row[key];
                rowDiv.appendChild(label);
                rowDiv.appendChild(span);
            }
            rowDiv.appendChild(document.createElement("br"));
        }

        // Кнопка удаления участника
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.innerText = "Удалить участника";
        delBtn.addEventListener("click", () => deleteRow(start + rowIndex));
        rowDiv.appendChild(delBtn);

        inputsDiv.appendChild(rowDiv);
    });
}

// Удаление строки
async function deleteRow(rowIndex) {
    const row = sheetData[rowIndex];
    if (!confirm(`Удалить участника ${row.username}?`)) return;

    try {
        const res = await fetch('/api/delete_row', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rowIndex })
        });
        const result = await res.json();
        alert(result.message || "Участник удалён!");
        await fetchSheetData();
    } catch (err) {
        console.error("Ошибка при удалении:", err);
        alert("Ошибка при удалении участника.");
    }
}

// Навигация страниц
function setupNavigation() {
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");

    prevBtn.addEventListener("click", () => {
        if (currentPage > 0) {
            currentPage--;
            renderPage();
        }
    });

    nextBtn.addEventListener("click", () => {
        if ((currentPage + 1) * PAGE_SIZE < sheetData.length) {
            currentPage++;
            renderPage();
        }
    });
}

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

    try {
        const res = await fetch('/api/update_sheet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedData)
        });
        const result = await res.json();
        alert(result.message || "Данные сохранены!");
        await fetchSheetData();
    } catch (err) {
        console.error("Ошибка при сохранении:", err);
        alert("Ошибка при сохранении данных.");
    }
});

// Инициализация
fetchSheetData();
setupNavigation();

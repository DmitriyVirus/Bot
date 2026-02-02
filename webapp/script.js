// Количество строк на странице
const PAGE_SIZE = 5;
let currentPage = 0;

// Все данные таблицы
let sheetData = [];

async function fetchSheetData() {
    const res = await fetch("/api/get_sheet");
    sheetData = await res.json();
    renderPage();
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

        const realRowIndex = start + rowIndex; // ВАЖНО

        for (const key in row) {
            const label = document.createElement("label");
            label.innerText = key;

            const input = document.createElement("input");
            input.type = "text";
            input.value = row[key] ?? "";
            input.dataset.key = key;
            input.dataset.rowIndex = realRowIndex;

            rowDiv.appendChild(label);
            rowDiv.appendChild(input);
            rowDiv.appendChild(document.createElement("br"));
        }

        inputsDiv.appendChild(rowDiv);
        inputsDiv.appendChild(document.createElement("hr"));
    });
}

// Навигация
document.getElementById("prevBtn").onclick = () => {
    if (currentPage > 0) {
        currentPage--;
        renderPage();
    }
};

document.getElementById("nextBtn").onclick = () => {
    if ((currentPage + 1) * PAGE_SIZE < sheetData.length) {
        currentPage++;
        renderPage();
    }
};

// Сохранение
document.getElementById("editForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const inputs = document.querySelectorAll("#inputs input");
    const tempRows = {};

    inputs.forEach(input => {
        const rowIndex = input.dataset.rowIndex;
        const key = input.dataset.key;

        if (!tempRows[rowIndex]) tempRows[rowIndex] = {};
        tempRows[rowIndex][key] = input.value;
    });

    const updatedData = Object.values(tempRows);

    console.log("Отправляем:", updatedData);

    const res = await fetch("/api/update_sheet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData)
    });

    const result = await res.json();
    alert(result.message || "Сохранено");

    await fetchSheetData();
});

// Инициализация
fetchSheetData();

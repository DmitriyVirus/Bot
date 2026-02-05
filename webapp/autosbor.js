let data = [];
let currentCol = 0;

async function loadData() {
    const res = await fetch("/api/get_autosbor");
    data = await res.json();

    if (!Array.isArray(data) || data.length === 0) {
        document.getElementById("collectorName").innerText = "Нет данных";
        return;
    }

    render();
}

function render() {
    if (!data.length) return;

    const col = data[currentCol];
    if (!col) return;

    // Заголовок — номер столбца
    document.getElementById("collectorName").innerText = `Пак ${currentCol + 1}`;

    const fields = document.getElementById("fields");
    fields.innerHTML = "";

    // Выводим все 7 строк (включая первую) и делаем их редактируемыми
    for (let i = 0; i < 7; i++) {
        const div = document.createElement("div");
        div.className = "field";

        const input = document.createElement("input");
        // Если данных нет, выводим пустую строку
        input.value = col.values[i] || "";
        input.oninput = e => col.values[i] = e.target.value;

        div.appendChild(input);
        fields.appendChild(div);
    }
}

function prevColumn() {
    if (currentCol > 0) {
        currentCol--;
        render();
    }
}

function nextColumn() {
    if (currentCol < data.length - 1) {
        currentCol++;
        render();
    }
}

async function saveColumn() {
    const col = data[currentCol];

    await fetch("/api/save_autosbor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            column_index: currentCol,
            values: col.values
        })
    });

    alert("Сохранено");
}

loadData();

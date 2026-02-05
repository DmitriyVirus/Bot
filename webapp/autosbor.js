let data = [];
let currentCol = 0;

async function loadData() {
    const res = await fetch("/api/get_autosbor");
    data = await res.json(); 
    render();
}

function render() {
    const col = data[currentCol];
    if (!col) return;

    document.getElementById("collectorName").innerText = col.name;

    const fields = document.getElementById("fields");
    fields.innerHTML = "";

    col.values.forEach((val, i) => {
        const div = document.createElement("div");
        div.className = "field";

        const input = document.createElement("input");
        input.value = val;
        input.oninput = e => col.values[i] = e.target.value;

        div.appendChild(input);
        fields.appendChild(div);
    });
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

const PAGE_SIZE = 5;
let currentPage = 0;
let sheetData = [];

const columnMap = {
    user_id: "ID",
    username: "@ имя в ТГ",
    first_name: "Имя",
    last_name: "Фамилия",
    name: "Ник+Имя",
    aliases: "Прозвища",
    about: "Инфа"
};

const editableFields = ["name", "aliases", "about"];

async function fetchSheetData() {
    const res = await fetch("/api/get_sheet");
    sheetData = await res.json();
    currentPage = 0;
    renderPage();
}

function renderPage() {
    const inputsDiv = document.getElementById("inputs");
    inputsDiv.innerHTML = "";

    const start = currentPage * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, sheetData.length);

    sheetData.slice(start, end).forEach(row => {
        const rowDiv = document.createElement("div");
        rowDiv.className = "row-block";

        for (const key in columnMap) {
            if (!(key in row)) continue;

            const label = document.createElement("span");
            label.innerText = columnMap[key];
            rowDiv.appendChild(label);

            if (editableFields.includes(key)) {
                const input = document.createElement("input");
                input.type = "text";
                input.value = row[key] || "";
                input.dataset.key = key;
                input.dataset.userId = String(row.user_id); // ВАЖНО
                rowDiv.appendChild(input);
            } else {
                const div = document.createElement("div");
                div.className = "readonly-field";
                div.innerText = row[key] ?? "";
                rowDiv.appendChild(div);
            }

            rowDiv.appendChild(document.createElement("br"));
        }

        const delBtn = document.createElement("button");
        delBtn.innerText = "Удалить участника";
        delBtn.onclick = () => deleteRow(row.user_id, row.username);
        rowDiv.appendChild(delBtn);

        inputsDiv.appendChild(rowDiv);
    });
}

async function deleteRow(userId, username) {
    if (!confirm(`Удалить участника ${username}?`)) return;

    const res = await fetch("/api/delete_row", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: String(userId) })
    });

    if (!res.ok) {
        alert("Ошибка удаления");
        return;
    }

    await fetchSheetData();
}

document.getElementById("editForm").addEventListener("submit", async e => {
    e.preventDefault();

    const inputs = document.querySelectorAll("#inputs input");
    const updates = {};

    inputs.forEach(input => {
        const userId = input.dataset.userId;
        const key = input.dataset.key;

        if (!updates[userId]) {
            updates[userId] = { user_id: userId };
        }
        updates[userId][key] = input.value;
    });

    const res = await fetch("/api/update_sheet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.values(updates))
    });

    if (!res.ok) {
        alert("Ошибка сохранения");
        return;
    }

    await fetchSheetData();
});

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

fetchSheetData();

function renderPage() {
    const inputsDiv = document.getElementById("inputs");
    inputsDiv.innerHTML = "";

    const start = currentPage * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, sheetData.length);
    const rowsToShow = sheetData.slice(start, end);

    rowsToShow.forEach((row, rowIndex) => {
        const rowDiv = document.createElement("div");
        rowDiv.className = "row-block";

        const realRowIndex = start + rowIndex + 2; // +2 — потому что первая строка заголовки

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

        // Кнопка удалить
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.innerText = "Удалить строку";
        delBtn.onclick = async () => {
            if (!confirm("Удалить эту строку?")) return;

            await fetch("/api/delete_row", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ row_index: realRowIndex })
            });

            await fetchSheetData();
        };

        rowDiv.appendChild(delBtn);
        inputsDiv.appendChild(rowDiv);
        inputsDiv.appendChild(document.createElement("hr"));
    });
}

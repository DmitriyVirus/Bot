async function fetchAdmins() {
    const res = await fetch("/api/get_admins");
    const data = await res.json();

    const container = document.getElementById("admins");
    container.innerHTML = "";

    data.forEach((row, index) => {
        const div = document.createElement("div");
        div.className = "admin-row";

        const idSpan = document.createElement("span");
        idSpan.innerText = row.id;

        const nameSpan = document.createElement("span");
        nameSpan.innerText = row.name;

        const delBtn = document.createElement("button");
        delBtn.innerText = "Удалить";
        delBtn.onclick = async () => {
            if (!confirm(`Удалить администратора ${row.name}?`)) return;

            await fetch("/api/delete_admin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ row_index: index + 2 }) 
                // +2 — заголовок + Google Sheets (1-based)
            });

            fetchAdmins();
        };

        div.appendChild(idSpan);
        div.appendChild(nameSpan);
        div.appendChild(delBtn);

        container.appendChild(div);
    });
}

fetchAdmins();

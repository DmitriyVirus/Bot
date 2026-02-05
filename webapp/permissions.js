async function fetchPermissions() {
    const res = await fetch("/api/get_permissions");
    const data = await res.json();

    const container = document.getElementById("permissions");
    container.innerHTML = "";

    data.forEach((row, index) => {
        const div = document.createElement("div");
        div.className = "permission-row";

        const idSpan = document.createElement("span");
        idSpan.innerText = row.id;

        const nameSpan = document.createElement("span");
        nameSpan.innerText = row.name;

        const delBtn = document.createElement("button");
        delBtn.innerText = "Удалить";
        delBtn.onclick = async () => {
            if (!confirm(`Удалить ${row.name}?`)) return;

            await fetch("/api/delete_permission", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ row_index: index + 2 })
            });

            fetchPermissions();
        };

        div.appendChild(idSpan);
        div.appendChild(nameSpan);
        div.appendChild(delBtn);

        container.appendChild(div);
    });
}

fetchPermissions();

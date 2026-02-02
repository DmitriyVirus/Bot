// Эмуляция данных первой строки
const firstRow = {
  user_id: "123456",
  username: "DDestopia",
  first_name: "Дмитрий",
  last_name: "Лисенко",
  name: "выясняем",
  aliases: "выясняем",
  about: "выясняем"
};

const inputsDiv = document.getElementById("inputs");

for (const key in firstRow) {
    const label = document.createElement("label");
    label.innerText = key;
    const input = document.createElement("input");
    input.type = "text";
    input.value = firstRow[key];
    input.id = key;
    inputsDiv.appendChild(label);
    inputsDiv.appendChild(input);
    inputsDiv.appendChild(document.createElement("br"));
}

document.getElementById("editForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const updatedRow = {};
    for (const key in firstRow) {
        updatedRow[key] = document.getElementById(key).value;
    }
    console.log("Отправляем на сервер:", updatedRow);

    // TODO: Отправить данные обратно боту через Web App Data
    alert("Данные сохранены (тест).");
});

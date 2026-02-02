<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Редактирование таблицы</title>
<link rel="stylesheet" href="style.css">
<style>
  #controlsWrapper {
    display: flex;
    justify-content: flex-start;
    gap: 10px;
    margin-top: 10px;
  }

  #prevBtn, #nextBtn {
    width: 100px;
    height: 40px;
  }

  #saveBtn {
    width: 220px; /* примерно вдвое шире */
    height: 40px;
  }

  .row-block {
    margin-bottom: 10px;
  }

  .row-block input[readonly] {
    background-color: #f0f0f0;
  }
</style>
</head>
<body>
<h2>Редактирование таблицы</h2>

<form id="editForm">
  <div id="inputs"></div>
  <div id="controlsWrapper">
    <button type="button" id="prevBtn">Назад</button>
    <button type="button" id="nextBtn">Вперед</button>
    <button type="submit" id="saveBtn">Сохранить</button>
  </div>
</form>

<script src="webapp/script.js"></script>
</body>
</html>

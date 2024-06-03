<?php

// Проверяем, было ли передано имя файла в параметре GET запроса
if (isset($_GET['name']) && !empty($_GET['name'])) {
    // Собираем путь к файлу JSON
    $filename = '../data/cycles/' . $_GET['name'] . '.json';

    // Проверяем существование файла
    if (file_exists($filename)) {
        // Загружаем содержимое файла JSON
        $json_data = file_get_contents($filename);

        // Пытаемся декодировать JSON данные
        $decoded_data = json_decode($json_data, true);

        // Проверяем успешность декодирования
        if ($decoded_data !== null) {
            // Генерируем HTML форму для редактирования полей JSON
            echo '<form action="save_json.php" method="post" id="jsonForm">';
            foreach ($decoded_data as $key => $value) {
                if ($key === "url") {
                    continue; // Пропускаем поле для URL
                }

                // Проверяем, является ли значение массивом (объектом JSON)
                if (is_array($value)) {
                    echo '<h3 class="text-center">' . htmlspecialchars($key) . '</h3>'; // Заголовок для объекта JSON
                    foreach ($value as $subkey => $subvalue) {
                        // Выводим поля ввода для каждого параметра объекта JSON
                        echo '<label for="' . htmlspecialchars($key . '_' . $subkey) . '">' . htmlspecialchars($subkey) . ':</label>';
                        echo '<input type="text" id="' . htmlspecialchars($key . '_' . $subkey) . '" name="' . htmlspecialchars($key . '_' . $subkey) . '" value="' . htmlspecialchars($subvalue) . '" class="form-control"><br>';
                    }
                } else {
                    // Выводим поля ввода для обычных значений
                    echo '<label for="' . htmlspecialchars($key) . '">' . htmlspecialchars($key) . ':</label>';
                    echo '<input type="text" id="' . htmlspecialchars($key) . '" name="' . htmlspecialchars($key) . '" value="' . htmlspecialchars($value) . '" class="form-control"><br>';
                }
            }
            // Добавляем кнопку для добавления нового поля
            echo '<button type="button" onclick="addNewField()" class="btn btn-dark bg-gradient my-2">Добавить новое поле</button><br>';
            // Добавляем скрытое поле с именем файла
            echo '<input type="hidden" name="filename" value="data/cycles/' . htmlspecialchars($_GET['name']) . '.json" class="form-control">';
            // Добавляем кнопку для отправки формы
            echo '<input type="submit" value="Сохранить" class="btn btn-success bg-gradient">';
            echo '</form>';
        } else {
            // Если декодирование JSON не удалось, отправляем сообщение об ошибке
            echo '<p>Error: Failed to decode JSON</p>';
        }
    } else {
        // Если файл не существует, отправляем сообщение об ошибке
        echo '<p>Error: File not found</p>';
    }
} else {
    // Если параметр name не был передан, отправляем сообщение об ошибке
    echo '<p>Error: Name parameter is missing</p>';
}

?>

<script>
    function addNewField() {
        // Создаем новые элементы input
        var newInputGroup = document.createElement("div");
        newInputGroup.classList.add("row", "mb-3");

        // Создаем первый input для ключа
        var newKeyInputGroup = document.createElement("div");
        newKeyInputGroup.classList.add("col-6");
        newKeyInputGroup.classList.add("col-md-3");
        var newKeyInput = document.createElement("input");
        newKeyInput.setAttribute("type", "text");
        newKeyInput.setAttribute("name", "new_key[]");
        newKeyInput.setAttribute("placeholder", "Новый ключ");
        newKeyInput.classList.add("form-control");
        newKeyInputGroup.appendChild(newKeyInput);

        // Создаем разделитель ":"
        var separatorSpan = document.createElement("span");
        separatorSpan.classList.add("input-group-text");

        // Создаем второй input для значения
        var newValueInputGroup = document.createElement("div");
        newValueInputGroup.classList.add("col-6");
        newValueInputGroup.classList.add("col-md-9");
        var newValueInput = document.createElement("input");
        newValueInput.setAttribute("type", "text");
        newValueInput.setAttribute("name", "new_value[]");
        newValueInput.setAttribute("placeholder", "Значение для нового ключа");
        newValueInput.classList.add("form-control");
        newValueInputGroup.appendChild(newValueInput);

        // Добавляем созданные элементы в общий контейнер
        newInputGroup.appendChild(newKeyInputGroup);
        newInputGroup.appendChild(newValueInputGroup);

        // Находим форму и добавляем новые поля перед кнопкой "Сохранить"
        var form = document.getElementById("jsonForm");
        form.insertBefore(newInputGroup, form.lastElementChild.previousElementSibling);
    }
</script>

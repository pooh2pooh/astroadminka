<?php

$replys_dir = '../data/replys';
$files = scandir($replys_dir);
$categories = [];

// Здесь парсятся все доступные категории,
// и хранятся в $categories
foreach ($files as $file) {
    if (pathinfo($file, PATHINFO_EXTENSION) === 'json') {
        $json_data = file_get_contents($replys_dir . '/' . $file);
        $reply = json_decode($json_data, true);

        if ($reply !== null) {
            $category = isset($reply['category']) ? $reply['category'] : 'Uncategorized';
            if (!in_array($category, $categories)) {
                $categories[] = $category;
            }
        } else {
            echo '<span class="text-danger small">Ошибка при декодировании JSON файла: ' . $file . '</span>';
        }
    }
}


// Проверяем, было ли передано имя файла в параметре GET запроса
if (isset($_GET['name']) && !empty($_GET['name'])) {
    // Собираем путь к файлу JSON
    $filename = '../data/replys/' . $_GET['name'] . '.json';

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
                    if ($key === "keyboard" && empty($value)) {
                        continue; // Пропускаем пустой список keyboard
                    }

                    echo '<h3 class="text-center">' . htmlspecialchars($key) . '</h3>'; // Заголовок для объекта JSON
                    foreach ($value as $index => $item) {
                        // Выводим поля ввода для каждого параметра объекта JSON
                        echo '<div class="row mb-3">';
                        foreach ($item as $subkey => $subvalue) {
                            echo '<div class="col-6">';
                            echo '<label for="' . htmlspecialchars($key . '_' . $index . '_' . $subkey) . '">' . htmlspecialchars($subkey) . ':</label>';
                            echo '<input type="text" id="' . htmlspecialchars($key . '_' . $index . '_' . $subkey) . '" name="' . htmlspecialchars($key . '_' . $index . '_' . $subkey) . '" value="' . $subvalue . '" class="form-control">';
                            echo '</div>';
                        }
                        echo '</div>';
                    }
                } else if ($key == 'category') {
                    //
                    if ($key == "category") {
                        $name = '<strong>Категория:</strong><br><small class="text-muted">&nbsp;к какой категории относится сообщение</small>';
                    }
                    echo '<label for="' . htmlspecialchars($key) . '">' . (isset($name) && $name !== null ? $name : htmlspecialchars($key)) . '</label>';
                    $name = null;
                    echo '<select id="' . htmlspecialchars($key) . '" name="' . htmlspecialchars($key) . '" class="form-control">';
                    foreach ($categories as $category) {
                        $selected = ($category == $value) ? 'selected' : '';
                        echo '<option value="' . htmlspecialchars($category) . '" ' . $selected . '>' . htmlspecialchars($category) . '</option>';
                    }
                    echo '</select><br>';
                } else {
                    if ($key == "title") {
                        $name = '<strong>Заголовок:</strong><br><small class="text-muted">&nbsp;отображается везде</small>';
                    }
                    if ($key == "message") {
                        $name = '<strong>Сообщение:</strong><br><small class="text-muted">&nbsp;сообщение которое отправляет бот</small>';
                    }
                    // Выводим поля ввода для обычных значений
                    echo '<label for="' . htmlspecialchars($key) . '">' . (isset($name) && $name !== null ? $name : htmlspecialchars($key)) . '</label>';
                    echo '<input type="text" id="' . htmlspecialchars($key) . '" name="' . htmlspecialchars($key) . '" value="' . $value . '" class="form-control"><br>';
                }
            }
            // Добавляем кнопку для добавления нового поля
            echo '<button type="button" onclick="addNewField()" class="btn btn-dark bg-gradient my-2">Добавить новое поле</button><br>';
            // Добавляем скрытое поле с именем файла
            echo '<input type="hidden" name="filename" value="data/replys/' . htmlspecialchars($_GET['name']) . '.json" class="form-control">';
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

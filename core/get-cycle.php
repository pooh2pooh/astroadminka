<?php

$cycles_dir = '../data/cycles';
$files = scandir($cycles_dir);
$categories = [];

// Здесь парсятся все доступные категории,
// и хранятся в $categories
foreach ($files as $file) {
    if (pathinfo($file, PATHINFO_EXTENSION) === 'json') {
        $json_data = file_get_contents($cycles_dir . '/' . $file);
        $cycle = json_decode($json_data, true);

        if ($cycle !== null) {
            $category = isset($cycle['category']) ? $cycle['category'] : 'Uncategorized';
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
                if ($key === "trigger") {
                    $trigger = $value;
                }

                // Проверяем, является ли значение массивом (объектом JSON),
                // тогда реализуем сложную логику обработки таких объектов
                if (is_array($value)) {
                    echo '<h3 class="text-center">' . htmlspecialchars($key) . '</h3>'; // Заголовок для объекта JSON
                    foreach ($value as $subkey => $subvalue) {
                        // Выводим поля ввода для каждого параметра объекта JSON
                        echo '<label for="' . htmlspecialchars($key . '_' . $subkey) . '">' . htmlspecialchars($subkey) . ':</label>';
                        echo '<input type="text" id="' . htmlspecialchars($key . '_' . $subkey) . '" name="' . htmlspecialchars($key . '_' . $subkey) . '" value="' . htmlspecialchars($subvalue) . '" class="form-control"><br>';
                    }
                } else if (preg_match("/^\d{1,2}\/\d{2}\/\d{4}$/", $key)) {
                    // Строка соответствует маске даты "дд/мм/гггг"
                    $dates[$key] = $value;
                } else if ($key == 'category') {
                    //
                    if ($key == "category") {
                        $name = '<strong>Категория:</strong><br><small class="text-muted">&nbsp;к какой категории относится цикл</small>';
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
                    // Иначе выводим поля ввода для обычных значений,
                    // простые инпуты с заголовками
                    if ($key == "title") {
                        $name = '<strong>Заголовок:</strong><br><small class="text-muted">&nbsp;отображается везде</small>';
                    }
                    if ($key == "tooltip") {
                        $name = '<strong>Подсказка:</strong><br><small class="text-muted">&nbsp;тестовая функция для админ-панели, отображает подсказку при наведении курсора на элемент</small>';
                    }
                    if ($key == "trigger") {
                        $name = '<strong>Триггер:</strong><br><small class="text-muted">&nbsp;с помощью него настраивается события для срабатывания цикла</small>';
                    }

                    echo '<label for="' . htmlspecialchars($key) . '">' . (isset($name) && $name !== null ? $name : htmlspecialchars($key)) . '</label>';
                    $name = null;
                    echo '<input type="text" id="' . htmlspecialchars($key) . '" name="' . htmlspecialchars($key) . '" value="' . htmlspecialchars($value) . '" class="form-control"><br>';
                }
            }

            // Обрабатываем список дат для цикла,
            // здесь же скрываем историю дат, всегда показываем 3 самые актуальные
            if (isset($dates) && is_array($dates)) {
                $counter = 0; // Счетчик выводимых инпутов
                $hiddenInputs = []; // Массив для хранения скрытых инпутов
                foreach (array_reverse($dates) as $key => $value) {
                    if ($counter < 3) { // Проверяем, не превышен ли лимит вывода
                        echo '<label for="' . htmlspecialchars($key) . '">' . htmlspecialchars($key) . ':</label>';
                        echo '<input type="text" id="' . htmlspecialchars($key) . '" name="' . htmlspecialchars($key) . '" value="' . htmlspecialchars($value) . '" class="form-control"><br>';
                        $counter++;
                    } else { // Если превышен, добавляем инпуты в массив для скрытия
                        $hiddenInputs[$key] = $value;
                    }
                }

                // Если есть скрытые инпуты, выводим кнопку для их отображения
                if (!empty($hiddenInputs)) {
                    echo '<div class="accordion" id="collapseMenu">';
                    echo '<div class="accordion-item">';
                    echo '<h2 class="accordion-header" id="headingCollapse">';
                    echo '<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseHidden" aria-expanded="false" aria-controls="collapseHidden">';
                    echo 'Показать все поля';
                    echo '</button>';
                    echo '</h2>';
                    echo '<div id="collapseHidden" class="accordion-collapse collapse" aria-labelledby="headingCollapse" data-bs-parent="#collapseMenu">';
                    echo '<div class="accordion-body">';

                    // Выводим скрытые инпуты
                    foreach ($hiddenInputs as $key => $value) {
                        echo '<label for="' . htmlspecialchars($key) . '">' . htmlspecialchars($key) . ':</label>';
                        echo '<input type="text" id="' . htmlspecialchars($key) . '" name="' . htmlspecialchars($key) . '" value="' . htmlspecialchars($value) . '" class="form-control"><br>';
                    }

                    echo '</div>';
                    echo '</div>';
                    echo '</div>';
                    echo '</div>';
                }
            }

            // Добавляем кнопку для добавления нового поля,
            // здесь можно указать несколько триггеров,
            // для которых будет выводится кнопка "Добавить новое поле"
            if (isset($trigger) && $trigger == 'exact_day') {
                echo '<button type="button" onclick="addNewField()" class="btn btn-dark bg-gradient my-2">Добавить новое поле</button><br>';
            }
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

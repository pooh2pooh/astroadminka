<?php

    // Проверяем, было ли передано имя файла в параметре GET запроса
    if (isset($_GET['name']) && !empty($_GET['name'])) {
        // Собираем путь к файлу JSON
        $filename = '../data/subscriptions/' . $_GET['name'] . '.json';

        // Если передан GET параметр new, выводим пустую форму для новой подписки
        if ($_GET['name'] === 'new') {
            $empty_data = [
                "filename" => "",
                "title" => "",
                "price" => "",
                "url" => "",
                "allow_cycles" => []
            ];
            renderForm($empty_data);
        } else {
            // Проверяем существование файла
            if (file_exists($filename)) {
                // Загружаем содержимое файла JSON
                $json_data = file_get_contents($filename);

                // Пытаемся декодировать JSON данные
                $decoded_data = json_decode($json_data, true);

                // Проверяем успешность декодирования
                if ($decoded_data !== null) {
                    renderForm($decoded_data);
                } else {
                    // Если декодирование JSON не удалось, отправляем сообщение об ошибке
                    echo '<p>Error: Failed to decode JSON</p>';
                }
            } else {
                // Если файл не существует, отправляем сообщение об ошибке
                echo '<p>Error: File not found</p>';
            }
        }
    } else {
        // Если параметр name не был передан, отправляем сообщение об ошибке
        echo '<p>Error: Name parameter is missing</p>';
    }

    function renderForm($data) {
        // Генерируем HTML форму для редактирования полей JSON
        echo '<form hx-post="/core/set-subscribe.php" id="jsonForm">';
        foreach ($data as $key => $value) {
            if ($key === "url") {
                continue; // Пропускаем поле для URL
            }

            // Проверяем, является ли значение массивом (объектом JSON)
            if (is_array($value)) {

                if ($key === "allow_cycles") {
                    echo '<h3 class="text-center">' . htmlspecialchars($key) . '</h3>'; // Заголовок для объекта JSON
                    // Читаем файлы JSON из директории и выводим чекбоксы
                    $cycles_directory = '../data/cycles/';
                    $cycles_files = scandir($cycles_directory);
                    foreach ($cycles_files as $file) {
                        if ($file !== '.' && $file !== '..' && strpos($file, '.json') !== false) {
                            $cycle_name = substr($file, 0, -5);
                            $checked = (in_array($cycle_name, $value)) ? 'checked' : '';
                            echo '<div class="form-check">';
                            echo '<input class="form-check-input" type="checkbox" name="allow_cycles[]" value="' . htmlspecialchars($cycle_name) . '" ' . $checked . '>';
                            echo '<label class="form-check-label" for="' . htmlspecialchars($cycle_name) . '">' . htmlspecialchars($cycle_name) . '</label>';
                            echo '</div>';
                        }
                    }
                    continue;
                }                    

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
        
        // Добавляем кнопку для отправки формы
        echo '<input type="submit" value="Сохранить" class="btn btn-success bg-gradient me-1">';

        if ($_GET['name'] != 'new') {
            // Добавляем скрытое поле с именем редактируемого файла подписки
            echo '<input type="hidden" name="filename" value="' . htmlspecialchars($_GET['name']) . '">';
            echo '<input type="button" value="Удалить" hx-get="/core/del-subscribe.php?name=' . $_GET['name'] . '" hx-trigger="click" hx-target="#main_window" hx-indicator="#indicator_main_window" class="btn btn-danger bg-gradient me-1">';
        }

        echo '</form>';
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

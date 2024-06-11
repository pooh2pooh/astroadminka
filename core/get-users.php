<?php

    // Функция для загрузки данных из JSON файла
    function loadJSON($filename) {
        $json = file_get_contents($filename);
        return json_decode($json, true);
    }

    // Функция для получения списка файлов JSON в директории
    function getJSONFilesList($dir) {
        $files = scandir($dir);
        $jsonFiles = [];
        foreach ($files as $file) {
            if (pathinfo($file, PATHINFO_EXTENSION) === 'json') {
                $jsonFiles[] = $file;
            }
        }
        return $jsonFiles;
    }

    // Функция для построения таблицы HTML на основе файлов JSON
    function buildTableFromJSONFiles($dir) {
        $cycles_dir = '../data/subscriptions';
        $files = scandir($cycles_dir);
        $subscriptions = [];

        // Здесь парсятся все доступные категории,
        // и хранятся в $categories
        foreach ($files as $file) {
            if (pathinfo($file, PATHINFO_EXTENSION) === 'json') {
                $subscriptions[] = pathinfo($file, PATHINFO_FILENAME);
            }
        }

        $jsonFiles = getJSONFilesList($dir);
        if (empty($jsonFiles)) {
            return '<p>Не удалось найти JSON файлы в указанной папке.</p>';
        }

        $table = '<table class="table table-striped table-sm">
                    <thead>
                        <tr>
                            <th scope="col">#</th>
                            <th scope="col">Имя</th>
                            <th scope="col">Последнее обновление</th>
                            <th scope="col">Рефералы</th>
                            <th scope="col">Подписка</th>
                        </tr>
                    </thead>
                    <tbody>';

        foreach ($jsonFiles as $index => $filename) {
            $userData = loadJSON($dir . '/' . $filename);
            $creationDate = date('Y-m-d H:i:s', filemtime($dir . '/' . $filename));
            $table .= '<tr>
                        <td>' . pathinfo($filename, PATHINFO_FILENAME) . '</td>
                        <td>' . $userData['full_name'] . '</td>
                        <td>' . $creationDate . '</td>
                        <td>' . implode(", ", $userData['referals']) . '</td>';
            $table .= '<td>';
            $isFirst = true; // Флаг для определения первого элемента
            foreach ($subscriptions as $subscription) {
                $checked = ($userData['subscription'] === $subscription || ($isFirst && empty($userData['subscription']))) ? 'checked' : '';
                $uniqueId = 'subscription_' . $index . '_' . htmlspecialchars($subscription);
                $uniqueName = 'user_' . pathinfo($filename, PATHINFO_FILENAME); // Уникальное имя для каждой группы радиокнопок
                $table .= '<label><input type="radio" name="' . $uniqueName . '" value="' . htmlspecialchars($subscription) . '" ' . $checked . ' hx-post="../core/set-user.php" hx-trigger="change" hx-swap="outerHTML"> ' . htmlspecialchars($subscription) . '</label><br>';
                $isFirst = false; // После первой итерации устанавливаем флаг в false
            }
            $table .= '</td>';
            $table .= '</tr>';
        }

        $table .= '</tbody></table>';
        return $table;
    }

    // Укажите путь к директории с файлами JSON
    $jsonFolder = '../data/users';

    // Построение таблицы HTML
    $tableHTML = buildTableFromJSONFiles($jsonFolder);

    // Вывод таблицы HTML
    echo $tableHTML;

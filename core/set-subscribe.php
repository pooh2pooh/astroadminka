<?php

    // Проверяем, было ли передано имя файла в параметре POST запроса
    if (isset($_POST['filename']) && !empty($_POST['filename'])) {
        // Собираем путь к файлу JSON
        $filename = '../data/subscriptions/' . $_POST['filename'] . '.json';

        // Загружаем содержимое файла JSON или создаем новый, если файл не существует
        $decoded_data = [];
        if (file_exists($filename)) {
            $json_data = file_get_contents($filename);
            $decoded_data = json_decode($json_data, true);
        }

        // Обновляем или создаем данные из $_POST
        foreach ($_POST as $key => $value) {
            if ($key !== 'filename') {
                $decoded_data[$key] = $value;
            }
        }

        if (isset($decoded_data['url']) || empty($decoded_data['url']))
            $decoded_data['url'] = '/core/get-subscribe.php?name=' . $_POST['filename'];

        // Кодируем обновленные данные обратно в JSON формат
        $updated_json_data = json_encode($decoded_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

        // Пытаемся записать обновлённые данные обратно в файл
        if (file_put_contents($filename, $updated_json_data) !== false) {
            echo 'Данные успешно обновлены.';
            // echo 'Данные успешно обновлены в файле ' . htmlspecialchars($filename);
        } else {
            echo 'Ошибка при записи данных в файл ' . htmlspecialchars($filename);
        }
    } else {
        // Если параметр filename не был передан, отправляем сообщение об ошибке
        echo 'Ошибка: Параметр filename отсутствует в запросе';
    }

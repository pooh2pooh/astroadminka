<?php

    // Проверяем, было ли передано имя файла в параметре GET запроса
    if (isset($_GET['name']) && !empty($_GET['name'])) {
        // Формируем путь к файлу JSON
        $filename = '../data/subscriptions/' . $_GET['name'] . '.json';

        // Проверяем существование файла
        if (file_exists($filename)) {
            // Пытаемся удалить файл
            if (unlink($filename)) {
                echo 'Файл успешно удален.';
            } else {
                echo 'Ошибка: Не удалось удалить файл.';
            }
        } else {
            echo 'Ошибка: Файл не существует.';
        }
    } else {
        echo 'Ошибка: Параметр name отсутствует в запросе.';
    }

<?php

// Проверяем, был ли отправлен POST запрос
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    // Проверяем, есть ли в запросе данные
    if (!empty($_POST)) {
        // Перебираем полученные данные
        foreach ($_POST as $key => $value) {
            // Проверяем, соответствует ли ключ формату "user_<ID>"
            if (preg_match('/^user_\d+$/', $key)) {
                // Извлекаем ID пользователя из ключа
                $userId = substr($key, 5); // Удаляем "user_" из ключа, чтобы получить только ID

                // Формируем путь к файлу пользователя
                $filePath = '../data/users/' . $userId . '.json';

                // Проверяем, существует ли файл пользователя
                if (file_exists($filePath)) {
                    // Загружаем содержимое файла JSON
                    $userData = json_decode(file_get_contents($filePath), true);

                    // Обновляем параметр subscription
                    $userData['subscription'] = $value;

                    // Записываем обновленные данные обратно в файл
                    file_put_contents($filePath, json_encode($userData, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));

                    // Возвращаем анимацию загрузки
                    echo '<img src="../assets/loader.gif" alt="Loading..." width="32"/>';
                    exit; // Завершаем выполнение скрипта после отправки изображения
                } else {
                    // Если файл пользователя не существует, возвращаем ошибку
                    echo '<img src="../assets/loader.gif" alt="Loading..." width="32"/>';
                    exit; // Завершаем выполнение скрипта после отправки изображения
                }
            } else {
                // Если ключ не соответствует формату "user_<ID>", игнорируем его
                continue;
            }
        }
    } else {
        // Если данные в POST запросе отсутствуют, возвращаем ошибку
        echo '<img src="../assets/loader.gif" alt="Loading..." width="32"/>';
        exit; // Завершаем выполнение скрипта после отправки изображения
    }
} else {
    // Если запрос не POST, возвращаем ошибку
    echo '<img src="../assets/loader.gif" alt="Loading..." width="32"/>';
    exit; // Завершаем выполнение скрипта после отправки изображения
}

?>

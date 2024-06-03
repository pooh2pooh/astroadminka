<?php

function updateJsonFileIfValid($postData) {
    if (!isset($postData['filename']) || !file_exists($postData['filename'])) {
        return "Файл JSON не найден.";
    }

    // Получение данных из файла JSON
    $jsonFile = $postData['filename'];
    $jsonData = json_decode(file_get_contents($jsonFile), true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        return "Ошибка чтения JSON файла.";
    }

    // Преобразование данных формы в соответствующий формат
    $updatedData = $jsonData;

    // Удаляем ключ 'filename' из массива для обновления
    unset($postData['filename']);

    foreach ($postData as $key => $value) {
        if (preg_match('/^keyboard_(\d+)_(.+)$/', $key, $matches)) {
            $index = (int)$matches[1];
            $subkey = $matches[2];
            $updatedData['keyboard'][$index][$subkey] = $value;
        } else {
            $updatedData[$key] = $value;
        }
    }

    // Подсчет обновленных полей
    $updatedFieldsCount = 0;
    foreach ($updatedData as $key => $value) {
        if ($jsonData[$key] !== $value) {
            $updatedFieldsCount++;
        }
    }

    if (file_put_contents($jsonFile, json_encode($updatedData, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) === false) {
        return "Ошибка при записи в JSON файл.";
    }

    $resultMessage = "Данные успешно обновлены в файле JSON.\n";
    $resultMessage .= "Обновлено полей: $updatedFieldsCount\n";
    $resultMessage .= "Новые данные в файле JSON:\n";
    $resultMessage .= "<pre>" . json_encode($updatedData, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "</pre>";

    return $resultMessage;
}

echo nl2br(updateJsonFileIfValid($_POST));

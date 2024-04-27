<?php

// Функция для чтения JSON из файла
function readJSONFile($filename) {
    $json = file_get_contents($filename);
    return json_decode($json, true);
}

// Функция для получения суммы подписки по файлу подписки
function getSubscriptionPrice($subscription) {
    $subscriptionFile = "../data/subscriptions/$subscription.json";
    if (file_exists($subscriptionFile)) {
        $subscriptionData = readJSONFile($subscriptionFile);
        return $subscriptionData['price'] ?? 0;
    } else {
        return 0;
    }
}

// Функция для обхода всех файлов JSON в папке пользователей и подсчета суммы
function calculateTotalPrice() {
    $usersFolder = "../data/users/";
    $totalPrice = 0;

    // Получаем список файлов в папке пользователей
    $userFiles = glob($usersFolder . "*.json");
    
    // Обходим каждый файл пользователей
    foreach ($userFiles as $userFile) {
        $userData = readJSONFile($userFile);
        $subscription = $userData['subscription'] ?? null;
        if ($subscription !== null) {
            $price = getSubscriptionPrice($subscription);
            $totalPrice += $price;
        }
    }

    return $totalPrice;
}

// Вызываем функцию для подсчета общей суммы
$totalPrice = calculateTotalPrice();

// Возвращаем результат
if ($totalPrice > 0) {
    echo "<span class=\"text-success\">+$totalPrice</span>";
} else {
    echo "0";
}

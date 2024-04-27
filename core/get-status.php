<?php

	// Команда для поиска PID процесса Python
	$command = "pgrep -f 'python astrobot.py'";

	// Выполняем команду и получаем результат
	$output = shell_exec($command);

	// Проверяем, есть ли процесс в результате выполнения команды
	if (!empty($output)) {
		echo '<span class="bg-success p-1">ДОСТУПЕН</span>';
	} else {
		echo '<span class="bg-danger p-1">НЕДОСТУПЕН</span>';
	}
		
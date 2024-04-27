<ul class="nav flex-column"><?php
  // Here $json_data temp var!
  $json_data = file_get_contents('../data/menu.json');
  $menu = json_decode($json_data, true);

  if ($menu === null) {
    die('<p class="text-danger small">Ошибка при декодировании меню из JSON</p>');
  }

  // Выводим ссылки меню в требуемом формате
  foreach ($menu['links'] as $link) {
      if (isset($link['title']) && isset($link['url'])) {
          echo '<li class="nav-item">';
          $tooltip = isset($link['tooltip']) ? (strlen($link['tooltip']) ? 'data-bs-placement="right" data-bs-toggle="tooltip" data-bs-title="' . $link['tooltip'] .'" data-bs-delay=\'{"show":250,"hide":0}\'' : '') : '';
          echo '<a hx-get="' . $link['url'] . '" hx-trigger="click" hx-target="#main_window" hx-indicator="#indicator_main_window" class="nav-link d-flex align-items-center gap-2" aria-current="page" href="#" ' . $tooltip . '" data-bs-dismiss="offcanvas" data-bs-target="#sidebarMenu">';
          echo '<svg class="bi"><use xlink:href="/assets/icons.svg#' . $link['icon'] . '"/></svg>';
          echo $link['title'];
          echo '</a>';
          echo '</li>';
      } else if (isset($link['title']) && isset($link['items_from_dir'])) {
          echo '<h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-body-secondary text-uppercase">';
          echo '<span>' . $link['title'] . '</span>';
        
        if (isset($link['buttons'])) {
          foreach ($link['buttons'] as $button) {
              $tooltip = isset($button['tooltip']) ? (strlen($button['tooltip']) ? 'data-bs-toggle="tooltip" data-bs-title="' . $button['tooltip'] .'"' : '') : '';
              echo '<a class="link-secondary" hx-get="' . $button['url'] . '" hx-trigger="click" hx-target="#main_window" hx-indicator="#indicator_main_window" aria-label="' . $button['title'] . '" ' . $tooltip . '>';
              echo '<svg class="bi"><use xlink:href="/assets/icons.svg#' . $button['icon'] . '"/></svg>';
              echo '</a>';
          }
        }
  
        echo '</h6>';

        if (isset($link['items_from_dir'])) {

          // Получаем список файлов в директории
          $files = scandir($link['items_from_dir']);

          // Перебираем файлы
          foreach ($files as $file) {
            // Проверяем, является ли файл JSON файлом
            if (pathinfo($file, PATHINFO_EXTENSION) === 'json') {
                // Читаем содержимое JSON файла
                // Here $json_data temp var!
                $json_data = file_get_contents($link['items_from_dir'] . '/' . $file);
                // Декодируем JSON
                $cycle = json_decode($json_data, true);
                // Проверяем успешность декодирования
                if ($cycle !== null) {
                    echo '<li class="nav-item">';
                    $tooltip = isset($cycle['tooltip']) ? (strlen($cycle['tooltip']) ? 'data-bs-placement="right" data-bs-toggle="tooltip" data-bs-title="' . $cycle['tooltip'] .'" data-bs-delay="{\'show\':250,\'hide\':0}\"' : '') : '';
                    echo '<a hx-get="' . $cycle['url'] . '" hx-trigger="click" hx-target="#main_window" hx-indicator="#indicator_main_window" class="nav-link d-flex align-items-center gap-2" aria-current="page" href="#" ' . $tooltip . ' data-bs-dismiss="offcanvas" data-bs-target="#sidebarMenu">';
                    echo isset($cycle['icon']) && $cycle['icon'] !== '' ? '<svg class="bi"><use xlink:href="/assets/icons.svg#' . $cycle['icon'] . '"/></svg>' : '';
                    echo $cycle['title'];
                    echo '</a>';
                    echo '</li>';
                } else {
                    echo '<span class="text-danger small">Ошибка при декодировании JSON файла: ' . $file . '</span>';
                }
            }
          }

        }
      }
  }
?></ul>

<hr class="my-3">

<ul class="nav flex-column mb-auto">
  <li class="nav-item">
    <a class="nav-link d-flex align-items-center gap-2" href="#">
      <svg class="bi"><use xlink:href="/assets/icons.svg#question-circle"/></svg>
      Справка
    </a>
  </li>
</ul>

<!-- Tooltips for sidebar -->
<script type="text/javascript">
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
</script>

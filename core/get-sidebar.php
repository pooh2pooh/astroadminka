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
            $files = scandir($link['items_from_dir']);
            $categories = [];
            $uncategorized = [];

            foreach ($files as $file) {
                if (pathinfo($file, PATHINFO_EXTENSION) === 'json') {
                    $json_data = file_get_contents($link['items_from_dir'] . '/' . $file);
                    $cycle = json_decode($json_data, true);

                    if ($cycle !== null) {
                        $category = isset($cycle['category']) ? $cycle['category'] : 'Uncategorized';
                        if ($category === 'Uncategorized') {
                            $uncategorized[] = $cycle;
                        } else {
                            $categories[$category][] = $cycle;
                        }
                    } else {
                        echo '<span class="text-danger small">Ошибка при декодировании JSON файла: ' . $file . '</span>';
                    }
                }
            }

            echo '<ul class="nav flex-column">';
            foreach ($uncategorized as $cycle) {
                $tooltip = isset($cycle['tooltip']) ? (strlen($cycle['tooltip']) ? 'data-bs-placement="right" data-bs-toggle="tooltip" data-bs-title="' . $cycle['tooltip'] . '" data-bs-delay=\'{"show":250,"hide":0}\' ' : '') : '';
                echo '<li class="nav-item">';
                echo '<a hx-get="' . $cycle['url'] . '" hx-trigger="click" hx-target="#main_window" hx-indicator="#indicator_main_window" class="nav-link scroll-to-top d-flex align-items-center gap-2" aria-current="page" href="#" ' . $tooltip . ' data-bs-dismiss="offcanvas" data-bs-target="#sidebarMenu">';
                echo isset($cycle['icon']) && $cycle['icon'] !== '' ? '<svg class="bi"><use xlink:href="/assets/icons.svg#' . $cycle['icon'] . '"/></svg>' : '';
                echo $cycle['title'];
                echo '</a>';
                echo '</li>';
            }
            echo '</ul>';

            foreach ($categories as $category => $items) {
                $category_id = str_replace(' ', '_', $category);
                echo '<div class="accordion p-1" id="accordion' . $category_id . '">';
                echo '<div class="accordion-item">';
                echo '<h2 class="accordion-header" id="heading' . $category_id . '">';
                echo '<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse' . $category_id . '" aria-expanded="false" aria-controls="collapse' . $category_id . '">';
                echo $category;
                echo '</button>';
                echo '</h2>';
                echo '<div id="collapse' . $category_id . '" class="accordion-collapse collapse" aria-labelledby="heading' . $category_id . '" data-bs-parent="#accordion' . $category_id . '">';
                echo '<div class="accordion-body">';
                echo '<ul class="nav flex-column">';

                foreach ($items as $cycle) {
                    $tooltip = isset($cycle['tooltip']) ? (strlen($cycle['tooltip']) ? 'data-bs-placement="right" data-bs-toggle="tooltip" data-bs-title="' . $cycle['tooltip'] . '" data-bs-delay=\'{"show":250,"hide":0}\' ' : '') : '';
                    echo '<li class="nav-item">';
                    echo '<a hx-get="' . $cycle['url'] . '" hx-trigger="click" hx-target="#main_window" hx-indicator="#indicator_main_window" class="nav-link scroll-to-top d-flex align-items-center gap-2" aria-current="page" href="#" ' . $tooltip . ' data-bs-dismiss="offcanvas" data-bs-target="#sidebarMenu">';
                    echo isset($cycle['icon']) && $cycle['icon'] !== '' ? '<svg class="bi"><use xlink:href="/assets/icons.svg#' . $cycle['icon'] . '"/></svg>' : '';
                    echo $cycle['title'];
                    echo '</a>';
                    echo '</li>';
                }

                echo '</ul>';
                echo '</div>';
                echo '</div>';
                echo '</div>';
                echo '</div>';
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

<!--   Tooltips for sidebar   -->
<script type="text/javascript">
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
</script>

<!--  Scroll to Top for clock link item  -->
<script>
    var links = document.querySelectorAll('.scroll-to-top');
    links.forEach(function(link) {
        link.addEventListener('click', function(e) {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });
</script>

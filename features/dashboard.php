<?php

?>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.3.2/dist/chart.umd.js" integrity="sha384-eI7PSr3L1XLISH8JdDII5YN/njoSsxfbrkCTnJrzXt+ENP5MOVBxD+l6sEG4zoLp" crossorigin="anonymous"></script>
<script src="/assets/js/dashboard.js"></script>

<h1 class="text-center pt-4">₽ <span hx-get="/core/get-bank.php" hx-trigger="every 1s" hx-swap="innerHTML" hx-indicator="#loader"><img src="/assets/loader.gif" width="32"/></span></h1>
<span id="loader" style="display: none;"><img src="/assets/loader.gif" width="32"/></span> <!-- ГРЯЗНЫЙ ХАК ЧТОБЫ ИСПРАВИТЬ ПРЫГАНИЕ ИНТЕРФЕЙСА ПРИ ОБНОВЛЕНИИ ДАННЫХ -->

<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
  <h1 class="h2">Нагрузка за <span class="d-none d-sm-inline">неделю</span></h1>
  <div class="btn-toolbar mb-2 mb-md-0">
    <!-- <div class="btn-group me-2">
      <button type="button" class="btn btn-sm btn-outline-secondary">Share</button>
      <button type="button" class="btn btn-sm btn-outline-secondary">Export</button>
    </div> -->
    <button type="button" class="btn btn-sm btn-outline-secondary dropdown-toggle d-flex align-items-center gap-1">
      <svg class="bi"><use xlink:href="/assets/icons.svg#calendar3"/></svg>
      Текущая неделя
    </button>
  </div>
</div>

<canvas class="my-4 w-100" id="myChart" width="900" height="380"></canvas>

<h2>Пользователи</h2>
<div class="table-responsive small">
  <div hx-get="/core/get-users.php" hx-trigger="every 1s" hx-swap="innerHTML" hx-indicator="#loader">
    <img src="/assets/loader.gif" width="32"/>
  </div>
</div>

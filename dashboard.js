(() => {
  'use strict';

  // Graphs
  const ctx = document.getElementById('myChart');
  let previousData = null;
  let myChart = null;

  // Функция для загрузки JSON из файла
  async function loadJSON(url) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        if (response.status === 404) {
          return null; // Файл не найден
        }
        throw new Error(`Ошибка загрузки: ${response.status}`);
      }
      return response.json();
    } catch (error) {
      console.error('Произошла ошибка при загрузке JSON:', error);
      return null;
    }
  }

  // Загружаем данные из файла JSON для текущей недели
  async function loadWeekActivityData() {
    const currentDate = new Date();
    const year = currentDate.getFullYear();
    const weekNumber = getWeekNumber(currentDate); // Получаем номер текущей недели
    const url = `data/activity_data/week_${year}_${weekNumber}_activity.json`; // Формируем URL файла
    return await loadJSON(url);
  }

  // Получаем номер недели для даты
  function getWeekNumber(date) {
    const yearStart = new Date(date.getFullYear(), 0, 0); // День установлен на 0, что означает последний день предыдущего года
    const pastDays = (date - yearStart) / 86400000;
    const daysInCurrentYear = (date.getFullYear() % 4 == 0 && date.getFullYear() % 100 != 0 || date.getFullYear() % 400 == 0) ? 366 : 365;
    const weekNo = Math.floor((pastDays - yearStart.getDay() + 1) / 7);
    
    if (weekNo === 0) {
        // В случае, если первая неделя начинается с понедельника, текущая неделя еще не началась
        return getWeekNumber(new Date(date.getFullYear() - 1, 11, 31));
    } else {
        return weekNo;
    }
  }

  // Основной код
  async function main() {
    try {
      const weekActivityData = await loadWeekActivityData();
      const daysOfWeek = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];
      const activityCounts = daysOfWeek.map(day => weekActivityData?.[day] || 0); // Заполняем значениями из файла или 0, если нет данных

      // Проверяем, изменились ли данные
      if (!isEqual(previousData, activityCounts)) {
        previousData = activityCounts;

        // Создаем новый график, если он еще не создан
        if (!myChart) {
          myChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: daysOfWeek,
              datasets: [{
                data: activityCounts,
                lineTension: 0,
                backgroundColor: 'transparent',
                borderColor: 'darkred',
                borderWidth: 4,
                pointBackgroundColor: 'red'
              }]
            },
            options: {
              plugins: {
                legend: {
                  display: false
                },
                tooltip: {
                  boxPadding: 3
                }
              },
              scales: {
                y: {
                  beginAtZero: true // Начинать шкалу с 0
                }
              },
              ticks: {
                stepSize: 1 // Шаг шкалы: 1
              }
            }
          });
        } else {
          // Обновляем только измененные данные на графике
          for (let i = 0; i < activityCounts.length; i++) {
            myChart.data.datasets[0].data[i] = activityCounts[i];
          }
          myChart.update();
        }
      }
    } catch (error) {
      console.error('Произошла ошибка:', error);
    }
  }

  // Функция для сравнения двух массивов
  function isEqual(arr1, arr2) {
    if (arr1 === arr2) return true;
    if (arr1 == null || arr2 == null) return false;
    if (arr1.length !== arr2.length) return false;
    for (let i = 0; i < arr1.length; ++i) {
      if (arr1[i] !== arr2[i]) return false;
    }
    return true;
  }

  // Обновляем график каждые 3 секунды
  setInterval(main, 1000);
})();

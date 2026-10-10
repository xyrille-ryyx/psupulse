/* PSU Pulse dashboard charts (Chart.js 4). Colors come from CSS tokens. */
(function () {
  if (!window.Chart) return;

  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const palette = () => ({
    pos: css('--pos'), neg: css('--neg'), neu: css('--neu'),
    text: css('--text-2'), grid: css('--border'), surface: '#fafbff',
  });
  const readJSON = (id) => {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : null;
  };

  function baseOptions(c) {
    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
    Chart.defaults.color = c.text;
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 250 },
      plugins: {
        legend: { display: false }, // the legend lives in the side panel
        tooltip: { padding: 10, boxPadding: 4, usePointStyle: true },
      },
    };
  }

  function trendChart(c) {
    const data = readJSON('trend-data');
    const el = document.getElementById('trend-chart');
    if (!data || !el) return;
    let mode = 'share';
    const series = [['Positive', 'positive', c.pos], ['Negative', 'negative', c.neg], ['Neutral', 'neutral', c.neu]];
    const values = (key) => (mode === 'share' ? data[key] : data[key + '_n']);

    const chart = new Chart(el, {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: series.map(([label, key, color]) => ({
          label, key, data: values(key), borderColor: color, backgroundColor: color,
          borderWidth: 2.5, pointRadius: 4, pointHoverRadius: 6, pointBorderColor: c.surface,
          pointBorderWidth: 2, tension: 0.3, spanGaps: false,
        })),
      },
      options: {
        ...baseOptions(c),
        interaction: { mode: 'index', intersect: false },
        plugins: {
          ...baseOptions(c).plugins,
          tooltip: {
            ...baseOptions(c).plugins.tooltip,
            callbacks: {
              label: (ctx) => {
                if (ctx.parsed.y == null) return `${ctx.dataset.label}: hidden (small group)`;
                return `${ctx.dataset.label}: ${ctx.parsed.y}${mode === 'share' ? '%' : ' comments'}`;
              },
              footer: (items) => `${data.total[items[0].dataIndex]} comments in total`,
            },
          },
        },
        scales: {
          y: { min: 0, grid: { color: c.grid }, border: { display: false },
               ticks: { callback: (v) => (mode === 'share' ? v + '%' : v), precision: 0 } },
          x: { grid: { display: false } },
        },
      },
    });

    const applyMode = () => {
      chart.data.datasets.forEach((ds) => { ds.data = values(ds.key); });
      chart.options.scales.y.max = mode === 'share' ? 100 : undefined;
      chart.update();
    };
    applyMode();

    document.querySelectorAll('[data-chart-toggle="trend"] button').forEach((btn) => {
      btn.addEventListener('click', () => {
        mode = btn.dataset.mode;
        btn.parentElement.querySelectorAll('button').forEach((b) => b.classList.toggle('on', b === btn));
        applyMode();
      });
    });
  }

  function topicChart(c) {
    const data = readJSON('topic-data');
    const el = document.getElementById('topic-chart');
    if (!data || !el || !data.labels.length) return;
    const bar = (label, key, color) => ({
      label, data: data[key], backgroundColor: color, borderColor: c.surface, borderWidth: 1,
      borderRadius: 4, borderSkipped: false, barThickness: 18,
    });
    new Chart(el, {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [bar('Positive', 'positive', c.pos), bar('Negative', 'negative', c.neg), bar('Neutral', 'neutral', c.neu)],
      },
      options: {
        ...baseOptions(c),
        indexAxis: 'y',
        interaction: { mode: 'index', axis: 'y', intersect: false },
        scales: {
          x: { stacked: true, grid: { color: c.grid }, border: { display: false }, ticks: { precision: 0 } },
          y: { stacked: true, grid: { display: false } },
        },
      },
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    const c = palette();
    trendChart(c);
    topicChart(c);
  });
})();

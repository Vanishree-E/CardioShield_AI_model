async function loadCompare() {
  const res = await fetch("/api/compare");
  const data = await res.json();
  const body = document.getElementById("metrics-body");
  body.innerHTML = "";

  const modelNames = Object.keys(data.results);
  modelNames.forEach((name) => {
    const m = data.results[name];
    const isBest = name === data.best_model;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${name}${isBest ? ' <span class="tag low">best</span>' : ""}</td>
      <td>${m.accuracy}</td>
      <td>${m.precision}</td>
      <td>${m.recall}</td>
      <td>${m.f1}</td>
      <td>${m.roc_auc}</td>
    `;
    body.appendChild(tr);
  });

  const ctx = document.getElementById("compare-chart").getContext("2d");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: modelNames,
      datasets: [
        { label: "Accuracy", data: modelNames.map(n => data.results[n].accuracy), backgroundColor: "#3FBFAE" },
        { label: "F1", data: modelNames.map(n => data.results[n].f1), backgroundColor: "#7FC69A" },
        { label: "ROC-AUC", data: modelNames.map(n => data.results[n].roc_auc), backgroundColor: "#E8664E" }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#E9F1EF", font: { family: "IBM Plex Sans" } } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#8FA8A6" } },
        y: { grid: { color: "#2A4347" }, ticks: { color: "#8FA8A6" }, min: 0, max: 1 }
      }
    }
  });
}

loadCompare();

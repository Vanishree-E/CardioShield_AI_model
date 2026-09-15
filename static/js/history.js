async function loadHistory() {
  const res = await fetch("/api/history");
  const rows = await res.json();
  const body = document.getElementById("history-body");
  const empty = document.getElementById("history-empty");
  body.innerHTML = "";

  if (rows.length === 0) {
    empty.style.display = "block";
    document.getElementById("history-table").style.display = "none";
    return;
  }
  empty.style.display = "none";
  document.getElementById("history-table").style.display = "table";

  rows.forEach((r, i) => {
    const tr = document.createElement("tr");
    const isHigh = r.prediction === 1;
    tr.innerHTML = `
      <td>${r.id}</td>
      <td>${r.timestamp}</td>
      <td>${r.age}</td>
      <td>${r.sex === 1 ? "M" : "F"}</td>
      <td>${r.cp}</td>
      <td>${r.chol}</td>
      <td>${r.thalach}</td>
      <td>${r.model_used}</td>
      <td><span class="tag ${isHigh ? "high" : "low"}">${isHigh ? "High risk" : "Low risk"}</span></td>
      <td>${(r.probability * 100).toFixed(1)}%</td>
    `;
    body.appendChild(tr);
  });
}

document.getElementById("clear-btn").addEventListener("click", async () => {
  if (!confirm("Delete all prediction history? This cannot be undone.")) return;
  await fetch("/api/history/clear", { method: "POST" });
  loadHistory();
});

loadHistory();

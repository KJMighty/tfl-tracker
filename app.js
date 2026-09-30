const API_BASE = "http://127.0.0.1:8000";

async function loadStatus() {
  const res = await fetch(`${API_BASE}/status`);
  const lines = await res.json();

  const tbody = document.querySelector("#status-table tbody");
  tbody.innerHTML = "";

  for (const line of lines) {
    const row = document.createElement("tr");
    const statusClass = line.is_good ? "good" : "bad";
    const statusText = line.is_good ? "Good Service" : "Disrupted";

    row.innerHTML = `
      <td>${line.line_name}</td>
      <td class="${statusClass}">${statusText}</td>
      <td>${line.status_description}</td>
    `;
    tbody.appendChild(row);
  }
}

async function loadReliability() {
  const res = await fetch(`${API_BASE}/reliability?days=7`);
  const lines = await res.json();

  const container = document.getElementById("reliability-chart");
  container.innerHTML = "";

  for (const line of lines) {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-label">${line.line_name}</div>
      <div class="bar-track">
        <div class="bar-fill" style="width: ${line.pct_good}%"></div>
      </div>
      <div style="width: 50px; text-align: right;">${line.pct_good}%</div>
    `;
    container.appendChild(row);
  }
}

loadStatus();
loadReliability();
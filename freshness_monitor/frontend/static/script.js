// Get DOM elements
const form = document.getElementById("monitorForm");
const startMonitorBtn = document.getElementById("startMonitorBtn");
const result = document.getElementById("result");
const resultContent = document.getElementById("resultContent");
const stats = document.getElementById("stats");
const totalAssets = document.getElementById("totalAssets");
const freshCount = document.getElementById("freshCount");
const staleCount = document.getElementById("staleCount");
const outdatedCount = document.getElementById("outdatedCount");

// Show result message
function showResult(message, type) {
  resultContent.textContent = message;
  result.className = `result ${type} show`;
}

// Update stats display
function updateStats(data) {
  totalAssets.textContent = data.total_assets || 0;
  freshCount.textContent = data.fresh_assets || 0;
  staleCount.textContent = data.stale_assets || 0;
  outdatedCount.textContent = data.outdated_assets || 0;
  stats.classList.add("show");
}

// Button loading state
function setButtonLoading(isLoading) {
  if (isLoading) {
    startMonitorBtn.classList.add("loading");
    startMonitorBtn.disabled = true;
  } else {
    startMonitorBtn.classList.remove("loading");
    startMonitorBtn.disabled = false;
  }
}

// Handle form submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  setButtonLoading(true);

  const request = {
    threshold_days: parseInt(
      document.getElementById("thresholdDays").value,
      10
    ),
  };

  try {
    const response = await fetch("/workflows/v1/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (data.success) {
      showResult("Monitoring started successfully!", "success");
      if (data.stats) {
        updateStats(data.stats);
      }
    } else {
      showResult(data.error || "Failed to start monitoring", "error");
    }
  } catch (error) {
    showResult(error.message, "error");
  } finally {
    setButtonLoading(false);
  }
});

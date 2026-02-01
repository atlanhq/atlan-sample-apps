window.env = {
  APP_HTTP_HOST: "{{ app_http_host }}",
  APP_HTTP_PORT: "{{ app_http_port }}",
  APP_DASHBOARD_HTTP_HOST: "{{ app_dashboard_http_host }}",
  APP_DASHBOARD_HTTP_PORT: "{{ app_dashboard_http_port }}",
};

// Update WAVE badge based on API key input
document.addEventListener("DOMContentLoaded", function () {
  const waveApiKeyInput = document.getElementById("wave_api_key");
  const waveBadge = document.getElementById("waveBadge");

  waveApiKeyInput.addEventListener("input", function () {
    if (this.value.trim()) {
      waveBadge.textContent = "Enabled";
      waveBadge.classList.add("enabled");
    } else {
      waveBadge.textContent = "Requires API Key";
      waveBadge.classList.remove("enabled");
    }
  });
});

async function handleSubmit(event) {
  event.preventDefault();

  const url = document.getElementById("url").value;
  const wcagLevel = document.getElementById("wcag_level").value;
  const waveApiKey = document.getElementById("wave_api_key").value;

  const resultModal = document.getElementById("successModal");
  const runButton = document.getElementById("runAuditButton");
  const buttonText = runButton.querySelector("span");

  // Disable button and show loading state
  runButton.disabled = true;
  buttonText.textContent = "Starting Audit...";
  runButton.classList.add("loading");

  try {
    const requestBody = {
      url: url,
      wcag_level: wcagLevel,
    };

    // Only include WAVE API key if provided
    if (waveApiKey.trim()) {
      requestBody.wave_api_key = waveApiKey;
    }

    const response = await fetch("/workflows/v1/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    if (response.ok) {
      buttonText.textContent = "Audit Started!";
      runButton.classList.remove("loading");
      runButton.classList.add("success");
      resultModal.classList.add("show");
    } else {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "Failed to start audit");
    }
  } catch (error) {
    console.error("Error starting audit:", error);
    buttonText.textContent = "Try Again";
    runButton.classList.remove("loading");
    runButton.classList.add("error");

    // Show error message
    showError(error.message || "Failed to start the audit. Please try again.");
  } finally {
    // Reset button after delay
    setTimeout(() => {
      runButton.disabled = false;
      buttonText.textContent = "Start Accessibility Audit";
      runButton.classList.remove("success", "error", "loading");
      resultModal.classList.remove("show");
    }, 5000);
  }
}

function showError(message) {
  // Create error toast if it doesn't exist
  let errorToast = document.getElementById("errorToast");
  if (!errorToast) {
    errorToast = document.createElement("div");
    errorToast.id = "errorToast";
    errorToast.className = "error-toast";
    document.body.appendChild(errorToast);
  }

  errorToast.textContent = message;
  errorToast.classList.add("show");

  setTimeout(() => {
    errorToast.classList.remove("show");
  }, 4000);
}

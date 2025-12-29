window.env = {
  APP_HTTP_HOST: "{{ app_http_host }}",
  APP_HTTP_PORT: "{{ app_http_port }}",
  APP_DASHBOARD_HTTP_HOST: "{{ app_dashboard_http_host }}",
  APP_DASHBOARD_HTTP_PORT: "{{ app_dashboard_http_port }}",
};

async function handleSubmit(event) {
  event.preventDefault();
  const resultDiv = document.getElementById("successModal");
  const runButton = document.getElementById("runWorkflowButton");

  runButton.textContent = "Running... 🚀";
  runButton.disabled = true;

  try {
    const response = await fetch("/workflows/v1/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });

    if (response.ok) {
      runButton.textContent = "Success! 🎉";
      resultDiv.classList.add("show");
    } else {
      throw new Error("Workflow start failed");
    }
  } catch (error) {
    runButton.textContent = "Try Again 🔄";
    runButton.classList.add("error");
  } finally {
    setTimeout(() => {
      runButton.disabled = false;
      runButton.textContent = "Run Workflow";
      runButton.classList.remove("error");
      resultDiv.classList.remove("show");
    }, 5000);
  }
}


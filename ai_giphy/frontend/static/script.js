window.env = {
  APP_HTTP_HOST: "{{ app_http_host }}",
  APP_HTTP_PORT: "{{ app_http_port }}"
};

async function handleSubmit(event) {
  event.preventDefault();
  const ai_input_string = document.getElementById("ai_input_string").value;
  const resultDiv = document.getElementById("successModal");
  const runButton = document.getElementById("submitBtn");
  const logMessages = document.getElementById("logMessages");
  const logsContainer = document.getElementById("logsContainer");

  function addLog(message, isError = false) {
    logsContainer.style.display = "block"; // Show logs container
    const logElement = document.createElement('div');
    logElement.className = 'log-message';
    logElement.textContent = message;
    if (isError) logElement.style.color = '#ff4444'; // A common error color
    logMessages.appendChild(logElement);
    logMessages.scrollTop = logMessages.scrollHeight;
  }

  runButton.textContent = "Sending... 🚀";
  runButton.disabled = true;
  logMessages.innerHTML = ""; // Clear previous logs

  try {
    addLog(`Sending request: ${ai_input_string}`);

    // Updated payload and endpoint
    const payload = {
      ai_input_string: ai_input_string,
    };

    const response = await fetch("/workflows/v1/start", { // Changed endpoint
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload) // Simplified payload
    });

    if (response.ok) {
      const result = await response.json(); // Assuming it returns JSON
      addLog("Request successful!");
      addLog(`Response: ${JSON.stringify(result, null, 2)}`);
      runButton.textContent = "Sent! 🎉";
      resultDiv.classList.add("show");
    } else {
      const errorText = await response.text();
      addLog(`Error: ${response.status} ${response.statusText}. ${errorText}`, true);
      throw new Error(`Submission failed: ${response.status} ${errorText}`);
    }
  } catch (error) {
    console.error(error);
    addLog(`Client-side error: ${error.message}`, true);
    runButton.textContent = "Try Again 🔄";
    runButton.classList.add("error"); // Ensure an .error class is defined in CSS for styling
  } finally {
    setTimeout(() => {
      runButton.disabled = false;
      runButton.textContent = "✨ Send Magic ✨";
      runButton.classList.remove("error");
      // Do not hide the modal immediately, let the user see the success/failure.
      // resultDiv.classList.remove("show"); // Removed this line
    }, 5000); // Keep modal visible for 5 seconds
  }
} 
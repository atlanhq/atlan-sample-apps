window.env = {
  APP_HTTP_HOST: "{{ app_http_host }}",
  APP_HTTP_PORT: "{{ app_http_port }}",
  APP_DASHBOARD_HTTP_HOST: "{{ app_dashboard_http_host }}",
  APP_DASHBOARD_HTTP_PORT: "{{ app_dashboard_http_port }}",
};

async function handleSubmit(event) {
  event.preventDefault();
  
  // Collect all form data
  const username = document.getElementById("username").value.trim();
  const city = document.getElementById("city").value.trim();
  const units = document.getElementById("units").value;
  
  // Basic validation
  if (!username) {
    showError("Please enter a username");
    return;
  }
  
  // Prepare request payload
  const payload = {
    username: username
  };
  
  // Only add city and units if they have values (let backend use defaults)
  if (city) {
    payload.city = city;
  }
  if (units && units !== "celsius") { // celsius is default, no need to send
    payload.units = units;
  }
  
  const resultDiv = document.getElementById("successModal");
  const runButton = document.getElementById("runWorkflowButton");

  // Update button state
  runButton.textContent = "Submitting... 🚀";
  runButton.disabled = true;
  runButton.classList.remove("error");

  try {
    const response = await fetch("/workflows/v1/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      runButton.textContent = "Submitted! 🎉";
      resultDiv.classList.add("show");
      
      // Log what was sent for debugging
      console.log("Weather request sent:", payload);
      
      // Show success message
      showSuccess(`Weather request submitted for ${username} in ${city || "London"} (${units})`);
      
      // Clear form after successful submission
      setTimeout(() => {
        clearForm();
      }, 2000);
    } else {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }
  } catch (error) {
    console.error("Error submitting weather request:", error);
    showError(`Failed to submit request: ${error.message}`);
    runButton.textContent = "Try Again 🔄";
    runButton.classList.add("error");
  } finally {
    setTimeout(() => {
      runButton.disabled = false;
      runButton.textContent = "Get Weather 🚀";
      runButton.classList.remove("error");
      resultDiv.classList.remove("show");
    }, 5000);
  }
}

function showSuccess(message) {
  console.log("✅", message);
  // You could add a toast notification here if desired
}

function showError(message) {
  console.error("❌", message);
  // You could add a toast notification here if desired
}

function clearForm() {
  document.getElementById('username').value = '';
  document.getElementById('city').value = '';
  document.getElementById('units').value = 'celsius';
} 
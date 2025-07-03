// Get DOM elements
const form = document.getElementById("reminderForm");
const credentialsStep = document.getElementById("credentialsStep");
const userStep = document.getElementById("userStep");
const nextStepBtn = document.getElementById("nextStepBtn");
const prevStepBtn = document.getElementById("prevStepBtn");
const sendReminderBtn = document.getElementById("sendReminderBtn");
const userSelect = document.getElementById("userSelect");
const result = document.getElementById("result");
const resultContent = document.getElementById("resultContent");
const temporalModal = document.getElementById("temporalModal");

// Show result message
function showResult(message, type) {
  resultContent.textContent = message;
  result.className = `result ${type} show`;
}

// Show modal
function showTemporalModal() {
  temporalModal.classList.add("show");
}

// Close modal when clicking outside
temporalModal.addEventListener("click", (e) => {
  if (e.target === temporalModal) {
    temporalModal.classList.remove("show");
  }
});

// Button loading state handlers
function setButtonLoading(button, isLoading) {
  if (isLoading) {
    button.classList.add("loading");
    button.disabled = true;
  } else {
    button.classList.remove("loading");
    button.disabled = false;
  }
}

// Fetch users
async function fetchUsers() {
  setButtonLoading(nextStepBtn, true);

  const config = {
    base_url: document.getElementById("baseUrl").value,
    atlan_token: document.getElementById("atlanToken").value,
    slack_bot_token: document.getElementById("slackToken").value,
  };

  try {
    const response = await fetch("/api/v1/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });

    const data = await response.json();

    if (data.success && data.users) {
      userSelect.innerHTML =
        '<option value="">Select a user...</option>' +
        data.users
          .map(
            (user) =>
              `<option value="${user.username}">${
                user.displayName || user.username
              }</option>`
          )
          .join("");

      credentialsStep.classList.remove("active");
      userStep.classList.add("active");
      result.classList.remove("show");
    } else {
      throw new Error(data.error || "Failed to fetch users");
    }
  } catch (error) {
    showResult(error.message, "error");
  } finally {
    setButtonLoading(nextStepBtn, false);
  }
}

// Event Listeners
nextStepBtn.addEventListener("click", fetchUsers);

prevStepBtn.addEventListener("click", () => {
  userStep.classList.remove("active");
  credentialsStep.classList.add("active");
  result.classList.remove("show");
});

sendReminderBtn.addEventListener("click", async () => {
  setButtonLoading(sendReminderBtn, true);

  const config = {
    base_url: document.getElementById("baseUrl").value,
    atlan_token: document.getElementById("atlanToken").value,
    slack_bot_token: document.getElementById("slackToken").value,
  };

  const request = {
    config: config,
    user_username: userSelect.value,
    asset_limit: parseInt(
      document.getElementById("assetLimit").value,
      10
    ),
  };

  if (!request.user_username) {
    showResult("Please select a user", "error");
    setButtonLoading(sendReminderBtn, false);
    return;
  }

  try {
    const response = await fetch("/workflows/v1/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    const data = await response.json();
    if (data.success) {
      showResult(
        `Success! ${data.message} (Workflow ID: ${data.data.workflow_id})`,
        "success"
      );
      showTemporalModal();
    } else {
      showResult(data.error || "Failed to send reminder", "error");
    }
  } catch (error) {
    showResult(error.message, "error");
  } finally {
    setButtonLoading(sendReminderBtn, false);
  }
});

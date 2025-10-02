/**
 * Anaplan 3-page wizard: Auth → Connection → Metadata selection
 * Endpoints: /auth, /metadata, /check, /start
 */

// Global state variables
let currentPage = 1;
const formData = {};
let currentAuthType = "basic";

// Legacy: unused form data collector (can be removed)
function updateFormData() {
  const activeSection = document.querySelector(".auth-section.active");
  if (!activeSection) return;

  // Get common inputs from page 1 only
  const commonInputs = document.querySelectorAll(
    "#page1 > .form-group input, #page1 .form-group.horizontal input"
  );
  commonInputs.forEach((input) => {
    if (input.value) {
      formData[input.id] = input.value;
    }
  });

  // Get active authentication section inputs
  const activeInputs = activeSection.querySelectorAll("input");
  activeInputs.forEach((input) => {
    if (input.value) {
      formData[input.id] = input.value;
    }
  });
}

// Updates sidebar step indicators (1,2,3) based on current page
function updateSteps() {
  const steps = document.querySelectorAll(".step");
  steps.forEach((step, index) => {
    const stepNumber = index + 1;
    step.classList.remove("active", "completed");
    if (stepNumber === currentPage) {
      step.classList.add("active");
    } else if (stepNumber < currentPage) {
      step.classList.add("completed");
    }
  });
}

// Core page navigation with validation (auth required for page 2+, connection name for page 3)
function goToPage(pageNumber) {
  // Validate page number
  if (pageNumber < 1 || pageNumber > 3) return;

  // Prevent unauthorized navigation
  if (pageNumber > currentPage) {
    // Check if trying to go past page 1 without authentication
    if (pageNumber > 1 && !sessionStorage.getItem("authenticationComplete")) {
      return;
    }

    // Check if trying to go past page 2
    if (pageNumber > 2) {
      const connectionName = document
        .getElementById("connectionName")
        .value.trim();
      if (!connectionName) {
        return;
      }
    }
  }

  // Hide all pages
  document.querySelectorAll(".page").forEach((page) => {
    page.classList.remove("active");
  });

  // Hide all navigation buttons
  document.querySelectorAll(".nav-buttons").forEach((nav) => {
    nav.style.display = "none";
  });

  // Show selected page
  document.getElementById(`page${pageNumber}`).classList.add("active");

  // Show corresponding navigation buttons
  document.getElementById(`page${pageNumber}-nav`).style.display = "flex";

  // If navigating to page 3, populate metadata dropdowns
  if (pageNumber === 3) {
    populateMetadataDropdowns();
  }

  // Update current page and steps
  currentPage = pageNumber;
  updateSteps();
}

// Handles Next button with validation (auth for page 1, connection name for page 2)
async function nextPage() {
  // If on page 1, ensure authentication is complete
  if (currentPage === 1) {
    if (!sessionStorage.getItem("authenticationComplete")) {
      const success = await testConnection();
      if (!success) {
        return;
      }
    }
    goToPage(2);
    return;
  }

  // For page 2
  if (currentPage === 2) {
    const connectionNameInput = document.getElementById("connectionName");
    const connectionName = connectionNameInput.value.trim();

    if (!connectionName) {
      connectionNameInput.style.border = "2px solid #DC2626";
      connectionNameInput.style.animation = "shake 0.5s";
      connectionNameInput.addEventListener("animationend", () => {
        connectionNameInput.style.animation = "";
      });
      connectionNameInput.addEventListener(
        "input",
        () => {
          connectionNameInput.style.border = "1px solid var(--border-color)";
        },
        { once: true }
      );
      return;
    }

    goToPage(3);
    return;
  }

  // For page 3 (if needed in the future)
  const nextPageNum = currentPage + 1;
  if (nextPageNum <= 3) {
    goToPage(nextPageNum);
  }
}

// Handles Previous button (backward navigation always allowed)
function previousPage() {
  const prevPageNum = currentPage - 1;
  if (prevPageNum >= 1) {
    goToPage(prevPageNum);
  }
}

// Manages UI during connection testing (button states, error messages, auth state)
async function testConnection() {
  const testButton = document.querySelector(".test-connection");
  const errorElement = document.getElementById("connectionError");
  const nextButton = document.getElementById("nextButton");

  try {
    // Disable test button and show loading state
    testButton.disabled = true;
    testButton.textContent = "Testing...";
    errorElement.classList.remove("visible");

    const success = await performConnectionTest();

    if (success) {
      // Success case
      testButton.innerHTML = `Connection Successful <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20" style="margin-left: 8px">
                <path fill-rule="evenodd" d="M8.603 3.799A4.49 4.49 0 0112 2.25c1.357 0 2.573.6 3.397 1.549a4.49 4.49 0 013.498 1.307 4.491 4.491 0 011.307 3.497A4.49 4.49 0 0121.75 12a4.49 4.49 0 01-1.549 3.397 4.491 4.491 0 01-1.307 3.497 4.491 4.491 0 01-3.497 1.307A4.49 4.49 0 0112 21.75a4.49 4.49 0 01-3.397-1.549 4.49 4.49 0 01-3.498-1.306 4.491 4.491 0 01-1.307-3.498A4.49 4.49 0 012.25 12c0-1.357.6-2.573 1.549-3.397a4.49 4.49 0 011.307-3.497 4.49 4.49 0 013.497-1.307zm7.007 6.387a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd" />
            </svg>`;
      testButton.style.backgroundColor = "var(--success-color)";
      testButton.style.color = "white";
      testButton.style.borderColor = "var(--success-color)";
      testButton.classList.add("success");
      nextButton.disabled = false;
      errorElement.classList.remove("visible");

      // Store authentication state
      sessionStorage.setItem("authenticationComplete", "true");
      return true;
    } else {
      throw new Error("Connection failed");
    }
  } catch (error) {
    // Show error message
    errorElement.textContent =
      error.message ||
      "Failed to connect. Please check your credentials and try again.";
    errorElement.classList.add("visible");
    testButton.style.backgroundColor = "";
    testButton.style.color = "";
    testButton.style.borderColor = "";
    testButton.textContent = "Test Connection";
    testButton.classList.remove("success");
    nextButton.disabled = true;
    sessionStorage.removeItem("authenticationComplete");
    return false;
  } finally {
    testButton.disabled = false;
  }
}

// Validates credentials via POST /workflows/v1/auth
async function performConnectionTest() {
  const activeSection = document.querySelector(".auth-section.active");
  if (!activeSection) return false;

  // Get common values
  const host = document.getElementById("host").value;

  let payload = {
    host,
    authType: currentAuthType,
  };

  switch (currentAuthType) {
    case "basic":
      payload.username = document.getElementById("basic-username").value;
      payload.password = document.getElementById("basic-password").value;
      break;
  }

  const response = await fetch(`/workflows/v1/auth`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Connection failed");
  }

  return data.success;
}

// Initialize button states
document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".button-group .btn");
  buttons.forEach((button) => {
    button.addEventListener("click", (e) => {
      const group = e.target.closest(".button-group");
      group.querySelectorAll(".btn").forEach((btn) => {
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-secondary");
      });
      e.target.classList.remove("btn-secondary");
      e.target.classList.add("btn-primary");
    });
  });

  // Update step click handlers
  document.querySelectorAll(".step").forEach((step) => {
    step.addEventListener("click", () => {
      const targetPage = parseInt(step.dataset.step);
      if (targetPage <= currentPage) {
        // Only allow clicking on current or previous steps
        goToPage(targetPage);
      }
    });
  });

  // Clear authentication state on page load
  sessionStorage.removeItem("authenticationComplete");
});


// Global variables for metadata management
let metadataOptions = {
  include: new Map(), // Map<appId, Set<pageId>>
  exclude: new Map(), // Map<appId, Set<pageId>>
};

// Store flat metadata data for UI processing
let flatMetadataData = []; // Array of flat metadata objects from backend

// Fetches available apps/pages from Anaplan via POST /workflows/v1/metadata
async function fetchMetadata() {
  try {
    const activeSection = document.querySelector(".auth-section.active");
    if (!activeSection) return [];

    // Get common values
    const host = document.getElementById("host").value;

    let payload = {
      host,
      authType: currentAuthType,
      type: "all",
    };

    switch (currentAuthType) {
      case "basic":
        payload.username = document.getElementById("basic-username").value;
        payload.password = document.getElementById("basic-password").value;
        break;
    }

    const response = await fetch(`/workflows/v1/metadata`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch metadata");
    }

    const data = await response.json();

    // Store nested data directly for UI processing
    flatMetadataData = data.data || [];
    return flatMetadataData;
  } catch (error) {
    console.error("Error fetching metadata:", error);
    flatMetadataData = [];
    return [];
  }
}

// Toggles dropdown visibility (closes others when opening new one)
function toggleDropdown(id) {
  const dropdown = document.getElementById(id);
  const content = dropdown.querySelector(".dropdown-content");

  // Close all other dropdowns first
  document.querySelectorAll(".dropdown-content").forEach((otherContent) => {
    if (otherContent !== content) {
      otherContent.classList.remove("show");
    }
  });

  // Toggle the clicked dropdown
  content.classList.toggle("show");

  // Prevent the click from bubbling up to the document
  event.stopPropagation();
}

// Updates dropdown header with selection summary (e.g., "Sales App (5 pages) +2 more")
function updateDropdownHeader(type) {
  const dropdown = document.getElementById(`${type}Metadata`);
  const header = dropdown.querySelector(".dropdown-header span");

  // Calculate total selected pages across all apps
  let totalSelectedPages = 0;
  const selectedApps = [];

  metadataOptions[type].forEach((pages, appId) => {
    let appPageCount = pages.size;
    let hasAnySelection = false;

    if (appPageCount > 0) {
      hasAnySelection = true;
    }

    // Show app name if it has any selection (pages or app-level)
    if (hasAnySelection) {
      const appData = flatMetadataData.find(item => item.value === appId);
      const appName = appData?.title || appId;
      selectedApps.push(`${appName} (${appPageCount} pages)`);
      totalSelectedPages += appPageCount;
    }
  });

  if (selectedApps.length === 0) {
    header.textContent = "Select apps and pages";
  } else if (selectedApps.length === 1) {
    header.textContent = selectedApps[0];
  } else {
    // Show first app and count of others
    header.textContent = `${selectedApps[0]} +${selectedApps.length - 1} more`;
  }

  // Add tooltip for full list when multiple apps are selected
  if (selectedApps.length > 1) {
    header.title = selectedApps.join("\n");
  } else {
    header.title = "";
  }
}

// Loads and populates both Include/Exclude dropdowns with metadata
async function populateMetadataDropdowns() {
  // Show loading state for both dropdowns
  ["include", "exclude"].forEach((type) => {
    const dropdown = document.getElementById(`${type}Metadata`);
    const header = dropdown.querySelector(".dropdown-header span");
    const content = dropdown.querySelector(".dropdown-content");
    header.textContent = "Loading...";
    content.innerHTML = ""; // Clear existing content
  });

  // Clear existing selections
  metadataOptions.include.clear();
  metadataOptions.exclude.clear();

  // Make single API call
  const data = await fetchMetadata();

  // Populate both dropdowns with the same data
  ["include", "exclude"].forEach((type) => {
    populateDropdown(type, data);
  });
}

// Creates 2-level checkbox hierarchy (app → page) for metadata selection
function populateDropdown(type, data) {
  const dropdown = document.getElementById(`${type}Metadata`);
  const content = dropdown.querySelector(".dropdown-content");
  const header = dropdown.querySelector(".dropdown-header span");

  // Reset content
  content.innerHTML = "";

  // Update header text based on whether we got data
  if (data.length === 0) {
    header.textContent = "No apps available";
    return;
  }

  // Reset to default text
  header.textContent = "Select apps and pages";

  // Sort apps by name
  const sortedApps = data.sort((a, b) => a.title.localeCompare(b.title));

  sortedApps.forEach(app => {
    const appName = app.title;
    const appId = app.value;

    // Create app container
    const appContainer = document.createElement("div");
    appContainer.className = "database-container";

    // Create app header
    const appDiv = document.createElement("div");
    appDiv.className = "database-item";

    const appCheckbox = document.createElement("input");
    appCheckbox.type = "checkbox";
    appCheckbox.id = `${type}-app-${appId}`;

    const appLabel = document.createElement("label");
    appLabel.textContent = appName;
    appLabel.htmlFor = `${type}-app-${appId}`;

    // Calculate total pages count for this app
    let totalPagesCount = app.children.length;

    const appCount = document.createElement("span");
    appCount.className = "selected-count";
    appCount.textContent = `0/${totalPagesCount}`;

    appDiv.appendChild(appCheckbox);
    appDiv.appendChild(appLabel);
    appDiv.appendChild(appCount);

    // Create pages list
    const pagesList = document.createElement("div");
    pagesList.className = "schema-list";
    pagesList.style.display = "none"; // Start collapsed
    pagesList.style.paddingLeft = "1.5rem"; // Add indentation for pages

    // Sort pages by name
    const sortedPages = app.children.sort((a, b) => a.title.localeCompare(b.title));

    sortedPages.forEach(page => {
      const pageName = page.title;
      const pageId = page.value;

      const pageDiv = document.createElement("div");
      pageDiv.className = "schema-item";

      const pageCheckbox = document.createElement("input");
      pageCheckbox.type = "checkbox";
      pageCheckbox.id = `${type}-page-${pageId}`;

      const pageLabel = document.createElement("label");
      pageLabel.textContent = pageName;
      pageLabel.htmlFor = `${type}-page-${pageId}`;

      pageDiv.appendChild(pageCheckbox);
      pageDiv.appendChild(pageLabel);
      pagesList.appendChild(pageDiv);

      // Page checkbox event listener
      pageCheckbox.addEventListener("change", (e) => {
        handlePageSelection(type, appId, pageId, e.target.checked);
        updateSelectionCounts(type, appId);
      });
    });

    // App checkbox event listener
    appCheckbox.addEventListener("change", (e) => {
      const allPages = app.children;
      handleAppSelection(type, appId, allPages, e.target.checked);
      pagesList.querySelectorAll('input[type="checkbox"]').forEach((cb) => (cb.checked = e.target.checked));
      updateSelectionCounts(type, appId);
    });

    // Click to toggle pages list
    appDiv.addEventListener("click", (e) => {
      if (e.target.type !== "checkbox") {
        const isVisible = pagesList.style.display !== "none";
        pagesList.style.display = isVisible ? "none" : "block";

        // Add visual indicator for expanded state
        if (isVisible) {
          appDiv.classList.remove("expanded");
        } else {
          appDiv.classList.add("expanded");
        }
      }
    });

    appContainer.appendChild(appDiv);
    appContainer.appendChild(pagesList);
    content.appendChild(appContainer);
  });
}

// Handles app-level selection (selects/deselects all pages in app)
function handleAppSelection(type, appId, pages, isSelected) {
  if (isSelected) {
    // Create app entry if it doesn't exist
    if (!metadataOptions[type].has(appId)) {
      metadataOptions[type].set(appId, new Set());
    }

    const appPages = metadataOptions[type].get(appId);

    // Add all pages for this app
    pages.forEach((page) => {
      appPages.add(page.value);
    });
  } else {
    // Remove entire app from selections
    metadataOptions[type].delete(appId);
  }

  // Update checkbox states to reflect the actual selection state
  updateCheckboxStates(type, appId);
  updateDropdownHeader(type);
}

// Handles individual page selection (granular control)
function handlePageSelection(type, appId, pageId, isSelected) {
  if (isSelected) {
    // Create app entry if it doesn't exist
    if (!metadataOptions[type].has(appId)) {
      metadataOptions[type].set(appId, new Set());
    }

    const appPages = metadataOptions[type].get(appId);

    // Add the page
    appPages.add(pageId);
  } else {
    // Remove page from selections
    if (metadataOptions[type].has(appId)) {
      const appPages = metadataOptions[type].get(appId);
      appPages.delete(pageId);

      // If app has no more pages, remove it too
      if (appPages.size === 0) {
        metadataOptions[type].delete(appId);
      }
    }
  }

  // Update checkbox states to reflect the actual selection state
  updateCheckboxStates(type, appId);
  updateDropdownHeader(type);
}



// Syncs checkbox states with actual selection data
function updateCheckboxStates(type, appId) {
  const appPages = metadataOptions[type].get(appId);

  // Update app checkbox
  const appCheckbox = document.getElementById(`${type}-app-${appId}`);
  if (appCheckbox) {
    appCheckbox.checked = appPages && appPages.size > 0;
  }

  // Update all page checkboxes for this app
  if (appPages) {
    // Get all page checkboxes for this app
    const pageCheckboxes = document.querySelectorAll(`input[id^="${type}-page-"]`);
    pageCheckboxes.forEach(checkbox => {
      const pageId = checkbox.id.replace(`${type}-page-`, '');
      // Check if this page belongs to the current app by finding it in the nested structure
      const appData = flatMetadataData.find(item => item.value === appId);
      if (appData && appData.children.some(page => page.value === pageId)) {
        checkbox.checked = appPages.has(pageId);
      }
    });
  }
}

// Updates "X/Y selected" counters next to app names
function updateSelectionCounts(type, appId) {
  const appPages = metadataOptions[type].get(appId);
  if (!appPages) return;

  // Get original app data for counting from nested data
  const appData = flatMetadataData.find(item => item.value === appId);
  if (!appData) return;

  // Update app count
  let totalSelectedPages = appPages.size;
  let totalAvailablePages = appData.children.length;

  const appCountSpan = document.querySelector(`#${type}-app-${appId}`).parentElement.querySelector('.selected-count');
  if (appCountSpan) {
    appCountSpan.textContent = `${totalSelectedPages}/${totalAvailablePages}`;
  }

  updateDropdownHeader(type);
}

// Converts UI selections to backend JSON format: {"include-metadata": "{\"app_id\":{\"page_id\":{}}}"}
function formatFilters(metadataOptions) {
  const formatFilter = (selections) => {
    const filter = {};

    selections.forEach((pages, appId) => {
      filter[appId] = {};
      pages.forEach((pageId) => {
        filter[appId][pageId] = {};
      });
    });

    return JSON.stringify(filter);
  };

  return {
    "include-metadata": formatFilter(metadataOptions.include),
    "exclude-metadata": formatFilter(metadataOptions.exclude),
  };
}



// Validates config before workflow execution via POST /workflows/v1/check
async function runPreflightChecks() {
  const checkButton = document.getElementById("runPreflightChecks");
  checkButton.disabled = true;
  checkButton.textContent = "Checking...";

  // Get or create the results container
  let resultsContainer = document.querySelector(".preflight-content");
  if (!resultsContainer) {
    resultsContainer = document.createElement("div");
    resultsContainer.className = "preflight-content";
    // Insert after the header section
    const preflightSection = document.querySelector(".preflight-section");
    preflightSection.appendChild(resultsContainer);
  }

  // Clear previous results
  resultsContainer.innerHTML = "";

  try {
    const activeSection = document.querySelector(".auth-section.active");
    if (!activeSection) return false;

    // Get common values
    const host = document.getElementById("host").value;

    let credentials = {
      host,
      authType: currentAuthType,
    };

    switch (currentAuthType) {
      case "basic":
        credentials.username = document.getElementById("basic-username").value;
        credentials.password = document.getElementById("basic-password").value;
        break;
    }

    const payload = {
      credentials,
      metadata: {
        ...formatFilters(metadataOptions),
      },
    };

    const response = await fetch(`/workflows/v1/check`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const responseJson = await response.json();

    // Create and append check results in sequence
    Object.entries(responseJson.data).forEach(([checkType, result]) => {
      const resultDiv = document.createElement("div");
      resultDiv.className = "check-result";

      const statusElement = document.createElement("div");
      statusElement.className = "check-status";

      if (result.success) {
        statusElement.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                        <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd" />
                    </svg>
                    <span>${result.successMessage}</span>
                `;
        statusElement.classList.add("success");
      } else {
        statusElement.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                        <path fill-rule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm-1.72 6.97a.75.75 0 10-1.06 1.06L10.94 12l-1.72 1.72a.75.75 0 101.06 1.06L12 13.06l1.72 1.72a.75.75 0 101.06-1.06L13.06 12l1.72-1.72a.75.75 0 10-1.06-1.06L12 10.94l-1.72-1.72z" clip-rule="evenodd" />
                    </svg>
                    <span>${result.failureMessage || "Check failed"}</span>
                `;
        statusElement.classList.add("error");
      }

      resultDiv.appendChild(statusElement);
      resultsContainer.appendChild(resultDiv);
    });
  } catch (error) {
    console.error("Preflight check failed:", error);
    const errorDiv = document.createElement("div");
    errorDiv.className = "check-status error";
    errorDiv.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path fill-rule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm-1.72 6.97a.75.75 0 10-1.06 1.06L10.94 12l-1.72 1.72a.75.75 0 101.06 1.06L12 13.06l1.72 1.72a.75.75 0 101.06-1.06L13.06 12l1.72-1.72a.75.75 0 10-1.06-1.06L12 10.94l-1.72-1.72z" clip-rule="evenodd" />
            </svg>
            <span>Failed to perform check</span>
        `;
    resultsContainer.appendChild(errorDiv);
  } finally {
    checkButton.disabled = false;
    checkButton.textContent = "Check";
  }
}

// Sets up preflight check button event listener
function setupPreflightCheck() {
  const checkButton = document.getElementById("runPreflightChecks");
  if (checkButton) {
    checkButton.addEventListener("click", async () => {
      await runPreflightChecks();
    });
  }
}

// Update your DOMContentLoaded listener
document.addEventListener("DOMContentLoaded", () => {
  setupPreflightCheck();
});



// Starts Anaplan data extraction workflow via POST /workflows/v1/start
async function handleRunWorkflow() {
  const runButton = document.querySelector("#runWorkflowButton");
  if (!runButton) return;
  const modal = document.getElementById("successModal");

  runButton.addEventListener("click", async () => {
    try {
      const activeSection = document.querySelector(".auth-section.active");
      if (!activeSection) return false;

      // Get common values
      const host = document.getElementById("host").value;

      let credentials = {
        host,
        authType: currentAuthType,
      };

      switch (currentAuthType) {
        case "basic":
          credentials.username = document.getElementById("basic-username").value;
          credentials.password = document.getElementById("basic-password").value;
          break;
      }

      runButton.disabled = true;
      runButton.textContent = "Starting...";

      const connectionName = document.getElementById("connectionName").value;
      const tenantId = window.env.TENANT_ID || "default";
      const appName = window.env.APP_NAME || "anaplan";
      //get epoch in milliseconds
      const currentEpoch = Math.floor(Date.now() / 1000);
      const connection = {
        connection_name: connectionName,
        connection_qualified_name: `${tenantId}/${appName}/${currentEpoch}`,
      };

      // Get metadata filters from page 3
      const filters = formatFilters(metadataOptions);

      const payload = {
        credentials,
        connection,
        metadata: {
          ...filters,
        },
      };

      const response = await fetch(`/workflows/v1/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      // Check for both HTTP errors and application errors
      if (!response.ok || !data.success) {
        const errorMessage = data.message || data.error || "Failed to start workflow";
        throw new Error(errorMessage);
      }

      // Show success state only if we actually succeeded
      runButton.textContent = "Started Successfully";
      runButton.classList.add("success");

      // Show modal
      modal.classList.add("show");
    } catch (error) {
      console.error("Failed to start workflow:", error);
      runButton.textContent = "Failed to Start";
      runButton.classList.add("error");

      const errorMessage = document.querySelector(".error-message");
      if (errorMessage) {
        errorMessage.textContent =
          "Failed to start workflow. Please try again.";
        errorMessage.classList.add("visible");
      }
    } finally {
      setTimeout(() => {
        runButton.disabled = false;
        runButton.textContent = "Run";
        runButton.classList.remove("success", "error");
        modal.classList.remove("show");
      }, 3000);
    }
  });
}

// Add to your DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", () => {
  handleRunWorkflow();
});

// Closes dropdowns when clicking outside them
function setupDropdownClickOutside() {
  document.addEventListener("click", (event) => {
    const dropdowns = document.querySelectorAll(".metadata-dropdown");
    dropdowns.forEach((dropdown) => {
      const content = dropdown.querySelector(".dropdown-content");
      // Check if click is outside the dropdown
      if (!dropdown.contains(event.target)) {
        content.classList.remove("show");
      }
    });
  });
}

// Add this to your DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", () => {
  setupDropdownClickOutside();
});

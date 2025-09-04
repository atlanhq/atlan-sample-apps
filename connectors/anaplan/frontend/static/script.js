/**
 * ANAPLAN APP FRONTEND CONTROLLER
 *
 * This file manages the 3-page wizard interface for configuring Anaplan data extraction:
 * Page 1: Authentication (host + basic auth credentials)
 * Page 2: Connection naming
 * Page 3: Metadata selection (2-level filter: app → page) + configuration
 *
 * MAIN ENDPOINTS USED:
 * - POST /workflows/v1/auth      - Validate credentials
 * - POST /workflows/v1/metadata  - Get available apps/pages for filters
 * - POST /workflows/v1/check     - Run preflight validation
 * - POST /workflows/v1/start     - Start extraction workflow
 *
 * KEY DATA STRUCTURES:
 * - metadataOptions: Map<appId, Set<pageId>> for include/exclude
 * - flatMetadataData: Array of nested metadata objects from backend
 *
 * WORKFLOW:
 * 1. User enters credentials → Test Connection → Authentication validated
 * 2. User enters connection name → Navigate to metadata page
 * 3. System fetches available metadata → User selects include/exclude
 * 4. User runs preflight checks → Validates configuration
 * 5. User starts workflow → Begins data extraction
 */

// Global state variables
let currentPage = 1;
const formData = {};
let currentAuthType = "basic";

/**
 * LEGACY FUNCTION - Currently unused, leftover from earlier versions
 * PURPOSE: Collects and stores form input values in a global formData object
 * INPUTS: None (reads from DOM elements)
 * DOM INTERACTIONS: Reads from active auth section and page 1 form inputs
 * ENDPOINTS: None
 * OUTPUTS: Updates global formData object
 * WHY IT EXISTS: Originally for form state persistence, but now redundant
 * STATUS: Can be removed in cleanup
 */
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

/**
 * VISUAL PROGRESS INDICATOR UPDATER
 * PURPOSE: Updates the sidebar step indicators (1,2,3) based on current page
 * INPUTS: Uses global currentPage variable
 * DOM INTERACTIONS: Adds/removes CSS classes (.active, .completed) on .step elements
 * ENDPOINTS: None
 * OUTPUTS: Visual feedback - blue circles with numbers, completed steps show filled circles
 * WHY IT EXISTS: Users need visual feedback of their progress through the 3-page wizard
 * CALLED BY: goToPage() function whenever page changes
 */
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

/**
 * MAIN NAVIGATION CONTROLLER - Core page switching logic
 * PURPOSE: Safely navigate between the 3 pages with validation checks
 * INPUTS: pageNumber (1, 2, or 3)
 * VALIDATION:
 *   - Page 1 → 2: Requires authentication completion
 *   - Page 2 → 3: Requires connection name to be filled
 * DOM INTERACTIONS:
 *   - Hides all pages, shows target page
 *   - Manages navigation button visibility
 *   - Triggers metadata loading on page 3
 * ENDPOINTS: None directly, but triggers fetchMetadata() on page 3
 * OUTPUTS: Page visibility changes, calls populateMetadataDropdowns()
 * WHY IT EXISTS: Prevents users from skipping required steps, maintains wizard flow
 * SECURITY: Prevents unauthorized navigation past authentication
 */
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

/**
 * NAVIGATION BUTTON HANDLER - Forward navigation with validation
 * PURPOSE: Handle Next button clicks with validation
 * INPUTS: None (reads current page state)
 * VALIDATION:
 *   - Page 1: Enforces authentication completion
 *   - Page 2: Requires connection name to be filled
 * DOM INTERACTIONS: Connection name input styling for errors
 * ENDPOINTS: None directly, but may trigger testConnection()
 * OUTPUTS: Calls goToPage() or shows validation errors
 * WHY IT EXISTS: User-friendly navigation with guided workflow enforcement
 */
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

/**
 * NAVIGATION BUTTON HANDLER - Backward navigation
 * PURPOSE: Handle Previous button clicks
 * INPUTS: None (reads current page state)
 * VALIDATION: None (backward navigation is always allowed)
 * DOM INTERACTIONS: None
 * ENDPOINTS: None
 * OUTPUTS: Calls goToPage() with previous page number
 * WHY IT EXISTS: Simple backward navigation through wizard
 */
function previousPage() {
  const prevPageNum = currentPage - 1;
  if (prevPageNum >= 1) {
    goToPage(prevPageNum);
  }
}

/**
 * USER-FACING CONNECTION TEST ORCHESTRATOR
 * PURPOSE: Manages UI state during connection testing and handles results
 * INPUTS: None (triggered by button click)
 * DOM INTERACTIONS:
 *   - Updates test button text/styling ("Testing..." → "Connection Successful")
 *   - Shows/hides error messages
 *   - Enables/disables Next button based on result
 * ENDPOINTS: None directly, delegates to performConnectionTest()
 * OUTPUTS:
 *   - Visual feedback (green success button with checkmark)
 *   - Error messages if connection fails
 *   - Updates sessionStorage authentication state
 * WHY IT EXISTS: Provides user feedback and prevents progression without valid credentials
 * FLOW: User clicks "Test Connection" → UI feedback → Backend validation → Result display
 */
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

/**
 * BACKEND CONNECTION VALIDATOR
 * PURPOSE: Sends credentials to backend for authentication validation
 * INPUTS: Reads from basic-username, basic-password, host inputs
 * ENDPOINTS: POST /workflows/v1/auth
 * PAYLOAD STRUCTURE:
 *   {
 *     host: "us1a.app.anaplan.com",
 *     authType: "basic",
 *     username: "username",
 *     password: "password123"
 *   }
 * OUTPUTS: Boolean (true/false) indicating connection success
 * ERROR HANDLING: Throws error with backend message on failure
 * WHY IT EXISTS: Validates user credentials before allowing metadata discovery
 * CURRENT STATUS: Has temporary bypass (return true) for development
 */
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

/**
 * ANAPLAN METADATA DISCOVERY
 * PURPOSE: Retrieves available apps and pages from Anaplan
 * ENDPOINTS: POST /workflows/v1/metadata
 * PAYLOAD STRUCTURE:
 *   {
 *     host: "<host>",
 *     authType: "basic",
 *     type: "all",
 *     username: "<username>",
 *     password: "<password>"
 *   }
 * EXPECTED RESPONSE (Nested Format):
 *   SUCCESS: {
 *     success: true,
 *     data: [
 *       {
 *         value: "app_id",
 *         title: "Sales App",
 *         children: [
 *           {
 *             value: "page_id",
 *             title: "Revenue Page",
 *             children: []
 *           }
 *         ]
 *       }
 *     ]
 *   }
 *   ERROR: {
 *     success: false,
 *     message: "Error description"
 *   }
 * WHY IT EXISTS: Users need to see available Anaplan content to select for extraction
 * CALLED BY: populateMetadataDropdowns() when user reaches page 3
 */
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

/**
 * DROPDOWN VISIBILITY CONTROLLER
 * PURPOSE: Opens/closes metadata dropdown menus
 * INPUTS: id of dropdown to toggle
 * DOM INTERACTIONS: Adds/removes .show class on dropdown content
 * BEHAVIOR: Closes other dropdowns when opening a new one
 * WHY IT EXISTS: Standard dropdown UI behavior - only one open at a time
 * CALLED BY: Click events on dropdown headers
 */
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

/**
 * DROPDOWN HEADER TEXT MANAGER
 * PURPOSE: Updates the main dropdown header to show current selection summary
 * INPUTS: type ("include" or "exclude")
 * PROCESSING:
 *   - Counts total selected pages across all apps
 *   - Creates summary text (e.g., "Sales App (5 pages)" or "Sales App +2 more")
 * OUTPUTS: Updates dropdown header text and tooltip
 * WHY IT EXISTS: Users need to see selection summary without opening dropdown
 * DISPLAY LOGIC:
 *   - No selections: "Select apps and pages"
 *   - One app: "Sales App (5 pages)"
 *   - Multiple: "Sales App (5 pages) +2 more"
 */
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

/**
 * DROPDOWN INITIALIZATION COORDINATOR
 * PURPOSE: Orchestrates the loading and population of both Include/Exclude dropdowns
 * INPUTS: None (called when user reaches page 3)
 * PROCESS:
 *   1. Shows "Loading..." state in both dropdowns
 *   2. Clears previous selections
 *   3. Calls fetchMetadata() to get fresh data
 *   4. Calls populateDropdown() for each dropdown type
 * ENDPOINTS: Indirectly calls POST /workflows/v1/metadata via fetchMetadata()
 * OUTPUTS: Populated dropdown menus with 2-level checkboxes
 * WHY IT EXISTS: Single entry point for metadata loading, handles loading states
 * CALLED BY: goToPage(3) when user navigates to metadata selection page
 */
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

/**
 * 2-LEVEL DROPDOWN UI BUILDER
 * PURPOSE: Creates interactive checkbox hierarchy for app→page selection
 * INPUTS:
 *   - type: "include" or "exclude"
 *   - data: Array of nested metadata objects from backend
 * DOM CREATION:
 *   - App level: checkbox + name + count
 *   - Page level: checkbox + name (collapsible)
 * EVENT LISTENERS: Adds click handlers for all checkboxes and expand/collapse
 * OUTPUTS: Complete interactive dropdown with nested checkboxes
 * WHY IT EXISTS: Users need granular control over what metadata to include/exclude
 * UI PATTERN: Hierarchical selection with parent/child checkbox relationships
 */
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

/**
 * APP-LEVEL SELECTION HANDLER
 * PURPOSE: Manages selection of entire app (all pages within)
 * INPUTS:
 *   - type: "include" or "exclude"
 *   - appId: Unique app identifier
 *   - pages: Array of page objects within this app
 *   - isSelected: Boolean indicating if app is being selected/deselected
 * PROCESSING: Updates metadataOptions Map structure for all pages in app
 * OUTPUTS: Updates global metadataOptions, triggers dropdown header update
 * WHY IT EXISTS: Bulk selection - users often want entire apps, not individual pages
 * CALLED BY: App checkbox change events
 */
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

/**
 * PAGE-LEVEL SELECTION HANDLER
 * PURPOSE: Manages selection of individual pages (finest granularity)
 * INPUTS:
 *   - type: "include" or "exclude"
 *   - appId, pageId: Full path identifiers
 *   - isSelected: Boolean for selection state
 * PROCESSING: Updates metadataOptions Set for the specific page
 * OUTPUTS: Updates global metadataOptions, triggers dropdown header update
 * WHY IT EXISTS: Granular control - users sometimes need specific pages only
 * CALLED BY: Page checkbox change events
 */
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



/**
 * CHECKBOX STATE UPDATER
 * PURPOSE: Updates checkbox states to reflect the actual selection state in metadataOptions
 * INPUTS: type ("include"/"exclude"), appId
 * DOM INTERACTIONS: Updates checkbox checked states based on actual selections
 * PROCESSING: Compares checkbox states with metadataOptions to ensure consistency
 * OUTPUTS: Synchronized checkbox states that match the actual selection data
 * WHY IT EXISTS: Ensures UI reflects the actual selection state when items are deselected
 * CALLED BY: All selection handler functions after updating metadataOptions
 */
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

/**
 * SELECTION COUNTER UPDATER
 * PURPOSE: Updates the "X/Y selected" counts displayed next to app names
 * INPUTS: type ("include"/"exclude"), appId to update
 * DOM INTERACTIONS: Updates .selected-count spans with current selection numbers
 * PROCESSING: Calculates selected vs. available counts for app
 * OUTPUTS: Visual feedback showing "5/12 pages" type counters
 * WHY IT EXISTS: Users need to see selection progress and make informed decisions
 * CALLED BY: All selection handler functions after updating metadataOptions
 */
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

/**
 * BACKEND PAYLOAD FORMATTER
 * PURPOSE: Converts UI selections into backend-compatible JSON filter format
 * INPUTS: Global metadataOptions Map structure
 * PROCESSING: Transforms Map<app<page>> into nested JSON objects
 * OUTPUT FORMAT:
 *   {
 *     "include-metadata": "{\"app_id\":{\"page_id\":{}}}",
 *     "exclude-metadata": "{\"app_id2\":{\"page_id2\":{}}}"
 *   }
 * WHY IT EXISTS: Backend expects specific JSON string format with IDs, not names
 * CALLED BY: runPreflightChecks() and handleRunWorkflow() before sending to backend
 * NOTE: Uses IDs (not names) and empty objects as values (not regex patterns)
 *
 * ENDPOINTS THAT USE THIS FORMAT:
 *   - POST /workflows/v1/check (preflight validation)
 *   - POST /workflows/v1/start (workflow execution)
 */
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



/**
 * PRE-EXECUTION VALIDATION RUNNER
 * PURPOSE: Validates configuration before running expensive full workflow
 * INPUTS: Form credentials + metadata selections + Anaplan config
 * PAYLOAD STRUCTURE:
 *   {
 *     credentials: { host, authType, username, password },
 *     metadata: {
 *       "include-metadata": "{...JSON...}",
 *       "exclude-metadata": "{...JSON...}",
 *       "exclude-empty-modules": "true",
 *       "ingest-system-dimension": "proxy"
 *     }
 *   }
 * ENDPOINTS: POST /workflows/v1/check
 * EXPECTED RESPONSE:
 *   SUCCESS: {
 *     success: true,
 *     data: {
 *       authenticationCheck: {success: true, successMessage: "..."},
 *       connectivityCheck: {success: true, successMessage: "..."},
 *       permissionsCheck: {success: true, successMessage: "..."}
 *     }
 *   }
 *   ERROR: {
 *     success: false,
 *     message: "Error description"
 *   }
 * OUTPUTS: Green/red status indicators with success/failure messages
 * WHY IT EXISTS: Catch configuration issues before expensive full extraction
 * UI FEEDBACK: Creates dynamic status boxes with checkmarks or X marks
 */
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

/**
 * EVENT LISTENER SETUP - Preflight Check Button
 * PURPOSE: Connects the "Check" button to runPreflightChecks function
 * INPUTS: None
 * DOM INTERACTIONS: Adds click listener to #runPreflightChecks button
 * OUTPUTS: None (sets up event listener)
 * WHY IT EXISTS: Separation of concerns - setup vs. execution logic
 * CALLED BY: DOMContentLoaded event listener
 */
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



/**
 * MAIN WORKFLOW EXECUTOR
 * PURPOSE: Starts the actual Anaplan data extraction workflow
 * INPUTS: All form data (credentials + metadata + config + connection info)
 * PAYLOAD STRUCTURE:
 *   {
 *     credentials: { host, authType, username, password },
 *     connection: {
 *       connection_name: "user-provided-name",
 *       connection_qualified_name: "tenant/anaplan/timestamp"
 *     },
 *     metadata: { ...formatFilters + ...getAnaplanConfig }
 *   }
 * ENDPOINTS: POST /workflows/v1/start
 * EXPECTED RESPONSE:
 *   SUCCESS: {
 *     success: true,
 *     data: {
 *       workflow_id: "workflow-identifier",
 *       status: "started",
 *       message: "Workflow started successfully"
 *     }
 *   }
 *   ERROR: {
 *     success: false,
 *     message: "Error description"
 *   }
 * OUTPUTS:
 *   - Success: Shows modal with link to Temporal UI for monitoring
 *   - Failure: Shows error message
 * WHY IT EXISTS: Triggers the actual data extraction process
 * UI FEEDBACK: Button states (Starting... → Started Successfully), success modal
 */
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

/**
 * EVENT LISTENER SETUP - Click Outside Dropdown Handler
 * PURPOSE: Closes dropdowns when user clicks outside them
 * INPUTS: None
 * DOM INTERACTIONS: Adds global click listener, closes .dropdown-content with .show class
 * BEHAVIOR: Standard dropdown UX - clicking outside closes dropdown
 * WHY IT EXISTS: Provides expected dropdown behavior for better user experience
 * CALLED BY: DOMContentLoaded event listener
 */
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

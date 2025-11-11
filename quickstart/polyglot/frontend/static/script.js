// Polyglot Demo - Frontend JavaScript

// Use relative URL to avoid CORS issues - will use the same origin as the page
const API_BASE_URL = '';

// DOM Elements
const calculateBtn = document.getElementById('calculate-btn');
const numberInput = document.getElementById('number-input');

// Event Listeners
calculateBtn.addEventListener('click', calculateFactorial);

// Allow Enter key to trigger calculation
numberInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') calculateFactorial();
});

/**
 * Calculate factorial
 */
async function calculateFactorial() {
    const number = parseInt(numberInput.value);

    if (isNaN(number) || number < 0 || number > 20) {
        displayError('Please enter a valid number between 0 and 20');
        return;
    }

    setButtonLoading(calculateBtn, true);

    try {
        // Start the workflow
        // Note: Don't send workflow_id - let the SDK generate it and save to state store
        const startResponse = await fetch(`${API_BASE_URL}/workflows/v1/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                number: number
            })
        });

        if (!startResponse.ok) {
            throw new Error(`Failed to start workflow: ${startResponse.statusText}`);
        }

        const startData = await startResponse.json();
        console.log('Workflow started:', startData);

        // Get the workflow_id from the response
        const workflowId = startData.data?.workflow_id;
        if (!workflowId) {
            throw new Error('No workflow_id returned from server');
        }

        // Show success popup
        showSuccessPopup(number, workflowId);

    } catch (error) {
        console.error('Error calculating factorial:', error);
        showErrorPopup(error.message);
    } finally {
        setButtonLoading(calculateBtn, false);
    }
}

/**
 * Show success popup after workflow starts
 */
function showSuccessPopup(number, workflowId) {
    alert(`✅ Workflow Started Successfully!\n\nCalculating factorial of ${number}\n\nWorkflow ID: ${workflowId}\n\nThe calculation is running in the background.\nResult will be saved to: /tmp/polyglot/results/factorial_result/`);
}

/**
 * Show error popup
 */
function showErrorPopup(message) {
    alert(`❌ Error\n\n${message}`);
}

/**
 * Display error message for validation
 */
function displayError(message) {
    alert(`❌ ${message}`);
}

/**
 * Set button loading state
 */
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = '<span class="loading"></span> Processing...';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText;
    }
}

// Initialize
window.addEventListener('load', () => {
    console.log('Polyglot Demo loaded');
});

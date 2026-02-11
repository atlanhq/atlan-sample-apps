let currentPage = 1;

function getBaseUrl() {
    return `http://${window.env.APP_HTTP_HOST}:${window.env.APP_HTTP_PORT}`;
}

function getCredentials() {
    return {
        host: document.getElementById('host').value,
        port: parseInt(document.getElementById('port').value) || 8080,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        http_scheme: document.getElementById('httpScheme').value,
        role: document.getElementById('role').value,
        catalog: document.getElementById('catalog') ? document.getElementById('catalog').value : 'system',
    };
}

function goToPage(pageNumber) {
    if (pageNumber < 1 || pageNumber > 3) return;

    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    document.getElementById(`page${pageNumber}`).style.display = 'block';

    // Update sidebar steps
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 === pageNumber) {
            step.classList.add('active');
        } else if (index + 1 < pageNumber) {
            step.classList.add('completed');
        }
    });

    currentPage = pageNumber;
}

async function testAuth() {
    const btn = document.getElementById('testAuthBtn');
    const resultDiv = document.getElementById('authResult');
    btn.disabled = true;
    btn.textContent = 'Testing...';
    resultDiv.style.display = 'block';
    resultDiv.textContent = 'Testing authentication against REST API and SQL...';

    try {
        const response = await fetch(`${getBaseUrl()}/workflows/v1/test_auth`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credentials: getCredentials() }),
        });
        const data = await response.json();

        if (data.success) {
            resultDiv.className = 'result-box success';
            resultDiv.textContent = 'Authentication successful for both REST API and SQL.';
        } else {
            resultDiv.className = 'result-box error';
            resultDiv.textContent = `Authentication failed: ${JSON.stringify(data.data)}`;
        }
    } catch (error) {
        resultDiv.className = 'result-box error';
        resultDiv.textContent = `Error: ${error.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Test Authentication';
    }
}

async function fetchMetadata() {
    const btn = document.getElementById('fetchMetaBtn');
    const resultDiv = document.getElementById('metadataResult');
    btn.disabled = true;
    btn.textContent = 'Fetching...';
    resultDiv.style.display = 'block';
    resultDiv.textContent = 'Fetching catalogs and schemas...';

    try {
        const response = await fetch(`${getBaseUrl()}/workflows/v1/metadata`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credentials: getCredentials() }),
        });
        const data = await response.json();

        if (data.success && data.data) {
            resultDiv.className = 'result-box success';
            const count = data.data.length;
            resultDiv.textContent = `Found ${count} catalog.schema combination(s).`;
        } else {
            resultDiv.className = 'result-box error';
            resultDiv.textContent = `Failed to fetch metadata: ${JSON.stringify(data)}`;
        }
    } catch (error) {
        resultDiv.className = 'result-box error';
        resultDiv.textContent = `Error: ${error.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Fetch Metadata';
    }
}

async function preflightCheck() {
    const btn = document.getElementById('preflightBtn');
    const resultDiv = document.getElementById('preflightResult');
    btn.disabled = true;
    btn.textContent = 'Checking...';
    resultDiv.style.display = 'block';
    resultDiv.textContent = 'Running preflight checks...';

    try {
        const response = await fetch(`${getBaseUrl()}/workflows/v1/preflight_check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                credentials: getCredentials(),
                metadata: {},
            }),
        });
        const data = await response.json();

        if (data.success) {
            resultDiv.className = 'result-box success';
            resultDiv.textContent = 'Preflight checks passed: REST API and SQL connectivity confirmed.';
        } else {
            resultDiv.className = 'result-box error';
            resultDiv.textContent = `Preflight checks failed: ${JSON.stringify(data.data)}`;
        }
    } catch (error) {
        resultDiv.className = 'result-box error';
        resultDiv.textContent = `Error: ${error.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Preflight Check';
    }
}

async function startWorkflow() {
    const btn = document.getElementById('startBtn');
    const resultDiv = document.getElementById('workflowResult');
    btn.disabled = true;
    btn.textContent = 'Starting...';
    resultDiv.style.display = 'block';
    resultDiv.textContent = 'Starting extraction workflow...';

    try {
        const payload = {
            credentials: getCredentials(),
            catalogs: [document.getElementById('catalog') ? document.getElementById('catalog').value : 'tpch'],
            metadata: {},
        };

        const response = await fetch(`${getBaseUrl()}/workflows/v1/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (response.ok) {
            resultDiv.className = 'result-box success';
            resultDiv.textContent = `Workflow started! ID: ${data.workflow_id || 'N/A'}`;

            // Show success modal
            const modal = document.getElementById('successModal');
            const link = document.getElementById('temporalLink');
            const workflowId = data.workflow_id || '';
            link.href = `http://${window.env.TEMPORAL_UI_HOST}:${window.env.TEMPORAL_UI_PORT}/namespaces/default/workflows/${workflowId}`;
            modal.style.display = 'flex';
        } else {
            resultDiv.className = 'result-box error';
            resultDiv.textContent = `Failed to start workflow: ${JSON.stringify(data)}`;
        }
    } catch (error) {
        resultDiv.className = 'result-box error';
        resultDiv.textContent = `Error: ${error.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Start Extraction';
    }
}

// Extractor App JavaScript
async function handleSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const runButton = document.getElementById('runWorkflowButton');
    
    // Disable button and show loading state
    runButton.disabled = true;
    runButton.textContent = 'Processing... ⏳';
    
    try {
        // Get form values directly from the input elements
        const inputFile = document.getElementById('inputFile').value.trim();
        const outputFile = document.getElementById('outputFile').value.trim();
        
        // Basic validation
        if (!inputFile) {
            alert('Please enter an input file path');
            runButton.disabled = false;
            runButton.textContent = 'Extract & Transform 🚀';
            return;
        }
        
        // Prepare the request payload
        const payload = {
            input_file: inputFile,
            output_file: outputFile
        };
        
        console.log('Submitting extraction request:', payload);
        console.log('Input file path:', inputFile);
        console.log('Output file path:', outputFile);
        
        // Make the API request
        const response = await fetch('/workflows/v1/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
            
        });
        
        if (response.ok) {
            runButton.textContent = "Submitted! 🎉";
            console.log('Extraction workflow started successfully');
            
            // Show success modal
            showSuccessModal();
            
            // Clear form after successful submission
            setTimeout(() => {
                form.reset();
            }, 2000);
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }
        
    } catch (error) {
        console.error('Error starting workflow:', error);
        alert(`Failed to start extraction workflow: ${error.message}`);
        runButton.textContent = "Try Again 🔄";
        runButton.classList.add("error");
    } finally {
        setTimeout(() => {
            runButton.disabled = false;
            runButton.textContent = 'Extract & Transform 🚀';
            runButton.classList.remove("error");
        }, 3000);
    }
}

function showSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.style.display = 'block';
    
    // Close modal when clicking outside
    modal.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            modal.style.display = 'none';
        }
    });
}

// Add some helpful interactions
document.addEventListener('DOMContentLoaded', function() {
    const inputFile = document.getElementById('inputFile');
    const outputFile = document.getElementById('outputFile');
    
    // Auto-generate output filename when input changes
    inputFile.addEventListener('input', function() {
        if (this.value && !outputFile.value) {
            const baseName = this.value.replace(/\.[^/.]+$/, '');
            outputFile.value = `${baseName}_transformed.json`;
        }
    });
    
    // Add file path validation
    inputFile.addEventListener('blur', function() {
        const value = this.value.trim();
        if (value && !value.endsWith('.json')) {
            this.style.borderColor = '#f56565';
            this.title = 'Please enter a valid JSON file path';
        } else {
            this.style.borderColor = '#e2e8f0';
            this.title = '';
        }
    });
    
    // Clear validation on focus
    inputFile.addEventListener('focus', function() {
        this.style.borderColor = '#e2e8f0';
        this.title = '';
    });
});

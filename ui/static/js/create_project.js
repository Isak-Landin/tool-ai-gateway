const API_ERRORS = {
    DUPLICATE_FIELD: 'This field value is already registered',
    PERSISTENCE_ERROR: 'Database error occurred',
    UNKNOWN: 'An unexpected error occurred'
};

function clearFieldErrors() {
    ['name', 'remote_repo_url', 'ssh_key'].forEach(fieldName => {
        const errorEl = document.getElementById(`${fieldName}-error`);
        if (errorEl) {
            errorEl.style.display = 'none';
            errorEl.textContent = '';
        }
    });
}

function showFieldError(fieldName, message) {
    const errorEl = document.getElementById(`${fieldName}-error`);
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
        // Scroll to error for visibility
        errorEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Handle form submission
document.getElementById('createProjectForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearFieldErrors();

    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.textContent;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating...';

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: document.getElementById('name').value,
                remote_repo_url: document.getElementById('remote_repo_url').value,
                ssh_key: document.getElementById('ssh_key').value,
            })
        });

        const data = await response.json();

        // Success: status 200-299 AND ok=true
        if (response.ok && data.ok === true) {
            // Project created successfully
            window.location.href = `/projects/${data.project_id}`;
            return; // Prevent button re-enable
        }

        // Validation error with specific field
        if (!data.ok && data.field) {
            const errorMsg = data.message ||
                           API_ERRORS[data.error_code] ||
                           API_ERRORS.UNKNOWN;
            showFieldError(data.field, errorMsg);
        }
        // Generic error without field
        else if (!data.ok === true || !data.ok === "true") {
            const errorMsg = data.message ||
                           API_ERRORS[data.error_code] ||
                           'Failed to create project';
            alert(`Error: ${errorMsg}`);
        }
        // Unexpected response
        else {
            alert('Unexpected response from server');
        }

    } catch (error) {
        // Network error, JSON parse error, etc.
        alert(`Network error: ${error.message}`);
    } finally {
        // Always restore button state if not redirecting
        if (submitBtn.disabled) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        }
    }
});
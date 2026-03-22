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

        // Success: status 200-299 AND ok=true (redirect to project)
        if (response.ok && data.ok === true) {
            window.location.href = `/projects/${data.project_id}`;
            return;
        }

        // Error with field information (show inline)
        if (!data.ok && data.field) {
            const errorMsg = data.message ||
                           API_ERRORS[data.error_code] ||
                           API_ERRORS.UNKNOWN;
            showFieldError(data.field, errorMsg);
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
            return;  // IMPORTANT: return to prevent further execution
        }

        // Generic error without field (show alert)
        if (!data.ok) {
            const errorMsg = data.message ||
                           API_ERRORS[data.error_code] ||
                           'Failed to create project';
            alert(`Error: ${errorMsg}`);
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
            return;
        }

        // Unexpected response structure
        alert('Unexpected response from server');
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;

    } catch (error) {
        console.log("Reached outside try clause");
        alert(`Network error: ${error.message}`);
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    }
});
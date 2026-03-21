function clearFieldErrors() {
    ['name', 'remote_repo_url', 'ssh_key'].forEach(fieldName => {
        const errorEl = document.getElementById(`${fieldName}-error`);
        if (errorEl) {
            errorEl.style.display = 'none';
            errorEl.textContent = '';
        }
    });
}

// Handle form submission
document.getElementById('createProjectForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearFieldErrors();

    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');

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

        // Check for success (status 200-299 AND ok=true)
        if (response.ok && data.ok === true) {
            window.location.href = `/projects/${data.project_id}`;
        }
        // Check for validation errors with field information
        else if (!data.ok && data.field) {
            const errorEl = document.getElementById(`${data.field}-error`);
            if (errorEl) {
                errorEl.textContent = data.message || `Error in ${data.field}`;
                errorEl.style.display = 'block';
            } else {
                alert(`Error in ${data.field}: ${data.message}`);
            }
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Project';
        }
        // Generic error (no specific field)
        else if (!data.ok) {
            alert(`Error: ${data.message || data.error_code || 'Failed to create project'}`);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Project';
        }
        // Unexpected success response structure
        else {
            alert('Unexpected response from server');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Project';
        }
    } catch (error) {
        alert(`Network error: ${error.message}`);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Project';
    }
});
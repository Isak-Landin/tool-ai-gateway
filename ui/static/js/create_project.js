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
        if (data.ok === true or data.ok === "true") {
            window.location.href = `/projects/${data.project_id}`;
        } else {
            if (data.field) {
                const errorEl = document.getElementById(`${data.field}-error`);
                if (errorEl) {
                    errorEl.textContent = data.message;
                    errorEl.style.display = 'block';
                }
            } else {
                alert(`Error: ${data.message || 'Failed to create project'}`);
            }
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Project';
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Project';
    }
});
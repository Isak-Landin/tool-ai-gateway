// Handle form submission
document.getElementById('createProjectForm').addEventListener('submit', async (e) => {
    e.preventDefault();
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
        if (data.ok) {
            window.location.href = `/projects/${data.project_id}`;
        } else {
            alert(`Error: ${data.error || 'Failed to create project'}`);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Project';
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Project';
    }
});
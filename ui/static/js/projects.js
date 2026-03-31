document.addEventListener("DOMContentLoaded", () => {
    const ui = window.AIToolGatewayUI;
    if (!ui) {
        return;
    }

    const createProjectPage = document.querySelector("[data-create-project-page]");
    if (createProjectPage) {
        initializeCreateProject(ui, createProjectPage);
    }
});

function initializeCreateProject(ui, page) {
    const form = page.querySelector("[data-create-project-form]");
    const statusNode = page.querySelector("[data-create-project-status]");
    const submitButton = page.querySelector("[data-create-project-submit]");

    if (!form || !statusNode || !submitButton) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(form);
        const payload = {
            name: String(formData.get("name") || "").trim(),
            remote_repo_url: String(formData.get("remote_repo_url") || "").trim(),
        };

        if (!payload.name) {
            setPanelStatus(statusNode, "error", "Project name is required.");
            return;
        }

        if (!payload.remote_repo_url) {
            setPanelStatus(statusNode, "error", "Remote repository URL is required.");
            return;
        }

        submitButton.disabled = true;
        setPanelStatus(statusNode, "loading", "Creating project bootstrap...");

        try {
            const result = await ui.requestJson("/projects", {
                method: "POST",
                body: payload,
            });

            window.location.assign(
                result.redirect_url || `/projects/bootstrap-complete?project_id=${encodeURIComponent(result.project_id)}`
            );
        } catch (error) {
            setPanelStatus(statusNode, "error", getErrorMessage(error, "Failed to create project."));
            submitButton.disabled = false;
        }
    });
}

function setPanelStatus(node, tone, message) {
    if (!node) {
        return;
    }

    node.hidden = false;
    node.className = `panel-status panel-status-${tone}`;
    node.textContent = message;
}

function getErrorMessage(error, fallbackMessage) {
    if (error?.payload?.message) {
        return error.payload.message;
    }

    if (error?.message) {
        return error.message;
    }

    return fallbackMessage;
}

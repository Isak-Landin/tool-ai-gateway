document.addEventListener("DOMContentLoaded", () => {
    const ui = window.AIToolGatewayUI;
    if (!ui) {
        return;
    }

    const projectsIndexPage = document.querySelector("[data-projects-index-page]");
    if (projectsIndexPage) {
        initializeProjectsIndex(ui, projectsIndexPage);
    }

    const createProjectPage = document.querySelector("[data-create-project-page]");
    if (createProjectPage) {
        initializeCreateProject(ui, createProjectPage);
    }

    const bootstrapPage = document.querySelector("[data-bootstrap-complete-page]");
    if (bootstrapPage) {
        initializeBootstrapComplete(bootstrapPage);
    }
});

async function initializeProjectsIndex(ui, page) {
    const statusNode = page.querySelector("[data-projects-status]");
    const listNode = page.querySelector("[data-projects-list]");
    const emptyNode = page.querySelector("[data-projects-empty]");

    setPanelStatus(statusNode, "loading", "Loading projects...");

    try {
        const payload = await ui.requestJson("/projects");
        const projects = Array.isArray(payload?.projects) ? payload.projects : [];

        if (!projects.length) {
            if (listNode) {
                listNode.hidden = true;
                listNode.replaceChildren();
            }
            if (emptyNode) {
                emptyNode.hidden = false;
            }
            setPanelStatus(statusNode, "empty", "No projects exist yet. Create one to start working.");
            return;
        }

        if (emptyNode) {
            emptyNode.hidden = true;
        }
        if (listNode) {
            listNode.hidden = false;
            listNode.replaceChildren(...projects.map((project) => buildProjectCard(ui, project)));
        }
        setPanelStatus(statusNode, "success", `${projects.length} project${projects.length === 1 ? "" : "s"} loaded.`);
    } catch (error) {
        if (listNode) {
            listNode.hidden = true;
            listNode.replaceChildren();
        }
        if (emptyNode) {
            emptyNode.hidden = true;
        }
        setPanelStatus(statusNode, "error", getErrorMessage(error, "Failed to load projects."));
    }
}

function buildProjectCard(ui, project) {
    const link = document.createElement("a");
    link.className = "panel panel-link project-card";
    link.href = `/projects/${project.project_id}`;

    const header = document.createElement("div");
    header.className = "panel-header-row";

    const title = document.createElement("h2");
    title.textContent = project.name || `Project #${project.project_id}`;

    const pill = document.createElement("span");
    pill.className = "meta-pill";
    pill.textContent = `#${project.project_id}`;

    header.append(title, pill);

    const branch = document.createElement("p");
    branch.className = "muted";
    branch.textContent = `Branch: ${project.branch || "main"}`;

    const created = document.createElement("p");
    created.className = "muted";
    created.textContent = `Created: ${ui.formatDate(project.created_at)}`;

    link.append(header, branch, created);
    return link;
}

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

            window.sessionStorage.setItem("latestProjectBootstrapResult", JSON.stringify(result));
            window.location.assign(`/projects/bootstrap-complete?project_id=${encodeURIComponent(result.project_id)}`);
        } catch (error) {
            setPanelStatus(statusNode, "error", getErrorMessage(error, "Failed to create project."));
            submitButton.disabled = false;
        }
    });
}

function initializeBootstrapComplete(page) {
    const statusNode = page.querySelector("[data-bootstrap-status]");
    const detailNode = page.querySelector("[data-bootstrap-detail]");
    const projectIdNode = page.querySelector("[data-bootstrap-project-id]");
    const projectNameNode = page.querySelector("[data-bootstrap-project-name]");
    const repoUrlNode = page.querySelector("[data-bootstrap-remote-repo-url]");
    const publicKeyNode = page.querySelector("[data-bootstrap-public-key]");
    const workspaceLink = page.querySelector("[data-bootstrap-workspace-link]");
    const settingsLink = page.querySelector("[data-bootstrap-settings-link]");

    const searchParams = new URLSearchParams(window.location.search);
    const expectedProjectId = String(searchParams.get("project_id") || "").trim();
    const savedPayload = window.sessionStorage.getItem("latestProjectBootstrapResult");

    if (!savedPayload) {
        setPanelStatus(statusNode, "error", "No recent bootstrap result is available in this browser session.");
        if (detailNode) {
            detailNode.hidden = true;
        }
        return;
    }

    let payload = null;
    try {
        payload = JSON.parse(savedPayload);
    } catch (_error) {
        payload = null;
    }

    if (!payload || (expectedProjectId && String(payload.project_id) !== expectedProjectId)) {
        setPanelStatus(statusNode, "error", "The stored bootstrap result does not match this project page.");
        if (detailNode) {
            detailNode.hidden = true;
        }
        return;
    }

    if (projectIdNode) {
        projectIdNode.textContent = String(payload.project_id || "");
    }
    if (projectNameNode) {
        projectNameNode.textContent = payload.name || "Unnamed project";
    }
    if (repoUrlNode) {
        repoUrlNode.textContent = payload.remote_repo_url || "Unavailable";
    }
    if (publicKeyNode) {
        publicKeyNode.textContent = payload.public_key || "Unavailable";
    }
    if (workspaceLink) {
        workspaceLink.href = `/projects/${payload.project_id}`;
    }
    if (settingsLink) {
        settingsLink.href = `/projects/${payload.project_id}/settings`;
    }
    if (detailNode) {
        detailNode.hidden = false;
    }

    setPanelStatus(
        statusNode,
        "success",
        "Project bootstrap was created. Add the public key before using repository-backed workspace features."
    );
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

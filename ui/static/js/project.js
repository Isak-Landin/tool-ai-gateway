document.addEventListener("DOMContentLoaded", () => {
    const ui = window.AIToolGatewayUI;
    const page = document.querySelector("[data-project-page]");

    if (!ui || !page) {
        return;
    }

    const projectId = Number(page.dataset.projectId || "0");
    if (!projectId) {
        return;
    }

    const pageData = ui.pageData || {};
    const initialProject = pageData.project || null;
    if (!initialProject) {
        return;
    }

    const state = {
        projectId,
        project: initialProject,
        branch: initialProject.branch || "main",
        models: Array.isArray(pageData.models) ? pageData.models : [],
        defaultModel: String(pageData.defaultModel || "").trim(),
        defaultSelection: String(pageData.defaultSelection || "auto").trim() || "auto",
        treeEntries: Array.isArray(pageData.treeEntries) ? pageData.treeEntries : [],
        collapsedDirs: new Set(),
        selectedFiles: new Set(),
        currentFilePath: pageData.currentFilePath || null,
    };

    initializeProjectPage(ui, page, state).catch((error) => {
        if (redirectForMissingProject(error)) {
            return;
        }

        renderProjectLoadFailure(page, error);
        console.error(error);
    });
});

async function initializeProjectPage(ui, page, state) {
    const pageType = page.dataset.projectPage;
    applyProjectShell(state.project);

    if (pageType === "workspace") {
        await initializeWorkspacePage(ui, page, state);
        return;
    }

    if (pageType === "activity") {
        await initializeActivityPage(ui, page, state);
        return;
    }

    if (pageType === "settings") {
        await initializeSettingsPage(ui, page, state);
    }
}

function redirectForMissingProject(error) {
    if (error?.status !== 404) {
        return false;
    }

    window.location.replace("/404");
    return true;
}

function renderProjectLoadFailure(page, error) {
    const message = getErrorMessage(error, "Failed to load project.");

    document.querySelectorAll("[data-project-name]").forEach((node) => {
        node.textContent = "Project unavailable";
    });

    document.querySelectorAll("[data-project-branch-pill]").forEach((node) => {
        node.textContent = "Unavailable";
    });

    [
        "[data-run-status]",
        "[data-tree-status]",
        "[data-file-status]",
        "[data-chat-status]",
        "[data-activity-status]",
        "[data-project-settings-status]",
    ].forEach((selector) => {
        const node = page.querySelector(selector);
        if (node) {
            setStatus(node, "error", message);
        }
    });
}

function applyProjectShell(project) {
    document.querySelectorAll("[data-project-name]").forEach((node) => {
        node.textContent = project.name || `Project #${project.project_id}`;
    });

    document.querySelectorAll("[data-project-branch-pill]").forEach((node) => {
        node.textContent = `Branch ${project.branch || "main"}`;
    });
}

async function initializeWorkspacePage(ui, page, state) {
    const branchInput = page.querySelector("[data-branch-input]");
    const modelSelect = page.querySelector("[data-model-select]");
    const repoReloadButton = page.querySelector("[data-repo-reload]");
    const searchForm = page.querySelector("[data-repo-search-form]");
    const runForm = page.querySelector("[data-run-form]");
    const presenterButtons = page.querySelectorAll("[data-presenter-target]");

    if (branchInput) {
        branchInput.value = state.branch;
    }
    setActivePresenter(page, "file");
    hydrateModelOptions(page, state, modelSelect);

    presenterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            setActivePresenter(page, button.dataset.presenterTarget || "file");
        });
    });

    if (repoReloadButton) {
        repoReloadButton.addEventListener("click", async () => {
            state.branch = normalizeBranchValue(branchInput?.value, state.project?.branch || "main");
            if (branchInput) {
                branchInput.value = state.branch;
            }
            await loadWorkspaceTree(ui, page, state);
        });
    }

    page.addEventListener("click", async (event) => {
        const target = event.target.closest("[data-tree-action], [data-search-result-path], [data-remove-selected-file]");
        if (!target) {
            return;
        }

        const action = target.dataset.treeAction;
        const path = target.dataset.path || target.dataset.searchResultPath || target.dataset.removeSelectedFile;

        if (action === "toggle-dir") {
            if (state.collapsedDirs.has(path)) {
                state.collapsedDirs.delete(path);
            } else {
                state.collapsedDirs.add(path);
            }
            renderTree(page, state);
            return;
        }

        if (action === "open-file" || target.dataset.searchResultPath) {
            const focusLine = Number(target.dataset.searchResultLine || "0") || null;
            await loadFile(ui, page, state, path, focusLine);
            setActivePresenter(page, "file");
            return;
        }

        if (action === "toggle-context") {
            if (state.selectedFiles.has(path)) {
                state.selectedFiles.delete(path);
            } else {
                state.selectedFiles.add(path);
            }
            renderTree(page, state);
            renderSelectedFiles(page, state);
            return;
        }

        if (target.dataset.removeSelectedFile) {
            state.selectedFiles.delete(path);
            renderTree(page, state);
            renderSelectedFiles(page, state);
        }
    });

    if (searchForm) {
        searchForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            await runRepositorySearch(ui, page, state);
        });
    }

    if (runForm) {
        runForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            await runProjectChat(ui, page, state);
        });
    }

}

async function initializeActivityPage(ui, page, state) {
    applyProjectShell(state.project);
}

async function initializeSettingsPage(ui, page, state) {
    const form = page.querySelector("[data-project-settings-form]");
    const statusNode = page.querySelector("[data-project-settings-status]");
    const nameInput = page.querySelector("[data-project-name-input]");
    const branchInput = page.querySelector("[data-project-branch-input]");
    const createdAtNode = page.querySelector("[data-project-created-at]");
    const updatedAtNode = page.querySelector("[data-project-updated-at]");

    applyProjectShell(state.project);

    if (!form) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        setStatus(statusNode, "loading", "Saving project settings...");

        try {
            const payload = await ui.requestJson(`/projects/${state.projectId}`, {
                method: "PATCH",
                body: {
                    name: String(nameInput?.value || "").trim(),
                    branch: normalizeBranchValue(branchInput?.value, state.project?.branch || "main"),
                },
            });

            state.project = payload;
            state.branch = payload.branch || state.branch;
            applyProjectShell(payload);
            fillSettingsPage(ui, payload, nameInput, branchInput, createdAtNode, updatedAtNode);
            setStatus(statusNode, "success", "Project settings saved.");
        } catch (error) {
            if (redirectForMissingProject(error)) {
                return;
            }
            setStatus(statusNode, "error", getErrorMessage(error, "Failed to save project settings."));
        }
    });
}

function fillSettingsPage(ui, project, nameInput, branchInput, createdAtNode, updatedAtNode) {
    if (nameInput) {
        nameInput.value = project.name || "";
    }
    if (branchInput) {
        branchInput.value = project.branch || "main";
    }
    if (createdAtNode) {
        createdAtNode.textContent = ui.formatDate(project.created_at);
    }
    if (updatedAtNode) {
        updatedAtNode.textContent = project.updated_at ? ui.formatDate(project.updated_at) : "Not updated yet";
    }
}

function hydrateModelOptions(page, state, selectNode) {
    const statusNode = page.querySelector("[data-run-status]");
    if (!selectNode) {
        return;
    }

    if (state.models.length) {
        selectNode.disabled = false;
        populateModelOptions(selectNode, state.models, state.defaultSelection);
        setStatus(statusNode, "muted", `Using backend model catalog. Auto resolves to ${state.defaultModel}.`);
        return;
    }

    selectNode.disabled = true;
    selectNode.replaceChildren(buildUnavailableModelOption());
}

function buildUnavailableModelOption() {
    const node = document.createElement("option");
    node.value = "";
    node.textContent = "Model options unavailable";
    return node;
}

function populateModelOptions(selectNode, models, defaultSelection) {
    selectNode.replaceChildren(...models.map((option) => {
        const node = document.createElement("option");
        node.value = option.value;
        node.textContent = option.label;
        node.selected = option.value === defaultSelection;
        return node;
    }));
}

function setActivePresenter(page, target) {
    page.querySelectorAll("[data-presenter-target]").forEach((button) => {
        button.classList.toggle("is-active", button.dataset.presenterTarget === target);
    });
    page.querySelectorAll("[data-presenter-view]").forEach((view) => {
        view.classList.toggle("is-active", view.dataset.presenterView === target);
    });
}

async function loadWorkspaceTree(ui, page, state) {
    const statusNode = page.querySelector("[data-tree-status]");
    setStatus(statusNode, "loading", "Loading repository tree...");

    try {
        const params = new URLSearchParams();
        const branch = normalizeBranchValue(page.querySelector("[data-branch-input]")?.value, state.project?.branch || "main");
        state.branch = branch;
        if (branch) {
            params.set("branch", branch);
        }

        const payload = await ui.requestJson(`/projects/${state.projectId}/repository/tree?${params.toString()}`);
        state.treeEntries = Array.isArray(payload?.entries) ? payload.entries : [];
        renderTree(page, state);

        if (state.treeEntries.length) {
            const firstFile = state.treeEntries.find((entry) => entry.is_file);
            if (firstFile && !state.currentFilePath) {
                await loadFile(ui, page, state, firstFile.path, null);
            }
            setStatus(statusNode, "success", `${state.treeEntries.length} repository entries loaded.`);
        } else {
            clearFileView(page);
            setStatus(statusNode, "empty", "No repository entries are available for this branch yet.");
        }
    } catch (error) {
        if (redirectForMissingProject(error)) {
            return;
        }
        state.treeEntries = [];
        renderTree(page, state);
        clearFileView(page);
        setStatus(statusNode, "error", getErrorMessage(error, "Failed to load repository tree."));
    }
}

function renderTree(page, state) {
    const treeNode = page.querySelector("[data-repo-tree]");
    const emptyNode = page.querySelector("[data-tree-empty]");

    if (!treeNode) {
        return;
    }

    treeNode.replaceChildren();

    if (!state.treeEntries.length) {
        treeNode.hidden = true;
        if (emptyNode) {
            emptyNode.hidden = false;
        }
        renderSelectedFiles(page, state);
        return;
    }

    treeNode.hidden = false;
    if (emptyNode) {
        emptyNode.hidden = true;
    }

    const visibleEntries = state.treeEntries.filter((entry) => {
        const hiddenByCollapsedParent = Array.from(state.collapsedDirs).some((collapsedPath) => (
            entry.path !== collapsedPath && entry.path.startsWith(`${collapsedPath}/`)
        ));
        return !hiddenByCollapsedParent;
    });

    visibleEntries.forEach((entry) => {
        const item = document.createElement("li");
        item.className = `repo-tree-item ${entry.is_dir ? "repo-tree-item-directory" : "repo-tree-item-file"}${state.currentFilePath === entry.path ? " is-current" : ""}`;
        item.style.setProperty("--tree-depth", String(Math.max(Number(entry.depth || 1) - 1, 0)));

        const row = document.createElement("div");
        row.className = "repo-tree-row";

        const indent = document.createElement("span");
        indent.className = "repo-tree-indent";
        row.append(indent);

        const primaryButton = document.createElement("button");
        primaryButton.type = "button";
        primaryButton.className = "repo-tree-button";
        primaryButton.dataset.treeAction = entry.is_dir ? "toggle-dir" : "open-file";
        primaryButton.dataset.path = entry.path;
        primaryButton.setAttribute("aria-expanded", entry.is_dir ? String(!state.collapsedDirs.has(entry.path)) : "false");

        const icon = document.createElement("span");
        icon.className = "repo-tree-icon";
        icon.textContent = entry.is_dir ? (state.collapsedDirs.has(entry.path) ? "▸" : "▾") : "•";

        const label = document.createElement("span");
        label.className = "repo-tree-label";
        label.textContent = entry.name;

        primaryButton.append(icon, label);
        row.append(primaryButton);

        if (entry.is_file) {
            const toggleContextButton = document.createElement("button");
            toggleContextButton.type = "button";
            toggleContextButton.className = `repo-tree-context-toggle${state.selectedFiles.has(entry.path) ? " is-selected" : ""}`;
            toggleContextButton.dataset.treeAction = "toggle-context";
            toggleContextButton.dataset.path = entry.path;
            toggleContextButton.textContent = state.selectedFiles.has(entry.path) ? "Added" : "Add";
            row.append(toggleContextButton);
        }

        item.append(row);
        treeNode.append(item);
    });

    renderSelectedFiles(page, state);
}

async function loadFile(ui, page, state, filePath, focusLine) {
    const statusNode = page.querySelector("[data-file-status]");
    setStatus(statusNode, "loading", "Loading file content...");

    try {
        const params = new URLSearchParams();
        params.set("path", filePath);
        if (state.branch) {
            params.set("branch", state.branch);
        }
        if (focusLine) {
            params.set("start_line", String(Math.max(focusLine - 20, 1)));
            params.set("number_of_lines", "80");
        }

        const payload = await ui.requestJson(`/projects/${state.projectId}/repository/file?${params.toString()}`);
        state.currentFilePath = payload.path;
        renderTree(page, state);
        renderFileView(page, payload, focusLine);
        setStatus(statusNode, "success", `Loaded ${payload.path}.`);
    } catch (error) {
        if (redirectForMissingProject(error)) {
            return;
        }
        clearFileView(page);
        setStatus(statusNode, "error", getErrorMessage(error, "Failed to load file content."));
    }
}

function renderFileView(page, file, focusLine) {
    const pathNode = page.querySelector("[data-file-path]");
    const metaNode = page.querySelector("[data-file-meta]");
    const gutterNode = page.querySelector("[data-file-gutter]");
    const contentNode = page.querySelector("[data-file-content]");
    const emptyNode = page.querySelector("[data-file-empty]");
    const codeWindow = page.querySelector("[data-code-window]");

    if (!gutterNode || !contentNode || !pathNode || !metaNode || !emptyNode || !codeWindow) {
        return;
    }

    const lines = String(file.content || "").split("\n");
    gutterNode.replaceChildren();
    contentNode.replaceChildren();

    lines.forEach((line, index) => {
        const lineNumber = file.start_line + index;
        const gutterLine = document.createElement("span");
        gutterLine.textContent = String(lineNumber);
        if (focusLine && lineNumber === focusLine) {
            gutterLine.classList.add("is-focus-line");
        }
        gutterNode.append(gutterLine);

        const codeLine = document.createElement("span");
        codeLine.className = "code-line";
        if (focusLine && lineNumber === focusLine) {
            codeLine.classList.add("is-focus-line");
        }
        codeLine.textContent = line || " ";
        contentNode.append(codeLine);
    });

    pathNode.textContent = file.path;
    metaNode.textContent = `${file.total_lines} total lines · showing ${file.start_line}-${file.end_line}`;
    codeWindow.hidden = false;
    emptyNode.hidden = true;
}

function clearFileView(page) {
    const pathNode = page.querySelector("[data-file-path]");
    const metaNode = page.querySelector("[data-file-meta]");
    const gutterNode = page.querySelector("[data-file-gutter]");
    const contentNode = page.querySelector("[data-file-content]");
    const emptyNode = page.querySelector("[data-file-empty]");
    const codeWindow = page.querySelector("[data-code-window]");

    if (pathNode) {
        pathNode.textContent = "No file selected";
    }
    if (metaNode) {
        metaNode.textContent = "Choose a file from the repository tree or search results.";
    }
    if (gutterNode) {
        gutterNode.replaceChildren();
    }
    if (contentNode) {
        contentNode.replaceChildren();
    }
    if (codeWindow) {
        codeWindow.hidden = true;
    }
    if (emptyNode) {
        emptyNode.hidden = false;
    }
}

async function runRepositorySearch(ui, page, state) {
    const queryInput = page.querySelector("[data-repo-search-query]");
    const statusNode = page.querySelector("[data-repo-search-status]");
    const resultsNode = page.querySelector("[data-repo-search-results]");
    const emptyNode = page.querySelector("[data-repo-search-empty]");

    if (!queryInput || !resultsNode || !emptyNode) {
        return;
    }

    const query = String(queryInput.value || "").trim();
    if (!query) {
        resultsNode.replaceChildren();
        resultsNode.hidden = true;
        emptyNode.hidden = false;
        setStatus(statusNode, "empty", "Enter a query to search the repository.");
        return;
    }

    setStatus(statusNode, "loading", "Searching repository text...");

    try {
        const params = new URLSearchParams({ query });
        if (state.branch) {
            params.set("branch", state.branch);
        }
        const payload = await ui.requestJson(`/projects/${state.projectId}/repository/search?${params.toString()}`);
        const matches = Array.isArray(payload?.matches) ? payload.matches : [];

        resultsNode.replaceChildren(...matches.map((match) => buildSearchResult(match)));
        resultsNode.hidden = !matches.length;
        emptyNode.hidden = matches.length > 0;
        setStatus(
            statusNode,
            matches.length ? "success" : "empty",
            matches.length ? `${matches.length} search result${matches.length === 1 ? "" : "s"} loaded.` : "No repository matches found."
        );
    } catch (error) {
        if (redirectForMissingProject(error)) {
            return;
        }
        resultsNode.replaceChildren();
        resultsNode.hidden = true;
        emptyNode.hidden = false;
        setStatus(statusNode, "error", getErrorMessage(error, "Failed to search repository text."));
    }
}

function buildSearchResult(match) {
    const item = document.createElement("li");
    item.className = "search-results-item";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "search-result-button";
    button.dataset.searchResultPath = match.path;
    button.dataset.searchResultLine = String(match.line_number || "");

    const title = document.createElement("strong");
    title.textContent = `${match.path}:${match.line_number}`;

    const snippet = document.createElement("span");
    snippet.className = "muted";
    snippet.textContent = match.line_text || "";

    button.append(title, snippet);
    item.append(button);
    return item;
}

async function loadMessages(ui, page, state, options) {
    const containerNode = page.querySelector(options.containerSelector);
    const statusNode = page.querySelector(options.statusSelector);
    const emptyNode = page.querySelector(options.emptySelector);

    if (!containerNode || !statusNode || !emptyNode) {
        return;
    }

    setStatus(statusNode, "loading", "Loading project history...");

    try {
        const payload = await ui.requestJson(`/projects/${state.projectId}/messages`);
        const messages = Array.isArray(payload?.messages) ? payload.messages : [];

        containerNode.replaceChildren(...messages.map((message) => buildMessageCard(ui, message)));
        containerNode.hidden = !messages.length;
        emptyNode.hidden = messages.length > 0;
        setStatus(
            statusNode,
            messages.length ? "success" : "empty",
            messages.length ? `${messages.length} message${messages.length === 1 ? "" : "s"} loaded.` : "No project history exists yet."
        );
    } catch (error) {
        if (redirectForMissingProject(error)) {
            return;
        }
        containerNode.replaceChildren();
        containerNode.hidden = true;
        emptyNode.hidden = false;
        setStatus(statusNode, "error", getErrorMessage(error, "Failed to load project history."));
    }
}

function buildMessageCard(ui, message) {
    const article = document.createElement("article");
    article.className = `chat-entry chat-entry-${message.role || "message"}`;

    const header = document.createElement("header");
    header.className = "chat-entry-header";

    const meta = document.createElement("div");
    meta.className = "chat-entry-meta";

    const roleLabel = document.createElement("strong");
    roleLabel.textContent = `${message.role || "message"} #${message.sequence_no}`;

    const timestamp = document.createElement("span");
    timestamp.className = "muted";
    timestamp.textContent = ui.formatDate(message.created_at);

    meta.append(roleLabel, timestamp);

    const stateNode = document.createElement("span");
    stateNode.className = "chat-entry-state";
    stateNode.textContent = message.ai_model_name ? `Model ${message.ai_model_name}` : "Project history";

    header.append(meta, stateNode);

    const content = document.createElement("p");
    content.className = "chat-entry-content";
    content.textContent = message.content || "(No text content)";

    article.append(header, content);

    if (message.thinking) {
        const thoughtBlock = document.createElement("div");
        thoughtBlock.className = "thought-block";

        const thoughtLabel = document.createElement("p");
        thoughtLabel.className = "thought-label";
        thoughtLabel.textContent = "Model thought";

        const thoughtContent = document.createElement("p");
        thoughtContent.className = "thought-content";
        thoughtContent.textContent = message.thinking;

        thoughtBlock.append(thoughtLabel, thoughtContent);
        article.append(thoughtBlock);
    }

    if (message.tool_name || message.done_reason) {
        const footer = document.createElement("div");
        footer.className = "message-detail-row";
        if (message.tool_name) {
            const tool = document.createElement("span");
            tool.className = "meta-pill";
            tool.textContent = `Tool ${message.tool_name}`;
            footer.append(tool);
        }
        if (message.done_reason) {
            const doneReason = document.createElement("span");
            doneReason.className = "meta-pill";
            doneReason.textContent = `Done ${message.done_reason}`;
            footer.append(doneReason);
        }
        article.append(footer);
    }

    return article;
}

function renderSelectedFiles(page, state) {
    const node = page.querySelector("[data-selected-files]");
    const emptyNode = page.querySelector("[data-selected-files-empty]");
    if (!node || !emptyNode) {
        return;
    }

    const selected = Array.from(state.selectedFiles).sort();
    node.replaceChildren(...selected.map((path) => {
        const item = document.createElement("li");
        item.className = "selected-file-chip";

        const label = document.createElement("span");
        label.textContent = path;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.dataset.removeSelectedFile = path;
        remove.textContent = "×";
        remove.setAttribute("aria-label", `Remove ${path} from selected context`);

        item.append(label, remove);
        return item;
    }));

    node.hidden = !selected.length;
    emptyNode.hidden = selected.length > 0;
}

async function runProjectChat(ui, page, state) {
    const statusNode = page.querySelector("[data-run-status]");
    const messageInput = page.querySelector("[data-run-message]");
    const branchInput = page.querySelector("[data-branch-input]");
    const modelSelect = page.querySelector("[data-model-select]");
    const submitButton = page.querySelector("[data-run-submit]");

    const message = String(messageInput?.value || "").trim();
    if (!message) {
        setStatus(statusNode, "error", "A message is required before sending a run.");
        return;
    }

    const branch = normalizeBranchValue(branchInput?.value, state.project?.branch || "main");
    const selectedModelValue = String(modelSelect?.value || "").trim();
    const aiModelName = selectedModelValue && selectedModelValue !== "auto" ? selectedModelValue : null;

    if (submitButton) {
        submitButton.disabled = true;
    }
    setStatus(statusNode, "loading", "Running project chat...");

    try {
        await ui.requestJson(`/projects/${state.projectId}/run`, {
            method: "POST",
            body: {
                message,
                selected_files: Array.from(state.selectedFiles),
                branch,
                ai_model_name: aiModelName,
            },
        });

        if (messageInput) {
            messageInput.value = "";
        }
        setActivePresenter(page, "chat");
        await loadMessages(ui, page, state, {
            containerSelector: "[data-chat-history]",
            statusSelector: "[data-chat-status]",
            emptySelector: "[data-chat-empty]",
        });
        setStatus(statusNode, "success", "Project chat run completed.");
    } catch (error) {
        if (redirectForMissingProject(error)) {
            return;
        }
        setStatus(statusNode, "error", getErrorMessage(error, "Project chat run failed."));
    } finally {
        if (submitButton) {
            submitButton.disabled = false;
        }
    }
}

function normalizeBranchValue(inputValue, fallbackBranch) {
    const normalizedValue = String(inputValue || "").trim();
    return normalizedValue || String(fallbackBranch || "main").trim() || "main";
}

function setStatus(node, tone, message) {
    if (!node) {
        return;
    }

    node.hidden = false;
    node.className = tone === "muted" ? "panel-status panel-status-muted" : `panel-status panel-status-${tone}`;
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

const selectedFiles = new Map();

async function fetchTree() {
    const res = await fetch("/api/tree");
    const data = await res.json();
    renderTree(data.roots || {});
}

function renderTree(roots) {
    const treeEl = document.getElementById("tree");
    treeEl.innerHTML = "";

    Object.entries(roots).forEach(([rootName, rootData]) => {
        const section = document.createElement("div");
        section.style.marginBottom = "16px";

        const title = document.createElement("h3");
        title.textContent = rootName;
        section.appendChild(title);

        const rootPath = document.createElement("div");
        rootPath.className = "muted small";
        rootPath.textContent = rootData.root_path || "";
        section.appendChild(rootPath);

        if (rootData.error) {
            const error = document.createElement("div");
            error.textContent = rootData.error;
            error.style.color = "#ff7b7b";
            section.appendChild(error);
        } else {
            const treeWrap = document.createElement("div");
            treeWrap.className = "tree-root";
            treeWrap.appendChild(buildTreeList(rootName, rootData.children || []));
            section.appendChild(treeWrap);
        }

        treeEl.appendChild(section);
    });
}

function buildTreeList(rootName, nodes) {
    const container = document.createElement("div");
    container.className = "tree-group";

    nodes.forEach((node) => {
        if (node.type === "directory") {
            container.appendChild(buildDirectoryNode(rootName, node));
        } else {
            container.appendChild(buildFileNode(rootName, node));
        }
    });

    return container;
}

function buildDirectoryNode(rootName, node) {
    const details = document.createElement("details");
    details.className = "tree-nav__item is-expandable";

    const summary = document.createElement("summary");
    summary.className = "tree-nav__item-title";

    const summaryLeft = document.createElement("span");
    summaryLeft.textContent = `📁 ${node.name}`;

    const summaryRight = document.createElement("span");
    summaryRight.style.display = "inline-flex";
    summaryRight.style.gap = "8px";
    summaryRight.style.marginLeft = "12px";

    const previewBtn = document.createElement("button");
    previewBtn.type = "button";
    previewBtn.className = "secondary";
    previewBtn.textContent = "Preview";
    previewBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        previewDirectory(node);
    };

    const selectBtn = document.createElement("button");
    selectBtn.type = "button";
    selectBtn.textContent = "Select all";
    selectBtn.onclick = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await selectDirectory(rootName, node);
    };

    summaryRight.appendChild(previewBtn);
    summaryRight.appendChild(selectBtn);

    summary.appendChild(summaryLeft);
    summary.appendChild(summaryRight);
    details.appendChild(summary);

    if (node.children && node.children.length > 0) {
        details.appendChild(buildTreeList(rootName, node.children));
    }

    return details;
}

function buildFileNode(rootName, node) {
    const row = document.createElement("div");
    row.className = "tree-file-row";

    const left = document.createElement("span");
    left.className = "tree-nav__item-title";
    left.textContent = `📄 ${node.name}`;

    const right = document.createElement("div");
    right.style.display = "inline-flex";
    right.style.gap = "8px";

    const previewBtn = document.createElement("button");
    previewBtn.type = "button";
    previewBtn.className = "secondary";
    previewBtn.textContent = "Preview";
    previewBtn.onclick = () => previewFile(rootName, node.path);

    const selectBtn = document.createElement("button");
    selectBtn.type = "button";
    selectBtn.textContent = "Select";
    selectBtn.onclick = () => selectFile(rootName, node.path);

    right.appendChild(previewBtn);
    right.appendChild(selectBtn);

    row.appendChild(left);
    row.appendChild(right);

    return row;
}

function collectFilePathsFromNode(node) {
    const paths = [];

    if (node.type === "file") {
        paths.push(node.path);
        return paths;
    }

    if (node.children && node.children.length > 0) {
        node.children.forEach((child) => {
            paths.push(...collectFilePathsFromNode(child));
        });
    }

    return paths;
}

async function selectDirectory(rootName, node) {
    const filePaths = collectFilePathsFromNode(node);

    for (const path of filePaths) {
        await selectFile(rootName, path, true);
    }

    renderSelectedFiles();
}

function previewDirectory(node) {
    const filePaths = collectFilePathsFromNode(node);

    document.getElementById("preview-meta").textContent =
        `${node.path || node.name} (${filePaths.length} files)`;

    document.getElementById("preview-content").textContent =
        filePaths.length > 0
            ? filePaths.join("\n")
            : "Directory is empty.";
}

async function previewFile(root, path) {
    const res = await fetch("/api/read", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root, path })
    });

    const data = await res.json();

    document.getElementById("preview-meta").textContent =
        data.ok ? `${data.root} / ${data.path} (${data.size} bytes)` : (data.error || "error");

    document.getElementById("preview-content").textContent =
        data.ok ? data.content : JSON.stringify(data, null, 2);
}

async function selectFile(root, path, skipRender = false) {
    const key = `${root}:${path}`;
    if (selectedFiles.has(key)) {
        return;
    }

    const res = await fetch("/api/read", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root, path })
    });

    const data = await res.json();
    if (!data.ok) {
        if (!skipRender) {
            alert(data.error || "Failed to read file");
        }
        return;
    }

    selectedFiles.set(key, {
        root: data.root,
        path: data.path,
        content: data.content,
        size: data.size
    });

    if (!skipRender) {
        renderSelectedFiles();
    }
}

function removeSelectedFile(key) {
    selectedFiles.delete(key);
    renderSelectedFiles();
}

function renderSelectedFiles() {
    const container = document.getElementById("selected-files");
    container.innerHTML = "";

    if (selectedFiles.size === 0) {
        container.innerHTML = '<div class="muted">No files selected.</div>';
        return;
    }

    selectedFiles.forEach((file, key) => {
        const row = document.createElement("div");
        row.className = "file-row";

        const left = document.createElement("div");
        left.innerHTML = `<div>${file.root} / ${file.path}</div><div class="muted small">${file.size} bytes</div>`;

        const right = document.createElement("div");

        const previewBtn = document.createElement("button");
        previewBtn.className = "secondary";
        previewBtn.textContent = "Preview";
        previewBtn.onclick = () => {
            document.getElementById("preview-meta").textContent =
                `${file.root} / ${file.path} (${file.size} bytes)`;
            document.getElementById("preview-content").textContent = file.content;
        };

        const removeBtn = document.createElement("button");
        removeBtn.textContent = "Remove";
        removeBtn.onclick = () => removeSelectedFile(key);

        right.appendChild(previewBtn);
        right.appendChild(removeBtn);

        row.appendChild(left);
        row.appendChild(right);

        container.appendChild(row);
    });
}

async function sendToGateway() {
    const instruction = document.getElementById("instruction").value;
    const files = Array.from(selectedFiles.values());

    const res = await fetch("/api/send-to-gateway", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction, files })
    });

    const data = await res.json();
    document.getElementById("gateway-response").textContent = JSON.stringify(data, null, 2);
}

document.getElementById("send-btn").addEventListener("click", sendToGateway);
document.getElementById("refresh-btn").addEventListener("click", fetchTree);

renderSelectedFiles();
fetchTree();
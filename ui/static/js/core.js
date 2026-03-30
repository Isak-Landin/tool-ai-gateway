document.documentElement.classList.add('js');

(() => {
    const rawConfig = window.__AI_TOOL_GATEWAY_UI_CONFIG__ || {};
    const gatewayBaseUrl = String(rawConfig.gatewayBaseUrl || '').replace(/\/+$/, '');

    function buildApiUrl(path) {
        const normalizedPath = String(path || '').startsWith("/") ? String(path || "") : `/${String(path || "")}`;
        return `${gatewayBaseUrl}${normalizedPath}`;
    }

    async function requestJson(path, options = {}) {
        const requestOptions = { method: "GET", ...options };
        const headers = new Headers(requestOptions.headers || {});
        const body = requestOptions.body;

        if (body && !(body instanceof FormData) && typeof body === "object") {
            headers.set("Content-Type", "application/json");
            requestOptions.body = JSON.stringify(body);
        }

        requestOptions.headers = headers;

        const response = await fetch(buildApiUrl(path), requestOptions);
        const rawText = await response.text();
        let payload = null;

        if (rawText) {
            try {
                payload = JSON.parse(rawText);
            } catch (_error) {
                payload = null;
            }
        }

        if (!response.ok) {
            const error = new Error(
                (payload && typeof payload.message === "string" && payload.message)
                || response.statusText
                || "Request failed"
            );
            error.status = response.status;
            error.payload = payload;
            throw error;
        }

        return payload;
    }

    function formatDate(value) {
        if (!value) {
            return "Unknown date";
        }

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return "Unknown date";
        }

        return new Intl.DateTimeFormat(undefined, {
            dateStyle: "medium",
            timeStyle: "short",
        }).format(date);
    }

    window.AIToolGatewayUI = {
        config: {
            gatewayBaseUrl,
        },
        buildApiUrl,
        requestJson,
        formatDate,
    };
})();

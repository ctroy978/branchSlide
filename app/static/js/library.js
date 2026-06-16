function showError(message) {
    const banner = document.getElementById("error-banner");
    banner.textContent = message;
    banner.classList.remove("hidden");
}

function clearError() {
    const banner = document.getElementById("error-banner");
    banner.classList.add("hidden");
    banner.textContent = "";
}

function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderValidationReport(container, report) {
    container.classList.remove("hidden");
    const lines = [];
    if (report.valid) {
        lines.push('<p class="text-green-800 font-medium">Validation passed.</p>');
    } else {
        lines.push('<p class="text-red-800 font-medium">Validation failed.</p>');
    }
    for (const issue of report.errors) {
        const loc = issue.path ? ` (${issue.path})` : "";
        lines.push(`<p class="text-red-700 text-sm">ERROR${loc}: ${issue.message}</p>`);
    }
    for (const issue of report.warnings) {
        const loc = issue.path ? ` (${issue.path})` : "";
        lines.push(`<p class="text-amber-700 text-sm">WARN${loc}: ${issue.message}</p>`);
    }
    container.innerHTML = lines.join("");
}

function statusBadge(entry) {
    if (entry.installed) {
        return '<span class="inline-block bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded">Installed</span>';
    }
    if (entry.slug) {
        return '<span class="inline-block bg-slate-100 text-slate-700 text-xs font-medium px-2 py-1 rounded">Ready</span>';
    }
    return '<span class="inline-block bg-amber-100 text-amber-800 text-xs font-medium px-2 py-1 rounded">Unreadable</span>';
}

function renderEntries(entries) {
    const list = document.getElementById("library-list");
    const empty = document.getElementById("library-empty");

    if (!entries.length) {
        list.innerHTML = "";
        empty.classList.remove("hidden");
        return;
    }

    empty.classList.add("hidden");
    list.innerHTML = entries.map((entry) => {
        const title = entry.title || entry.slug || "Unknown map";
        const slugLine = entry.slug
            ? `<p class="text-sm text-slate-500 mb-1">Slug: <code class="bg-slate-100 px-1 rounded">${entry.slug}</code></p>`
            : '<p class="text-sm text-amber-700 mb-1">Could not read manifest from archive.</p>';
        const installedActions = entry.installed
            ? `<button onclick="uninstallMap('${entry.installed_slug}')"
                       class="bg-white border border-red-300 text-red-700 px-3 py-2 rounded-lg text-sm hover:bg-red-50">
                    Uninstall
               </button>`
            : "";
        const installBtn = entry.slug
            ? `<button onclick="installZip('${entry.filename}')"
                       class="bg-indigo-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-indigo-700">
                    ${entry.installed ? "Re-install" : "Install"}
               </button>`
            : "";
        const deleteBtn = !entry.installed
            ? `<button onclick="deleteZip('${entry.filename}')"
                       class="bg-white border border-slate-300 text-slate-600 px-3 py-2 rounded-lg text-sm hover:bg-slate-50">
                    Delete zip
               </button>`
            : "";
        const teacherLink = entry.installed
            ? `<a href="/g/${entry.installed_slug}/teacher"
                  class="bg-white border border-indigo-300 text-indigo-700 px-3 py-2 rounded-lg text-sm hover:bg-indigo-50">
                    Open teacher panel
               </a>`
            : "";

        return `
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6" id="entry-${entry.filename}">
            <div class="flex flex-wrap items-start justify-between gap-3 mb-3">
                <div>
                    <h2 class="text-lg font-semibold">${title}</h2>
                    <p class="text-sm text-slate-500">${entry.filename} · ${formatFileSize(entry.file_size)}</p>
                </div>
                ${statusBadge(entry)}
            </div>
            ${slugLine}
            <div class="flex flex-wrap gap-2 mb-3">
                <button onclick="validateZip('${entry.filename}')"
                        class="bg-white border border-slate-300 text-slate-700 px-3 py-2 rounded-lg text-sm hover:bg-slate-50">
                    Validate
                </button>
                ${installBtn}
                ${installedActions}
                ${teacherLink}
                ${deleteBtn}
            </div>
            <div id="report-${entry.filename}" class="hidden bg-slate-50 border border-slate-200 rounded-lg p-3"></div>
        </div>`;
    }).join("");
}

async function refreshLibrary() {
    const response = await fetch("/api/admin/library");
    if (!response.ok) {
        throw new Error("Failed to load library");
    }
    const entries = await response.json();
    renderEntries(entries);
}

async function uploadZip() {
    clearError();
    const input = document.getElementById("zip-upload");
    const button = document.getElementById("upload-button");
    if (!input.files || !input.files.length) {
        showError("Choose a .zip file to upload.");
        return;
    }

    const formData = new FormData();
    formData.append("file", input.files[0]);
    button.disabled = true;
    button.textContent = "Uploading…";

    try {
        const response = await fetch("/api/admin/library/upload", {
            method: "POST",
            body: formData,
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || "Upload failed");
        }
        input.value = "";
        await refreshLibrary();
    } catch (err) {
        showError(err.message);
    } finally {
        button.disabled = false;
        button.textContent = "Upload";
    }
}

async function validateZip(filename) {
    clearError();
    const reportEl = document.getElementById(`report-${filename}`);
    reportEl.innerHTML = '<p class="text-sm text-slate-500">Validating…</p>';
    reportEl.classList.remove("hidden");

    try {
        const response = await fetch(`/api/admin/library/${encodeURIComponent(filename)}/validate`, {
            method: "POST",
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Validation request failed");
        }
        renderValidationReport(reportEl, data);
    } catch (err) {
        showError(err.message);
        reportEl.classList.add("hidden");
    }
}

async function installZip(filename) {
    clearError();
    const reportEl = document.getElementById(`report-${filename}`);
    reportEl.innerHTML = '<p class="text-sm text-slate-500">Installing…</p>';
    reportEl.classList.remove("hidden");

    try {
        const response = await fetch(`/api/admin/library/${encodeURIComponent(filename)}/install`, {
            method: "POST",
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Install failed");
        }
        const warnings = data.warnings || [];
        renderValidationReport(reportEl, {
            valid: true,
            errors: [],
            warnings,
        });
        await refreshLibrary();
    } catch (err) {
        showError(err.message);
        reportEl.classList.add("hidden");
    }
}

async function uninstallMap(slug) {
    clearError();
    const force = document.getElementById("force-uninstall")?.checked;
    if (!force && !confirm(`Uninstall "${slug}"? The map will be removed from the catalog and its files deleted. The zip stays in the library.`)) {
        return;
    }

    try {
        const url = `/api/admin/library/installed/${encodeURIComponent(slug)}${force ? "?force=true" : ""}`;
        const response = await fetch(url, { method: "DELETE" });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            if (response.status === 409) {
                showError(`${data.detail} Enable "Force uninstall" to remove anyway.`);
                return;
            }
            throw new Error(data.detail || "Uninstall failed");
        }
        await refreshLibrary();
    } catch (err) {
        showError(err.message);
    }
}

async function deleteZip(filename) {
    clearError();
    if (!confirm(`Delete "${filename}" from the library?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/library/${encodeURIComponent(filename)}`, {
            method: "DELETE",
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || "Delete failed");
        }
        await refreshLibrary();
    } catch (err) {
        showError(err.message);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const entries = window.__LIBRARY_ENTRIES__ || [];
    renderEntries(entries);
});
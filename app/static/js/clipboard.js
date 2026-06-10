async function copyText(text) {
    if (!text) {
        return false;
    }

    if (navigator.clipboard?.writeText) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch {
            // Fall back below — common on http:// LAN URLs (non-secure context).
        }
    }

    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    let copied = false;
    try {
        copied = document.execCommand('copy');
    } finally {
        document.body.removeChild(textarea);
    }
    return copied;
}

function selectInputText(inputId) {
    const input = document.getElementById(inputId);
    if (!input) {
        return;
    }
    input.focus();
    input.select();
}
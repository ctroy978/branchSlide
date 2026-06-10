async function endBranchSlideService(shutdownUrl = '/api/shutdown') {
    const confirmed = window.confirm(
        'Stop BranchSlide on this computer?\n\n' +
        'Both teacher and projector servers will shut down.'
    );
    if (!confirmed) {
        return;
    }

    try {
        await fetch(shutdownUrl, { method: 'POST' });
    } catch {
        // The server may close before the response finishes.
    }

    document.body.innerHTML = `
        <div class="min-h-screen flex flex-col items-center justify-center px-8 text-center bg-slate-50 text-slate-900">
            <h1 class="text-3xl font-bold mb-3">BranchSlide stopped</h1>
            <p class="text-slate-600 max-w-md">
                Teacher and projector servers have been shut down on this computer.
                Start again with <code class="bg-slate-200 px-1 rounded">uv run main</code>.
            </p>
        </div>`;
}
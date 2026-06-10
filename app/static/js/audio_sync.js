function stopAllAudio() {
    document.querySelectorAll('.slide-audio').forEach((element) => {
        element.pause();
        element.currentTime = 0;
    });
}

function playAudio(assetId) {
    const element = document.getElementById(`asset-${assetId}`);
    if (element) {
        element.play().catch(() => {});
    }
}

function pauseAudio(assetId) {
    const element = document.getElementById(`asset-${assetId}`);
    if (element) {
        element.pause();
    }
}

function handleAudioControl(message) {
    const assetId = message.asset_id;
    if (message.action === 'play') {
        playAudio(assetId);
    } else if (message.action === 'pause') {
        pauseAudio(assetId);
    } else if (message.action === 'stop') {
        const element = document.getElementById(`asset-${assetId}`);
        if (element) {
            element.pause();
            element.currentTime = 0;
        }
    }
}

function handleAudioAutoplay(state) {
    if (!state.audio_assets) {
        return;
    }
    for (const asset of state.audio_assets) {
        if (asset.autoplay) {
            playAudio(asset.id);
        }
    }
}
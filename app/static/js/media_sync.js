function mediaElement(assetId) {
    return document.getElementById(`asset-${assetId}`);
}

function stopAllMedia() {
    document.querySelectorAll('.slide-audio, .slide-video').forEach((element) => {
        element.pause();
        element.currentTime = 0;
    });
}

function playMedia(assetId) {
    const element = mediaElement(assetId);
    if (element) {
        element.play().catch(() => {});
    }
}

function pauseMedia(assetId) {
    const element = mediaElement(assetId);
    if (element) {
        element.pause();
    }
}

function stopMedia(assetId) {
    const element = mediaElement(assetId);
    if (element) {
        element.pause();
        element.currentTime = 0;
    }
}

function handleMediaControl(message) {
    const assetId = message.asset_id;
    if (message.action === 'play') {
        playMedia(assetId);
    } else if (message.action === 'pause') {
        pauseMedia(assetId);
    } else if (message.action === 'stop') {
        stopMedia(assetId);
    }
}

function handleMediaAutoplay(state) {
    const assets = state.playback_assets || state.audio_assets || [];
    for (const asset of assets) {
        if (asset.autoplay) {
            playMedia(asset.id);
        }
    }
}

// Backward-compatible aliases
const stopAllAudio = stopAllMedia;
const handleAudioControl = handleMediaControl;
const handleAudioAutoplay = handleMediaAutoplay;
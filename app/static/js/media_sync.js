function mediaElement(assetId) {
    return document.getElementById(`asset-${assetId}`);
}

const SILENT_AUDIO_WAV =
    'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';

let mediaPlaybackUnlocked = false;
let mediaPlaybackRequiresGesture = false;
const pendingPlayAssetIds = new Set();
let onPlaybackBlocked = null;
let onPlaybackUnlocked = null;
let onPlaybackRequiresGesture = null;

function setMediaPlaybackBlockedHandler(handler) {
    onPlaybackBlocked = handler;
}

function notifyPlaybackBlocked(assetId) {
    pendingPlayAssetIds.add(assetId);
    if (onPlaybackBlocked) {
        onPlaybackBlocked(assetId);
    }
}

function unlockMediaPlayback() {
    if (mediaPlaybackUnlocked) {
        return;
    }
    mediaPlaybackUnlocked = true;
    if (onPlaybackUnlocked) {
        onPlaybackUnlocked();
    }
    const pending = [...pendingPlayAssetIds];
    pendingPlayAssetIds.clear();
    for (const assetId of pending) {
        playMediaImmediate(assetId);
    }
}

async function probeMediaPlaybackAllowed() {
    const probe = new Audio(SILENT_AUDIO_WAV);
    probe.volume = 0;
    try {
        await probe.play();
        probe.pause();
        return true;
    } catch {
        return false;
    }
}

async function initMediaPlaybackUnlock(options = {}) {
    onPlaybackUnlocked = options.onUnlocked || null;
    onPlaybackRequiresGesture = options.onRequiresGesture || null;

    if (await probeMediaPlaybackAllowed()) {
        unlockMediaPlayback();
        return;
    }

    mediaPlaybackRequiresGesture = true;
    if (onPlaybackRequiresGesture) {
        onPlaybackRequiresGesture();
    }

    const unlock = () => unlockMediaPlayback();
    document.addEventListener('pointerdown', unlock, { once: true, capture: true });
    document.addEventListener('keydown', unlock, { once: true, capture: true });
}

function isMediaPlaybackUnlocked() {
    return mediaPlaybackUnlocked;
}

function mediaPlaybackNeedsGesture() {
    return mediaPlaybackRequiresGesture && !mediaPlaybackUnlocked;
}

function stopAllMedia() {
    pendingPlayAssetIds.clear();
    document.querySelectorAll('.slide-audio, .slide-video').forEach((element) => {
        element.pause();
        element.currentTime = 0;
    });
}

function playMediaImmediate(assetId) {
    const element = mediaElement(assetId);
    if (!element) {
        return Promise.resolve(false);
    }
    element.currentTime = 0;
    return element.play()
        .then(() => true)
        .catch((error) => {
            if (error.name === 'NotAllowedError') {
                notifyPlaybackBlocked(assetId);
            }
            return false;
        });
}

function playMedia(assetId) {
    if (!mediaPlaybackUnlocked) {
        notifyPlaybackBlocked(assetId);
        return Promise.resolve(false);
    }
    return playMediaImmediate(assetId);
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
    pendingPlayAssetIds.delete(assetId);
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
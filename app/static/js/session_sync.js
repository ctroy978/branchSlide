/**
 * Live session sync with WebSocket reconnect and REST state recovery.
 */
function createSessionSync(options) {
    const {
        joinCode,
        graphSlug,
        sessionId,
        syncBaseUrl,
        onState,
        onStatus,
        onFatalError,
    } = options;

    const apiUrl = joinCode
        ? `/api/${joinCode}`
        : `/api/g/${graphSlug}/sessions/${sessionId}`;
    let ws = null;
    let reconnectAttempt = 0;
    let reconnectTimer = null;
    let intentionalClose = false;

    function wsOrigin() {
        if (syncBaseUrl) {
            const url = new URL(syncBaseUrl);
            url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
            return url.origin;
        }
        const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
        return `${protocol}://${location.host}`;
    }

    function wsUrl() {
        const path = joinCode
            ? `/ws/${joinCode}`
            : `/ws/g/${graphSlug}/sessions/${sessionId}`;
        return `${wsOrigin()}${path}`;
    }

    async function fetchState() {
        let response;
        try {
            response = await fetch(apiUrl);
        } catch {
            throw new Error('server_unreachable');
        }
        if (response.status === 404) {
            throw new Error('session_not_found');
        }
        if (!response.ok) {
            throw new Error('server_unreachable');
        }
        return response.json();
    }

    function clearReconnectTimer() {
        if (reconnectTimer !== null) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
    }

    function scheduleReconnect() {
        clearReconnectTimer();
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000);
        reconnectAttempt += 1;
        onStatus('reconnecting', { attempt: reconnectAttempt, delayMs: delay });

        reconnectTimer = setTimeout(async () => {
            try {
                const state = await fetchState();
                onState(state);
                connect();
            } catch (error) {
                if (error.message === 'session_not_found') {
                    onFatalError('session_not_found');
                    return;
                }
                onStatus('server_unreachable', { attempt: reconnectAttempt });
                scheduleReconnect();
            }
        }, delay);
    }

    function connect() {
        if (intentionalClose) {
            return;
        }

        ws = new WebSocket(wsUrl());

        ws.onopen = () => {
            reconnectAttempt = 0;
            onStatus('live');
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'node_changed' && msg.state) {
                onState(msg.state);
            } else if (msg.type === 'audio_control') {
                handleAudioControl(msg);
            }
        };

        ws.onclose = (event) => {
            if (intentionalClose) {
                return;
            }
            if (event.code === 4404) {
                onFatalError('session_not_found');
                return;
            }
            scheduleReconnect();
        };

        ws.onerror = () => {
            // onclose handles reconnect
        };
    }

    return {
        async start() {
            onStatus('connecting');
            try {
                const state = await fetchState();
                onState(state);
                connect();
            } catch (error) {
                if (error.message === 'session_not_found') {
                    onFatalError('session_not_found');
                    return;
                }
                onStatus('server_unreachable');
                scheduleReconnect();
            }
        },
        stop() {
            intentionalClose = true;
            clearReconnectTimer();
            if (ws) {
                ws.close();
                ws = null;
            }
        },
    };
}
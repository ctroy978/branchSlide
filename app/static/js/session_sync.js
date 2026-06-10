/**
 * Live session sync with WebSocket reconnect and REST state recovery.
 */
function createSessionSync(options) {
    const {
        joinCode,
        graphSlug,
        sessionId,
        syncBaseUrl,
        pollIntervalMs = 0,
        onState,
        onStatus,
        onFatalError,
    } = options;

    const syncRoot = (syncBaseUrl || '').replace(/\/$/, '');

    function stateApiUrl() {
        if (joinCode) {
            return syncRoot
                ? `${syncRoot}/api/join/${joinCode}`
                : `/api/${joinCode}`;
        }
        return syncRoot
            ? `${syncRoot}/api/g/${graphSlug}/sessions/${sessionId}`
            : `/api/g/${graphSlug}/sessions/${sessionId}`;
    }

    let ws = null;
    let reconnectAttempt = 0;
    let reconnectTimer = null;
    let pollTimer = null;
    let intentionalClose = false;
    let hasReceivedState = false;

    function wsOrigin() {
        if (syncRoot) {
            const url = new URL(syncRoot);
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
            response = await fetch(stateApiUrl());
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

    function deliverState(state) {
        hasReceivedState = true;
        onState(state);
    }

    function clearReconnectTimer() {
        if (reconnectTimer !== null) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
    }

    function clearPollTimer() {
        if (pollTimer !== null) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function startPolling() {
        if (!pollIntervalMs || pollTimer !== null) {
            return;
        }
        pollTimer = setInterval(async () => {
            try {
                deliverState(await fetchState());
            } catch (error) {
                if (error.message === 'session_not_found') {
                    clearPollTimer();
                    onFatalError('session_not_found');
                }
            }
        }, pollIntervalMs);
    }

    function scheduleReconnect() {
        clearReconnectTimer();
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000);
        reconnectAttempt += 1;
        onStatus('reconnecting', { attempt: reconnectAttempt, delayMs: delay });

        reconnectTimer = setTimeout(async () => {
            try {
                deliverState(await fetchState());
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
                deliverState(msg.state);
            } else if (msg.type === 'media_control' || msg.type === 'audio_control') {
                handleMediaControl(msg);
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
            onStatus('reconnecting');
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
                deliverState(await fetchState());
                connect();
                startPolling();
            } catch (error) {
                if (error.message === 'session_not_found') {
                    onFatalError('session_not_found');
                    return;
                }
                onStatus('server_unreachable');
                scheduleReconnect();
                startPolling();
            }
        },
        stop() {
            intentionalClose = true;
            clearReconnectTimer();
            clearPollTimer();
            if (ws) {
                ws.close();
                ws = null;
            }
        },
        hasReceivedState: () => hasReceivedState,
    };
}
const API_BASE = window.__V8_API_BASE__ || '/api/v8';

async function fetchAPI(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (e) {
        console.warn('V8 API unavailable:', e.message);
        return null;
    }
}

async function fetchHealth() {
    return fetchAPI('/health');
}

async function fetchRecords(table, limit = 20) {
    return fetchAPI(`/records/${table}?limit=${limit}`);
}

async function fetchMemories(limit = 20) {
    return fetchAPI(`/memories?limit=${limit}`);
}

function isOffline() {
    return !window.__V8_HAS_API__;
}

// Privacy-Preserving Clinical Data Gateway - Full-Stack Application Logic
// NDPA 2023 Compliant | MIVA Open University

const API_BASE = '/api/v1';

let state = {
    token: localStorage.getItem('gateway_token') || null,
    user: JSON.parse(localStorage.getItem('gateway_user')) || null,
    activeTab: 'overview',
    charts: {
        phq9: null,
        diagnosis: null
    }
};

// -----------------------------------------------------------------------------
// 1. Initial Application Setup
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    if (state.token && state.user) {
        hideLoginModal();
        updateUserHeader();
        enforceRolePermissions();
        loadDashboardData();
    } else {
        showLoginModal();
    }
});

// -----------------------------------------------------------------------------
// 2. Authentication & Role Enforcement
// -----------------------------------------------------------------------------
function showLoginModal() {
    document.getElementById('login-modal').style.display = 'flex';
}

function hideLoginModal() {
    document.getElementById('login-modal').style.display = 'none';
}

function quickLogin(username, password) {
    document.getElementById('login-username').value = username;
    document.getElementById('login-password').value = password;
    handleLoginSubmit(new Event('submit'));
}

async function handleLoginSubmit(event) {
    event?.preventDefault();
    const u = document.getElementById('login-username').value;
    const p = document.getElementById('login-password').value;

    try {
        const res = await fetch(`${API_BASE}/auth/login_json`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Authentication failed');
        }

        const data = await res.json();
        state.token = data.access_token;
        state.user = { username: data.username, role: data.role };

        localStorage.setItem('gateway_token', state.token);
        localStorage.setItem('gateway_user', JSON.stringify(state.user));

        showToast(`Authenticated successfully as ${state.user.username} (${state.user.role})`, 'success');
        hideLoginModal();
        updateUserHeader();
        enforceRolePermissions();
        switchTab('overview');
        loadDashboardData();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('gateway_token');
    localStorage.removeItem('gateway_user');
    showToast('Signed out of gateway', 'info');
    showLoginModal();
}

function updateUserHeader() {
    if (!state.user) return;
    document.getElementById('user-display-name').textContent = state.user.username;
    const badge = document.getElementById('user-role-badge');
    badge.textContent = state.user.role.toUpperCase();
    badge.className = `role-pill role-${state.user.role}`;
}

function enforceRolePermissions() {
    if (!state.user) return;
    const role = state.user.role;

    const tabConfig = {
        admin: ['overview', 'ingest', 'analytics', 'vault', 'audit'],
        clinician: ['overview', 'ingest', 'analytics'],
        researcher: ['overview', 'analytics'],
        data_officer: ['overview', 'analytics', 'vault', 'audit']
    };

    const allowed = tabConfig[role] || ['overview'];

    ['overview', 'ingest', 'analytics', 'vault', 'audit'].forEach(t => {
        const btn = document.getElementById(`tab-${t}-btn`);
        if (btn) {
            if (allowed.includes(t)) {
                btn.classList.remove('hidden');
            } else {
                btn.classList.add('hidden');
            }
        }
    });

    if (!allowed.includes(state.activeTab)) {
        switchTab(allowed[0]);
    }
}

// -----------------------------------------------------------------------------
// 3. Tab Switching Navigation
// -----------------------------------------------------------------------------
function switchTab(tabName) {
    state.activeTab = tabName;

    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    const btn = document.getElementById(`tab-${tabName}-btn`);
    const content = document.getElementById(`tab-${tabName}`);

    if (btn) btn.classList.add('active');
    if (content) content.classList.add('active');

    // Trigger tab specific data load
    if (tabName === 'overview') loadOverviewSummary();
    if (tabName === 'analytics') loadAnalyticsData();
    if (tabName === 'vault') loadVaultData();
    if (tabName === 'audit') loadAuditData();
}

// Helper fetch with Auth header
async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    options.headers['Authorization'] = `Bearer ${state.token}`;
    const res = await fetch(url, options);
    if (res.status === 401) {
        showToast('Session expired. Please log in again.', 'error');
        logout();
        throw new Error('Unauthorized');
    }
    if (res.status === 403) {
        showToast('Access Forbidden: Your role lacks permission for this action.', 'error');
        throw new Error('Forbidden');
    }
    return res;
}

// -----------------------------------------------------------------------------
// 4. Data Loaders & Renderers
// -----------------------------------------------------------------------------
async function loadDashboardData() {
    await loadOverviewSummary();
}

async function loadOverviewSummary() {
    try {
        const res = await authFetch(`${API_BASE}/analytics/summary`);
        const data = await res.json();
        const s = data.summary;

        document.getElementById('metric-total-records').textContent = s.total_records.toLocaleString();
        document.getElementById('metric-avg-phq9').textContent = s.avg_phq9_score.toFixed(1);

        renderCharts(s);
    } catch (e) {
        console.warn('Overview summary fetch error:', e);
    }
}

function renderCharts(summary) {
    // 1. PHQ-9 Severity Chart
    const ctxPhq9 = document.getElementById('phq9Chart')?.getContext('2d');
    if (ctxPhq9) {
        if (state.charts.phq9) state.charts.phq9.destroy();
        state.charts.phq9 = new Chart(ctxPhq9, {
            type: 'bar',
            data: {
                labels: Object.keys(summary.phq9_categories),
                datasets: [{
                    label: 'Patient Count',
                    data: Object.values(summary.phq9_categories),
                    backgroundColor: ['#38bdf8', '#34d399', '#fbfbfb', '#fbbf24', '#f43f5e'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }

    // 2. Diagnosis Chart
    const ctxDiag = document.getElementById('diagnosisChart')?.getContext('2d');
    if (ctxDiag) {
        if (state.charts.diagnosis) state.charts.diagnosis.destroy();
        state.charts.diagnosis = new Chart(ctxDiag, {
            type: 'doughnut',
            data: {
                labels: Object.keys(summary.diagnosis_counts),
                datasets: [{
                    data: Object.values(summary.diagnosis_counts),
                    backgroundColor: ['#6366f1', '#a855f7', '#ec4899', '#14b8a6', '#f59e0b', '#10b981'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 } } } }
            }
        });
    }
}

async function loadAnalyticsData() {
    try {
        const res = await authFetch(`${API_BASE}/query/analytics?limit=100`);
        const result = await res.json();
        const tbody = document.getElementById('analytics-table-body');

        if (!result.data || result.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No scrubbed records found. Use the Clinical Ingest or Synthetic Seed feature to generate records.</td></tr>`;
            return;
        }

        tbody.innerHTML = result.data.map(r => {
            const scrubbedFormatted = r.scrubbed_clinical_notes
                .replace(/\[NAME\]/g, `<span class="tag-redacted">[NAME]</span>`)
                .replace(/\[LOCATION\]/g, `<span class="tag-redacted">[LOCATION]</span>`)
                .replace(/\[CONTACT\]/g, `<span class="tag-redacted">[CONTACT]</span>`)
                .replace(/\[FACILITY\]/g, `<span class="tag-redacted">[FACILITY]</span>`);

            return `
                <tr>
                    <td class="font-mono" style="color: var(--primary);">${r.patient_pseudonym_id.substring(0, 16)}...</td>
                    <td>${r.age} yrs / ${r.gender}</td>
                    <td>${r.location}</td>
                    <td><span class="status-chip ${r.phq9_score > 14 ? 'status-danger' : r.phq9_score > 9 ? 'status-warning' : 'status-success'}">${r.phq9_score}</span></td>
                    <td>${r.diagnosis}</td>
                    <td style="line-height: 1.5;">${scrubbedFormatted}</td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed to load analytics:', e);
    }
}

async function loadVaultData() {
    try {
        const res = await authFetch(`${API_BASE}/query/vault?limit=100`);
        const result = await res.json();
        const tbody = document.getElementById('vault-table-body');

        if (!result.data || result.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No vault records found.</td></tr>`;
            return;
        }

        tbody.innerHTML = result.data.map(r => `
            <tr>
                <td class="font-mono">${r.patient_pseudonym_id.substring(0, 12)}...</td>
                <td><span class="tag-encrypted">${r.encrypted_name.substring(0, 20)}...</span></td>
                <td><span class="tag-encrypted">${r.encrypted_contact.substring(0, 20)}...</span></td>
                <td>${r.age} yrs, ${r.gender} (${r.location})</td>
                <td><span class="status-chip status-warning">${r.phq9_score}</span></td>
                <td>${r.diagnosis}</td>
                <td class="raw-notes-cell">${r.raw_clinical_notes}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Failed to load raw vault:', e);
    }
}

async function loadAuditData() {
    try {
        const res = await authFetch(`${API_BASE}/audit?limit=100`);
        const result = await res.json();
        const tbody = document.getElementById('audit-table-body');

        if (!result.audit_logs || result.audit_logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No audit logs found.</td></tr>`;
            return;
        }

        tbody.innerHTML = result.audit_logs.map(l => `
            <tr>
                <td class="font-mono" style="color: var(--text-dim);">${l.timestamp.substring(0, 19).replace('T', ' ')}</td>
                <td><span class="font-mono" style="color: var(--primary);">${l.user_id}</span> (${l.user_role})</td>
                <td><span class="status-chip ${l.action_type === 'INGESTION' ? 'status-success' : 'status-warning'}">${l.action_type}</span></td>
                <td class="font-mono">${l.target_table}</td>
                <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${l.query_string}</td>
                <td class="font-mono">${l.execution_time_ms.toFixed(2)} ms</td>
                <td><span class="status-chip status-success">SUCCESS</span></td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Failed to load audit trail:', e);
    }
}

// -----------------------------------------------------------------------------
// 5. Ingestion & Synthetic Data Seeding
// -----------------------------------------------------------------------------
async function handleIngestSubmit(event) {
    event.preventDefault();

    const payload = {
        patient_id: document.getElementById('ingest-patient-id').value,
        pii: {
            patient_name: document.getElementById('ingest-patient-name').value,
            contact_info: document.getElementById('ingest-contact').value
        },
        demographics: {
            age: parseInt(document.getElementById('ingest-age').value),
            gender: document.getElementById('ingest-gender').value,
            location: document.getElementById('ingest-location').value
        },
        journey_timeline: [{
            timestamp: new Date().toISOString(),
            phq9_score: parseInt(document.getElementById('ingest-phq9').value),
            clinical_notes: document.getElementById('ingest-notes').value,
            diagnosis: document.getElementById('ingest-diagnosis').value,
            treatment_plan: [{ type: 'Medication', name: 'Sertraline', dosage: '50mg' }]
        }]
    };

    try {
        const res = await authFetch(`${API_BASE}/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        showToast(`Record ingested & scrubbed! Pseudonym: ${data.patient_pseudonym_id.substring(0, 12)}...`, 'success');
        switchTab('analytics');
    } catch (e) {
        showToast(`Ingestion failed: ${e.message}`, 'error');
    }
}

async function triggerSyntheticSeed() {
    const select = document.getElementById('seed-count-select');
    const count = select ? parseInt(select.value) || 50 : 50;

    try {
        showToast(`Generating ${count.toLocaleString()} synthetic patients (1-3 visits each)...`, 'info');
        const res = await authFetch(`${API_BASE}/simulator/seed?count=${count}`, { method: 'POST' });
        const data = await res.json();
        showToast(`Seeded ${data.records_generated.toLocaleString()} patients (${data.analytics_scrubbed_inserted.toLocaleString()} visit records) into RAW_VAULT & ANALYTICS_SCRUBBED!`, 'success');
        loadOverviewSummary();
        if (state.activeTab === 'analytics') loadAnalyticsData();
    } catch (e) {
        showToast(`Seeding failed: ${e.message}`, 'error');
    }
}


// -----------------------------------------------------------------------------
// 6. UI Toast Alerts
// -----------------------------------------------------------------------------
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>[${type.toUpperCase()}]</span> ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

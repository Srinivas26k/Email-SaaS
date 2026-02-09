// Enterprise Outreach Dashboard - Multi-Page Application

const API_BASE = '';
let emailChart = null;
let statusChart = null;
let timelineChart = null;
let availableColumns = [];
let currentFocusField = null;

// Current state
let currentPage = 'dashboard';
let currentLeadsFilter = 'all';
let currentLeadsPage = 1;
let currentLeadsSort = { by: 'id', order: 'desc' };
let selectedLeadIds = [];
let currentLogsPage = 1;
let logsSearchTimeout = null;
let analyticsDateFrom = null;
let analyticsDateTo = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    loadMetrics();
    loadDashboardLogs();
    loadTemplates();
    loadColumns();

    // Auto-refresh
    setInterval(loadMetrics, 5000);
    setInterval(() => {
        if (currentPage === 'dashboard') loadDashboardLogs();
    }, 10000);

    // Track focused field for variable insertion
    document.addEventListener('focusin', (e) => {
        if (e.target.classList.contains('input-field') ||
            e.target.classList.contains('textarea-field')) {
            currentFocusField = e.target;
        }
    });

    // Setup drag and drop
    setupDragDrop();

    // Hash navigation
    const hash = window.location.hash.slice(1) || 'dashboard';
    navigateTo(hash);
    if (typeof lucide !== 'undefined') lucide.createIcons();
});

// ============ NAVIGATION ============

function navigateTo(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    // Remove active from nav items
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    // Show selected page
    const pageElement = document.getElementById(`${page}-page`);
    if (pageElement) {
        pageElement.classList.add('active');
        currentPage = page;

        // Update nav
        document.querySelector(`a[href="#${page}"]`)?.classList.add('active');

        // Update URL
        window.location.hash = page;

        // Load page-specific data
        loadPageData(page);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

function loadPageData(page) {
    switch (page) {
        case 'dashboard':
            loadDashboardLogs();
            break;
        case 'leads':
            loadLeads();
            break;
        case 'analytics':
            setDefaultAnalyticsDates();
            loadAnalytics();
            break;
        case 'reports':
            break;
        case 'logs':
            loadLogs();
            break;
        case 'templates':
            loadColumns();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// ============ CHARTS ============

function initCharts() {
    // Email timeline chart (dashboard/analytics)
    const ctx1 = document.getElementById('emailChart');
    if (ctx1) {
        emailChart = new Chart(ctx1.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Emails Sent',
                    data: [],
                    borderColor: '#1976D2',
                    backgroundColor: 'rgba(25, 118, 210, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } }
            }
        });
    }

    // Timeline chart for analytics
    const ctx2 = document.getElementById('timelineChart');
    if (ctx2) {
        timelineChart = new Chart(ctx2.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Sent',
                    data: [],
                    borderColor: '#1976D2',
                    backgroundColor: 'rgba(25, 118, 210, 0.1)',
                    fill: true
                }, {
                    label: 'Replied',
                    data: [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });
    }

    // Status pie chart
    const ctx3 = document.getElementById('statusChart');
    if (ctx3) {
        statusChart = new Chart(ctx3.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'Sent', 'Replied', 'Failed'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#FF9800', '#1976D2', '#4CAF50', '#F44336']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });
    }
}

// ============ DASHBOARD ============

async function loadMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/metrics`);
        const data = await response.json().catch(() => ({}));
        const sent = data.sent_today ?? 0;
        const limit = data.daily_limit || 500;
        const replies = data.replies ?? 0;
        const failed = data.failed ?? 0;
        const status = data.campaign_status || 'STOPPED';

        document.getElementById('sentToday').textContent = `${sent} / ${limit}`;
        document.getElementById('replies').textContent = replies;
        document.getElementById('failed').textContent = failed;
        const repliedEl = document.getElementById('repliedCount');
        if (repliedEl) repliedEl.textContent = replies;

        const statusBadge = document.getElementById('campaignStatus');
        if (statusBadge) {
            statusBadge.textContent = status;
            statusBadge.style.backgroundColor = getStatusBGColor(status);
            statusBadge.style.color = getStatusTextColor(status);
        }

        const percentage = limit > 0 ? (sent / limit) * 100 : 0;
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        if (progressFill) progressFill.style.width = `${percentage}%`;
        if (progressPercent) progressPercent.textContent = `${Math.round(percentage)}%`;

    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

async function loadDashboardLogs() {
    try {
        const response = await fetch(`${API_BASE}/api/logs?page=1&limit=10`);
        const data = await response.json().catch(() => ({}));
        const container = document.getElementById('dashboardLogsContainer');
        if (!container) return;
        if (data.logs && data.logs.length > 0) {
            container.innerHTML = data.logs.map(log => `
                <div class="log-entry">
                    <span class="log-event">${escapeHtml(log.event)}</span>
                    <span class="log-timestamp">${formatTimeAgo(log.timestamp)}</span>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="no-data">No activity yet</p>';
        }
    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

// Campaign controls
async function startCampaign() {
    try {
        const response = await fetch(`${API_BASE}/api/campaign/start`, { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            showNotification(data.detail || 'Failed to start campaign', 'error');
            return;
        }
        showNotification(data.message || 'Campaign started', 'success');
        loadMetrics();
    } catch (error) {
        showNotification('Failed to start campaign', 'error');
    }
}

async function pauseCampaign() {
    try {
        const response = await fetch(`${API_BASE}/api/campaign/pause`, { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            showNotification(data.detail || 'Failed to pause campaign', 'error');
            return;
        }
        showNotification(data.message || 'Campaign paused', 'success');
        loadMetrics();
    } catch (error) {
        showNotification('Failed to pause campaign', 'error');
    }
}

async function stopCampaign() {
    try {
        const response = await fetch(`${API_BASE}/api/campaign/stop`, { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            showNotification(data.detail || 'Failed to stop campaign', 'error');
            return;
        }
        showNotification(data.message || 'Campaign stopped', 'success');
        loadMetrics();
    } catch (error) {
        showNotification('Failed to stop campaign', 'error');
    }
}

// Upload
async function uploadLeads() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];

    console.log('uploadLeads called, file:', file);

    if (!file) {
        console.log('No file selected, opening file picker');
        // If no file selected, open the file picker
        fileInput.click();
        return;
    }

    // Validate file type
    if (!file.name.endsWith('.csv')) {
        showNotification('Please select a CSV file', 'error');
        return;
    }

    console.log('Uploading file:', file.name, 'Size:', file.size, 'bytes');

    const formData = new FormData();
    formData.append('file', file);

    try {
        showNotification('Uploading...', 'info');
        
        const response = await fetch(`${API_BASE}/api/upload-leads`, {
            method: 'POST',
            body: formData
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Upload error:', errorText);
            throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Upload response:', data);

        if (data.success) {
            showNotification(data.message, 'success');
            fileInput.value = '';
            loadMetrics();

            if (data.columns && data.columns.length > 0) {
                availableColumns = data.columns.filter(col => col !== 'email');
                displayColumns(availableColumns);
            }
        } else {
            showNotification('Upload failed: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Upload failed: ' + error.message, 'error');
    }
}

// ============ LEADS MANAGEMENT ============

async function loadLeads() {
    try {
        const params = new URLSearchParams({
            page: currentLeadsPage,
            limit: 50,
            status: currentLeadsFilter,
            sort_by: currentLeadsSort.by,
            sort_order: currentLeadsSort.order
        });

        const search = document.getElementById('leadSearch')?.value;
        if (search) params.append('search', search);

        const response = await fetch(`${API_BASE}/api/leads?${params}`);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            document.getElementById('leadsTableBody').innerHTML =
                '<tr><td colspan="8" class="no-data">Failed to load leads</td></tr>';
            return;
        }
        renderLeadsTable(data.leads || []);
        renderPagination(data.page ?? 1, data.pages ?? 1);

    } catch (error) {
        console.error('Failed to load leads:', error);
        document.getElementById('leadsTableBody').innerHTML =
            '<tr><td colspan="8" class="no-data">Failed to load leads</td></tr>';
    }
}

function renderLeadsTable(leads) {
    const tbody = document.getElementById('leadsTableBody');

    if (!leads || leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No leads found</td></tr>';
        return;
    }

    tbody.innerHTML = leads.map(lead => {
        const d = lead.data || {};
        return `
        <tr>
            <td><input type="checkbox" class="lead-checkbox" value="${lead.id}"></td>
            <td>${escapeHtml(lead.email)}</td>
            <td>${escapeHtml(d.name || d.first_name || '-')}</td>
            <td>${escapeHtml(d.company || '-')}</td>
            <td><span class="status-pill status-${lead.status.toLowerCase()}">${lead.status}</span></td>
            <td>${lead.last_sent_at ? formatDate(lead.last_sent_at) : '-'}</td>
            <td>${lead.followup_count}</td>
            <td>
                <button class="action-btn action-delete" onclick="deleteLead(${lead.id})">Delete</button>
            </td>
        </tr>
    `;
    }).join('');
}

function renderPagination(current, total) {
    const container = document.getElementById('leadsPagination');
    if (total <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    if (current > 1) {
        html += `<button class="page-btn" onclick="goToPage(${current - 1})">← Prev</button>`;
    }

    for (let i = 1; i <= Math.min(total, 5); i++) {
        const active = i === current ? 'active' : '';
        html += `<button class="page-btn ${active}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (current < total) {
        html += `<button class="page-btn" onclick="goToPage(${current + 1})">Next →</button>`;
    }

    container.innerHTML = html;
}

function filterLeads(status) {
    currentLeadsFilter = status;
    currentLeadsPage = 1;

    const tabs = document.querySelectorAll('.filter-tab');
    tabs.forEach(t => t.classList.remove('active'));
    const order = ['all', 'pending', 'sent', 'replied', 'failed'];
    const idx = order.indexOf(status);
    if (idx >= 0 && tabs[idx]) tabs[idx].classList.add('active');
    if (event && event.target) event.target.classList.add('active');

    loadLeads();
}

function searchLeads() {
    currentLeadsPage = 1;
    loadLeads();
}

function sortLeads(column) {
    if (currentLeadsSort.by === column) {
        currentLeadsSort.order = currentLeadsSort.order === 'asc' ? 'desc' : 'asc';
    } else {
        currentLeadsSort.by = column;
        currentLeadsSort.order = 'desc';
    }
    loadLeads();
}

function goToPage(page) {
    currentLeadsPage = page;
    loadLeads();
}

async function deleteLead(id) {
    if (!confirm('Are you sure you want to delete this lead?')) return;

    try {
        const response = await fetch(`${API_BASE}/api/leads/${id}`, { method: 'DELETE' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            showNotification(data.detail || 'Failed to delete lead', 'error');
            return;
        }
        if (data.success) {
            showNotification('Lead deleted', 'success');
            loadLeads();
            loadMetrics();
        } else {
            showNotification('Failed to delete lead', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function toggleSelectAll() {
    const checked = document.getElementById('selectAll').checked;
    document.querySelectorAll('.lead-checkbox').forEach(cb => cb.checked = checked);
}

// ============ ANALYTICS ============

function setDefaultAnalyticsDates() {
    const to = new Date();
    const from = new Date();
    from.setDate(from.getDate() - 30);
    document.getElementById('analyticsDateFrom').value = from.toISOString().slice(0, 10);
    document.getElementById('analyticsDateTo').value = to.toISOString().slice(0, 10);
    analyticsDateFrom = from.toISOString().slice(0, 10);
    analyticsDateTo = to.toISOString().slice(0, 10);
}

function applyAnalyticsDateRange() {
    const fromEl = document.getElementById('analyticsDateFrom');
    const toEl = document.getElementById('analyticsDateTo');
    if (fromEl && toEl) {
        analyticsDateFrom = fromEl.value || null;
        analyticsDateTo = toEl.value || null;
        loadAnalytics();
    }
}

async function loadAnalytics() {
    try {
        let url = `${API_BASE}/api/analytics`;
        const params = [];
        if (analyticsDateFrom) params.push(`date_from=${encodeURIComponent(analyticsDateFrom)}`);
        if (analyticsDateTo) params.push(`date_to=${encodeURIComponent(analyticsDateTo)}`);
        if (params.length) url += '?' + params.join('&');
        const response = await fetch(url);
        const data = await response.json();

        // Update stats (guard against missing data)
        const totalEl = document.getElementById('analyticsTotal');
        const replyRateEl = document.getElementById('analyticsReplyRate');
        const failureRateEl = document.getElementById('analyticsFailureRate');
        if (totalEl) totalEl.textContent = data.total_leads ?? 0;
        if (replyRateEl) replyRateEl.textContent = `${data.reply_rate ?? 0}%`;
        if (failureRateEl) failureRateEl.textContent = `${data.failure_rate ?? 0}%`;

        // Update status chart
        const dist = data.status_distribution || {};
        if (statusChart) {
            statusChart.data.datasets[0].data = [
                dist.pending ?? 0,
                dist.sent ?? 0,
                dist.replied ?? 0,
                dist.failed ?? 0
            ];
            statusChart.update();
        }

        // Update timeline chart
        if (timelineChart && data.daily_stats && Array.isArray(data.daily_stats)) {
            timelineChart.data.labels = data.daily_stats.map(d => d.date);
            timelineChart.data.datasets[0].data = data.daily_stats.map(d => d.sent);
            timelineChart.data.datasets[1].data = data.daily_stats.map(d => d.replied);
            timelineChart.update();
        }

    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

// ============ REPORTS ============

async function previewReport() {
    try {
        const response = await fetch(`${API_BASE}/api/report/preview`);
        const data = await response.json();
        const card = document.getElementById('reportPreviewCard');
        const content = document.getElementById('reportPreviewContent');
        if (!card || !content) return;
        content.innerHTML = `
            <div class="report-preview-stats">
                <div class="rp-stat"><span class="rp-value">${data.today?.sent ?? 0}</span> Sent today</div>
                <div class="rp-stat"><span class="rp-value">${data.today?.replied ?? 0}</span> Replied today</div>
                <div class="rp-stat"><span class="rp-value">${data.overall?.reply_rate ?? 0}%</span> Reply rate</div>
                <div class="rp-stat"><span class="rp-value">${data.overall?.total_leads ?? 0}</span> Total leads</div>
            </div>
            <p class="report-preview-note">Daily report email uses the same data and is sent at 1 AM. Use "Send report now" to email it immediately.</p>
        `;
        card.style.display = 'block';
    } catch (error) {
        console.error('Failed to load report preview:', error);
        showNotification('Failed to load report preview', 'error');
    }
}

async function sendReportNow() {
    try {
        showNotification('Sending report...', 'info');
        const response = await fetch(`${API_BASE}/api/report/send`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            showNotification(data.message || 'Report sent', 'success');
        } else {
            showNotification(data.detail || 'Failed to send report', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

// ============ LOGS ============

function debounceSearchLogs() {
    if (logsSearchTimeout) clearTimeout(logsSearchTimeout);
    logsSearchTimeout = setTimeout(() => {
        currentLogsPage = 1;
        loadLogs();
    }, 300);
}

async function loadLogs() {
    try {
        const search = document.getElementById('logsSearch')?.value?.trim() || '';
        const params = new URLSearchParams({ page: currentLogsPage, limit: 50 });
        if (search) params.append('search', search);
        const response = await fetch(`${API_BASE}/api/logs?${params}`);
        const data = await response.json();

        const tbody = document.getElementById('logsTableBody');
        if (!data.logs || data.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="no-data">No logs found</td></tr>';
        } else {
            tbody.innerHTML = data.logs.map(log => `
                <tr>
                    <td class="log-time">${formatLogTime(log.timestamp)}</td>
                    <td class="log-email">${escapeHtml(log.email || '—')}</td>
                    <td class="log-event">${escapeHtml(log.event)}</td>
                </tr>
            `).join('');
        }

        document.getElementById('logsMeta').textContent = `Page ${data.page} of ${data.pages || 1} · ${data.total ?? 0} total`;
        renderLogsPagination(data.page, data.pages || 1);
    } catch (error) {
        console.error('Failed to load logs:', error);
        document.getElementById('logsTableBody').innerHTML = '<tr><td colspan="3" class="no-data">Failed to load logs</td></tr>';
    }
}

function formatLogTime(isoString) {
    const d = new Date(isoString);
    return d.toISOString().replace('T', ' ').slice(0, 19);
}

function renderLogsPagination(current, total) {
    const container = document.getElementById('logsPagination');
    if (!container || total <= 1) {
        if (container) container.innerHTML = '';
        return;
    }
    let html = '';
    if (current > 1) html += `<button class="page-btn" onclick="currentLogsPage=${current - 1}; loadLogs();">← Prev</button>`;
    for (let i = 1; i <= Math.min(total, 7); i++) {
        const active = i === current ? 'active' : '';
        html += `<button class="page-btn ${active}" onclick="currentLogsPage=${i}; loadLogs();">${i}</button>`;
    }
    if (current < total) html += `<button class="page-btn" onclick="currentLogsPage=${current + 1}; loadLogs();">Next →</button>`;
    container.innerHTML = html;
}

// ============ TEMPLATES ============

function displayColumns(columns) {
    const container = document.getElementById('variablesContainer');
    const fromCsvEl = document.getElementById('placeholdersFromCsv');
    const replyHintEl = document.getElementById('replyTemplateHint');

    if (!container) return;

    // Special variables always available (not from CSV)
    const specialVars = ['calendar_link', 'email'];
    const allVars = [...specialVars, ...(columns || [])];

    if (!columns || columns.length === 0) {
        container.innerHTML = '<p class="no-data">Upload a lead CSV on the Dashboard to see placeholders from your sheet.</p>';
        if (fromCsvEl) {
            fromCsvEl.textContent = '';
            fromCsvEl.style.display = 'none';
        }
        if (replyHintEl) {
            replyHintEl.textContent = 'Upload a lead CSV to see placeholders from your sheet. You can use {{calendar_link}}, {{email}}, and any column name from your CSV.';
        }
        // Still show special vars so they can use calendar_link and email
        const specialOnly = ['calendar_link', 'email'];
        container.innerHTML = '<p class="placeholder-sub">Always available:</p>' +
            specialOnly.map(col => `<button class="variable-tag" onclick="insertVariable('${col}')">{{${col}}}</button>`).join('') +
            '<p class="no-data" style="margin-top:0.75rem;">Upload a lead CSV to see placeholders from your sheet.</p>';
        ['initial', 'followup1', 'followup2', 'reply'].forEach(type => {
            const inlineContainer = document.getElementById(`${type}Variables`);
            if (inlineContainer) {
                inlineContainer.innerHTML = specialOnly.map(col =>
                    `<button class="inline-var" onclick="insertVariableInto('${type}Body', '${col}')">{{${col}}}</button>`
                ).join('');
            }
        });
        return;
    }

    // Show "From your lead sheet: col1, col2, ..."
    if (fromCsvEl) {
        fromCsvEl.textContent = 'From your lead sheet: ' + columns.map(c => '{{' + c + '}}').join(', ');
        fromCsvEl.style.display = 'block';
    }

    // Safe for attribute: escape quotes in column name
    const attr = (c) => String(c).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    container.innerHTML = allVars.map(col =>
        `<button class="variable-tag" onclick="insertVariable('${attr(col)}')" type="button">${escapeHtml('{{' + col + '}}')}</button>`
    ).join('');

    ['initial', 'followup1', 'followup2', 'reply'].forEach(type => {
        const inlineContainer = document.getElementById(`${type}Variables`);
        if (inlineContainer) {
            inlineContainer.innerHTML = allVars.map(col =>
                `<button class="inline-var" onclick="insertVariableInto('${type}Body', '${attr(col)}')" type="button">${escapeHtml('{{' + col + '}}')}</button>`
            ).join('');
        }
    });

    // Dynamic placeholder examples using their CSV columns
    const firstCol = columns[0] || 'first_name';
    const examplePlaceholder = 'e.g. Hi {{' + firstCol + '}}, ... Use the buttons above to insert placeholders from your lead sheet.';
    ['initialBody', 'followup1Body', 'followup2Body'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.placeholder = examplePlaceholder;
    });
    const replyBodyEl = document.getElementById('replyBody');
    if (replyBodyEl) replyBodyEl.placeholder = 'e.g. Hi {{' + firstCol + '}}, ... Use {{calendar_link}} for booking. Use the buttons above to insert.';

    const subjectPlaceholder = 'e.g. Quick question for {{' + firstCol + '}}';
    ['initialSubject', 'followup1Subject', 'followup2Subject', 'replySubject'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.placeholder = subjectPlaceholder;
    });

    if (replyHintEl) {
        replyHintEl.textContent = 'Placeholders from your lead sheet: ' + allVars.map(v => '{{' + v + '}}').join(', ');
    }
}

function insertVariable(columnName) {
    if (!currentFocusField) return;
    insertVariableInto(currentFocusField.id, columnName);
}

function insertVariableInto(fieldId, columnName) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    const variable = `{{${columnName}}}`;
    const start = field.selectionStart || 0;
    const end = field.selectionEnd || 0;
    const text = field.value;

    field.value = text.substring(0, start) + variable + text.substring(end);

    const newPos = start + variable.length;
    field.setSelectionRange(newPos, newPos);
    field.focus();
}

async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/api/templates`);
        const data = await response.json();

        if (data.templates) {
            if (data.templates.initial) {
                document.getElementById('initialSubject').value = data.templates.initial.subject;
                document.getElementById('initialBody').value = data.templates.initial.body;
            }
            if (data.templates.followup1) {
                document.getElementById('followup1Subject').value = data.templates.followup1.subject;
                document.getElementById('followup1Body').value = data.templates.followup1.body;
            }
            if (data.templates.followup2) {
                document.getElementById('followup2Subject').value = data.templates.followup2.subject;
                document.getElementById('followup2Body').value = data.templates.followup2.body;
            }
            if (data.templates.reply) {
                document.getElementById('replySubject').value = data.templates.reply.subject;
                document.getElementById('replyBody').value = data.templates.reply.body;
            } else {
                // Set default reply template
                document.getElementById('replySubject').value = "Let's schedule a call!";
                document.getElementById('replyBody').value = `Hi {{first_name}},

Thanks for your reply! I'd love to connect with you.

Please book a time that works best for you here:
{{calendar_link}}

Looking forward to our conversation!

Best regards`;
            }
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

async function saveTemplates() {
    const templates = {
        initial: {
            subject: document.getElementById('initialSubject').value,
            body: document.getElementById('initialBody').value
        },
        followup1: {
            subject: document.getElementById('followup1Subject').value,
            body: document.getElementById('followup1Body').value
        },
        followup2: {
            subject: document.getElementById('followup2Subject').value,
            body: document.getElementById('followup2Body').value
        },
        reply: {
            subject: document.getElementById('replySubject').value,
            body: document.getElementById('replyBody').value
        }
    };

    try {
        const response = await fetch(`${API_BASE}/api/templates/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(templates)
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Templates saved successfully!', 'success');
        } else {
            showNotification('Failed to save templates', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function loadColumns() {
    try {
        const response = await fetch(`${API_BASE}/api/columns`);
        const data = await response.json();

        if (data.columns && data.columns.length > 0) {
            availableColumns = data.columns.filter(col => col !== 'email');
            displayColumns(availableColumns);
        }
    } catch (error) {
        console.error('Failed to load columns:', error);
    }
}

// ============ SETTINGS ============

async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/settings`);
        const data = await response.json();

        const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ''; };
        set('settingsLicenseKey', data.license_key);
        set('settingsEmailQueueInterval', data.email_queue_interval_seconds);
        set('settingsReplyCheckInterval', data.reply_check_interval_seconds);
        set('settingsDailyLimit', data.daily_limit);
        set('settingsMinDelay', data.min_delay);
        set('settingsMaxDelay', data.max_delay);
        set('settingsPauseEvery', data.pause_every_n);
        set('settingsPauseMin', data.pause_min_minutes);
        set('settingsPauseMax', data.pause_max_minutes);
        set('settingsCalendarLink', data.calendar_link);

        renderEmailAccountsList(data.email_accounts || [], data.using_env_fallback === true);
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

function renderEmailAccountsList(accounts, usingEnvFallback) {
    const container = document.getElementById('emailAccountsList');
    if (!container) return;
    if (!accounts || accounts.length === 0) {
        const msg = usingEnvFallback
            ? 'No email accounts yet. Sending uses .env if configured. Add one below to manage and test.'
            : 'No email accounts yet. Add one below.';
        container.innerHTML = `<p class="no-data">${msg}</p>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
        return;
    }
    container.innerHTML = accounts.map(acc => `
        <div class="email-account-card" data-id="${acc.id}">
            <div class="acc-header">
                <strong>${escapeHtml(acc.label || acc.email)}</strong>
                <span class="acc-email">${escapeHtml(acc.email)}</span>
                ${acc.is_active ? '<span class="acc-badge active">Active</span>' : '<span class="acc-badge inactive">Inactive</span>'}
            </div>
            <div class="acc-details">
                SMTP ${acc.smtp_server}:${acc.smtp_port} · IMAP ${acc.imap_server}:${acc.imap_port}
                ${acc.sent_today !== undefined ? ` · Sent today: ${acc.sent_today}` : ''}
            </div>
            <div class="acc-actions">
                <button type="button" class="btn btn-secondary btn-sm" onclick="testAccountConnection(${acc.id}, this)">
                    <i data-lucide="plug" class="btn-icon" aria-hidden="true"></i> Test connection
                </button>
                <span class="test-result" id="testResult-${acc.id}"></span>
                <button type="button" class="btn btn-danger btn-sm" onclick="deleteEmailAccount(${acc.id})">
                    <i data-lucide="trash-2" class="btn-icon" aria-hidden="true"></i> Remove
                </button>
            </div>
        </div>
    `).join('');
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

async function testAccountConnection(accountId, btn) {
    if (accountId == null || accountId === undefined || accountId === 'null') {
        if (btn) btn.disabled = false;
        return;
    }
    const resultEl = document.getElementById(`testResult-${accountId}`);
    if (resultEl) { resultEl.textContent = 'Checking...'; resultEl.className = 'test-result pending'; }
    if (btn) btn.disabled = true;
    try {
        const response = await fetch(`${API_BASE}/api/email-accounts/${accountId}/test`, { method: 'POST' });
        const data = await response.json();
        const smtp = data.smtp || {};
        const imap = data.imap || {};
        const ok = smtp.ok && imap.ok;
        const msg = ok ? 'Connected' : [smtp.ok ? '' : `SMTP: ${smtp.message || 'Failed'}`, imap.ok ? '' : `IMAP: ${imap.message || 'Failed'}`].filter(Boolean).join('; ') || 'Connected';
        if (resultEl) {
            resultEl.textContent = msg;
            resultEl.className = 'test-result ' + (ok ? 'success' : 'error');
        }
    } catch (e) {
        if (resultEl) { resultEl.textContent = 'Request failed'; resultEl.className = 'test-result error'; }
    }
    if (btn) btn.disabled = false;
}

async function testNewAccountConnection() {
    const resultEl = document.getElementById('newAccountTestResult');
    const email = document.getElementById('newAccountEmail')?.value?.trim();
    const password = document.getElementById('newAccountPassword')?.value;
    if (!email || !password) { showNotification('Enter email and app password', 'error'); return; }
    if (resultEl) { resultEl.textContent = 'Checking...'; resultEl.className = 'test-result pending'; }
    try {
        const response = await fetch(`${API_BASE}/api/email-accounts/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                password,
                smtp_server: document.getElementById('newAccountSmtpServer')?.value || 'smtp.gmail.com',
                smtp_port: parseInt(document.getElementById('newAccountSmtpPort')?.value || '587', 10),
                imap_server: document.getElementById('newAccountImapServer')?.value || 'imap.gmail.com',
                imap_port: parseInt(document.getElementById('newAccountImapPort')?.value || '993', 10)
            })
        });
        const data = await response.json();
        const smtp = data.smtp || {};
        const imap = data.imap || {};
        const ok = smtp.ok && imap.ok;
        const msg = ok ? 'Connected' : [smtp.ok ? '' : `SMTP: ${smtp.message || 'Failed'}`, imap.ok ? '' : `IMAP: ${imap.message || 'Failed'}`].filter(Boolean).join('; ') || 'Connected';
        if (resultEl) {
            resultEl.textContent = msg;
            resultEl.className = 'test-result ' + (ok ? 'success' : 'error');
        }
    } catch (e) {
        if (resultEl) { resultEl.textContent = 'Request failed'; resultEl.className = 'test-result error'; }
    }
}

async function addEmailAccount() {
    const label = document.getElementById('newAccountLabel')?.value?.trim();
    const email = document.getElementById('newAccountEmail')?.value?.trim();
    const password = document.getElementById('newAccountPassword')?.value;
    if (!email || !password) { showNotification('Email and app password required', 'error'); return; }
    try {
        const response = await fetch(`${API_BASE}/api/email-accounts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                label: label || email,
                email,
                password,
                smtp_server: document.getElementById('newAccountSmtpServer')?.value || 'smtp.gmail.com',
                smtp_port: parseInt(document.getElementById('newAccountSmtpPort')?.value || '587', 10),
                imap_server: document.getElementById('newAccountImapServer')?.value || 'imap.gmail.com',
                imap_port: parseInt(document.getElementById('newAccountImapPort')?.value || '993', 10)
            })
        });
        const data = await response.json();
        if (data.success) {
            showNotification('Account added', 'success');
            document.getElementById('newAccountPassword').value = '';
            loadSettings();
        } else {
            showNotification(data.detail || 'Failed to add account', 'error');
        }
    } catch (e) {
        showNotification('Error: ' + e.message, 'error');
    }
}

async function deleteEmailAccount(accountId) {
    if (!confirm('Remove this email account? Leads sent from it will keep working.')) return;
    try {
        const response = await fetch(`${API_BASE}/api/email-accounts/${accountId}`, { method: 'DELETE' });
        const data = await response.json();
        if (data.success) { showNotification('Account removed', 'success'); loadSettings(); }
        else showNotification(data.detail || 'Failed', 'error');
    } catch (e) {
        showNotification('Error: ' + e.message, 'error');
    }
}

async function saveAppSettings(event) {
    if (event) event.preventDefault();
    try {
        const payload = {
            license_key: document.getElementById('settingsLicenseKey')?.value?.trim() || '',
            email_queue_interval_seconds: document.getElementById('settingsEmailQueueInterval')?.value?.trim() || '300',
            reply_check_interval_seconds: document.getElementById('settingsReplyCheckInterval')?.value?.trim() || '300',
            daily_email_limit: document.getElementById('settingsDailyLimit')?.value?.trim() || '500',
            min_delay_seconds: document.getElementById('settingsMinDelay')?.value?.trim() || '60',
            max_delay_seconds: document.getElementById('settingsMaxDelay')?.value?.trim() || '120',
            pause_every_n_emails: document.getElementById('settingsPauseEvery')?.value?.trim() || '20',
            pause_min_minutes: document.getElementById('settingsPauseMin')?.value?.trim() || '5',
            pause_max_minutes: document.getElementById('settingsPauseMax')?.value?.trim() || '8',
            calendar_link: document.getElementById('settingsCalendarLink')?.value?.trim() || ''
        };
        const response = await fetch(`${API_BASE}/api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (data.success) { showNotification('Settings saved', 'success'); }
        else showNotification(data.detail || 'Failed to save', 'error');
    } catch (e) {
        showNotification('Error: ' + e.message, 'error');
    }
    return false;
}

// ============ UTILITIES ============

function setupDragDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('csvFile');

    if (!uploadArea || !fileInput) {
        console.error('Upload area or file input not found!');
        return;
    }

    console.log('✓ Setting up drag and drop...');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '#1976D2';
            uploadArea.style.backgroundColor = '#f0f8ff';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '';
            uploadArea.style.backgroundColor = '';
        }, false);
    });

    // Handle dropped files
    uploadArea.addEventListener('drop', (e) => {
        console.log('📁 File dropped');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            console.log('File set:', files[0].name);
            
            // Show selected file
            const hint = document.getElementById('uploadHint');
            if (hint) {
                hint.textContent = `✓ Selected: ${files[0].name}`;
                hint.style.color = '#4CAF50';
                hint.style.fontWeight = 'bold';
            }
            
            uploadLeads();
        }
    }, false);

    // Click handler for entire upload area - opens file picker
    uploadArea.addEventListener('click', (e) => {
        console.log('📁 Upload area clicked - opening file picker');
        fileInput.click();
    });

    // File input change handler
    fileInput.addEventListener('change', () => {
        console.log('File input changed');
        if (fileInput.files.length > 0) {
            const fileName = fileInput.files[0].name;
            console.log('File selected:', fileName);
            
            // Show selected file name
            const hint = document.getElementById('uploadHint');
            if (hint) {
                hint.textContent = `✓ Selected: ${fileName}`;
                hint.style.color = '#4CAF50';
                hint.style.fontWeight = 'bold';
            }
            
            // Auto-upload after selection
            uploadLeads();
        }
    });
    
    console.log('✓ Drag and drop setup complete');
}

function getStatusBGColor(status) {
    const colors = {
        'RUNNING': '#d1fae5',
        'PAUSED': '#fef3c7',
        'STOPPED': '#fee2e2',
        'COMPLETED': '#e0e7ff'
    };
    return colors[status] || '#f1f5f9';
}

function getStatusTextColor(status) {
    const colors = {
        'RUNNING': '#047857',
        'PAUSED': '#b45309',
        'STOPPED': '#b91c1c',
        'COMPLETED': '#4338ca'
    };
    return colors[status] || '#475569';
}

function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTimeAgo(isoString) {
    const date = new Date(isoString);
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#F44336' : type === 'warning' ? '#FF9800' : '#2196F3'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        z-index: 10000;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

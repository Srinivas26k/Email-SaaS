// Dashboard JavaScript - API Integration and Real-time Updates

const API_BASE = '';
let emailChart = null;
let chartData = {
    labels: [],
    data: []
};
let availableColumns = [];
let currentFocusField = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    loadMetrics();
    loadLogs();
    loadTemplates();
    loadColumns();

    // Update every 5 seconds
    setInterval(loadMetrics, 5000);
    setInterval(loadLogs, 10000);

    // Track focused input for variable insertion
    document.addEventListener('focusin', (e) => {
        if (e.target.classList.contains('template-input') ||
            e.target.classList.contains('template-textarea')) {
            currentFocusField = e.target;
        }
    });
});

// Initialize Chart.js
function initChart() {
    const ctx = document.getElementById('emailChart').getContext('2d');
    emailChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Emails Sent',
                data: chartData.data,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a1a1aa'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a1a1aa'
                    }
                }
            }
        }
    });
}

// Load metrics from API
async function loadMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/metrics`);
        const data = await response.json();

        // Update metric cards
        document.getElementById('sentToday').textContent =
            `${data.sent_today} / ${data.daily_limit}`;
        document.getElementById('replies').textContent = data.replies;
        document.getElementById('failed').textContent = data.failed;

        // Update campaign status badge
        const statusBadge = document.getElementById('campaignStatus');
        statusBadge.textContent = data.campaign_status;
        statusBadge.style.backgroundColor = getStatusBGColor(data.campaign_status);
        statusBadge.style.color = getStatusTextColor(data.campaign_status);

        // Update progress bar
        const percentage = (data.sent_today / data.daily_limit) * 100;
        document.getElementById('progressFill').style.width = `${percentage}%`;
        document.getElementById('progressPercent').textContent = `${Math.round(percentage)}%`;

        // Update chart
        updateChart(data.sent_today);

    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

// Load logs from API
async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE}/api/logs?limit=50`);
        const data = await response.json();

        const logsContainer = document.getElementById('logsContainer');

        if (data.logs.length === 0) {
            logsContainer.innerHTML = '<p class="no-logs">No logs yet</p>';
            return;
        }

        logsContainer.innerHTML = data.logs.map(log => `
            <div class="log-entry">
                <span class="log-event">${escapeHtml(log.event)}</span>
                <span class="log-timestamp">${formatTimestamp(log.timestamp)}</span>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

// Update chart with new data
function updateChart(sentToday) {
    const now = new Date();
    const timeLabel = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;

    // Add new data point
    chartData.labels.push(timeLabel);
    chartData.data.push(sentToday);

    // Keep last 20 data points
    if (chartData.labels.length > 20) {
        chartData.labels.shift();
        chartData.data.shift();
    }

    // Update chart
    if (emailChart) {
        emailChart.data.labels = chartData.labels;
        emailChart.data.datasets[0].data = chartData.data;
        emailChart.update('none'); // Update without animation for performance
    }
}

// Campaign control functions
async function startCampaign() {
    try {
        const response = await fetch(`${API_BASE}/api/campaign/start`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showNotification('Campaign started!', 'success');
            loadMetrics();
        }
    } catch (error) {
        showNotification('Failed to start campaign', 'error');
        console.error(error);
    }
}

async function pauseCampaign() {
    try {
        const response = await fetch(`${API_BASE}/api/campaign/pause`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showNotification('Campaign paused', 'warning');
            loadMetrics();
        }
    } catch (error) {
        showNotification('Failed to pause campaign', 'error');
        console.error(error);
    }
}

async function stopCampaign() {
    try {
        const response = await fetch(`${API_BASE}/api/campaign/stop`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showNotification('Campaign stopped', 'error');
            loadMetrics();
        }
    } catch (error) {
        showNotification('Failed to stop campaign', 'error');
        console.error(error);
    }
}

// Upload leads
async function uploadLeads() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];

    if (!file) {
        showNotification('Please select a CSV file', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/api/upload-leads`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showNotification(data.message, 'success');
            fileInput.value = '';
            loadMetrics();

            // Display available columns
            if (data.columns && data.columns.length > 0) {
                availableColumns = data.columns.filter(col => col !== 'email');
                displayColumns(availableColumns);
                document.getElementById('templateSection').style.display = 'block';
            }
        } else {
            showNotification('Upload failed', 'error');
        }
    } catch (error) {
        showNotification('Upload failed: ' + error.message, 'error');
        console.error(error);
    }
}

// Display available columns
function displayColumns(columns) {
    const container = document.getElementById('columnsContainer');

    if (columns.length === 0) {
        container.innerHTML = '<p class="no-columns">No columns detected</p>';
        return;
    }

    container.innerHTML = columns.map(col =>
        `<button class="column-tag" onclick="insertVariable('${col}')">${col}</button>`
    ).join('');
}

// Insert variable into focused field
function insertVariable(columnName) {
    if (!currentFocusField) {
        // Try to find last focused field or default to initial body
        currentFocusField = document.getElementById('initialBody');
    }

    const variable = `{{${columnName}}}`;
    const start = currentFocusField.selectionStart;
    const end = currentFocusField.selectionEnd;
    const text = currentFocusField.value;

    currentFocusField.value = text.substring(0, start) + variable + text.substring(end);

    // Move cursor after inserted variable
    const newPos = start + variable.length;
    currentFocusField.setSelectionRange(newPos, newPos);
    currentFocusField.focus();
}

// Load available columns
async function loadColumns() {
    try {
        const response = await fetch(`${API_BASE}/api/columns`);
        const data = await response.json();

        if (data.columns && data.columns.length > 0) {
            availableColumns = data.columns.filter(col => col !== 'email');
            displayColumns(availableColumns);
            document.getElementById('templateSection').style.display = 'block';
        }
    } catch (error) {
        console.error('Failed to load columns:', error);
    }
}

// Load templates
async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/api/templates`);
        const data = await response.json();

        if (data.templates) {
            // Load initial template
            if (data.templates.initial) {
                document.getElementById('initialSubject').value = data.templates.initial.subject;
                document.getElementById('initialBody').value = data.templates.initial.body;
            }

            // Load followup1 template
            if (data.templates.followup1) {
                document.getElementById('followup1Subject').value = data.templates.followup1.subject;
                document.getElementById('followup1Body').value = data.templates.followup1.body;
            }

            // Load followup2 template
            if (data.templates.followup2) {
                document.getElementById('followup2Subject').value = data.templates.followup2.subject;
                document.getElementById('followup2Body').value = data.templates.followup2.body;
            }
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

// Save templates
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
        }
    };

    // Validate templates are not empty
    if (!templates.initial.subject || !templates.initial.body) {
        showNotification('Initial email subject and body are required', 'warning');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/templates/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(templates)
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Templates saved successfully!', 'success');
            loadLogs(); // Refresh logs to show the save event
        } else {
            showNotification('Failed to save templates', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
        console.error(error);
    }
}

// Utility functions
function getStatusColor(status) {
    const colors = {
        'RUNNING': '#10b981',
        'PAUSED': '#f59e0b',
        'STOPPED': '#ef4444',
        'COMPLETED': '#3b82f6'
    };
    return colors[status] || '#a1a1aa';
}

function getStatusBGColor(status) {
    const colors = {
        'RUNNING': '#90EE90',
        'PAUSED': '#FFE082',
        'STOPPED': '#FFCDD2',
        'COMPLETED': '#BBDEFB'
    };
    return colors[status] || '#E0E0E0';
}

function getStatusTextColor(status) {
    const colors = {
        'RUNNING': '#2E7D32',
        'PAUSED': '#F57C00',
        'STOPPED': '#C62828',
        'COMPLETED': '#1565C0'
    };
    return colors[status] || '#666666';
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type) {
    // Simple console notification for now
    // You can enhance this with a toast notification library
    console.log(`[${type.toUpperCase()}] ${message}`);
    alert(message);
}

// Setup drag and drop
function setupDragDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('csvFile');

    if (!uploadArea || !fileInput) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '#1976D2';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '';
        }, false);
    });

    uploadArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            fileInput.files = files;
            uploadLeads();
        }
    }, false);
}

// Insert variable into specific field
function insertVariableInto(fieldId, columnName) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    const variable = `{{${columnName}}}`;
    const start = field.selectionStart || 0;
    const end = field.selectionEnd || 0;
    const text = field.value;

    field.value = text.substring(0, start) + variable + text.substring(end);

    // Move cursor after inserted variable
    const newPos = start + variable.length;
    field.setSelectionRange(newPos, newPos);
    field.focus();
}

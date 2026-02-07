// Dashboard JavaScript - API Integration and Real-time Updates

const API_BASE = '';
let emailChart = null;
let chartData = {
    labels: [],
    data: []
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    loadMetrics();
    loadLogs();
    
    // Update every 5 seconds
    setInterval(loadMetrics, 5000);
    setInterval(loadLogs, 10000);
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
        document.getElementById('campaignStatus').textContent = data.campaign_status;
        
        // Update progress bar
        const percentage = (data.sent_today / data.daily_limit) * 100;
        document.getElementById('progressFill').style.width = `${percentage}%`;
        document.getElementById('progressPercent').textContent = `${Math.round(percentage)}%`;
        
        // Update chart
        updateChart(data.sent_today);
        
        // Update status card color
        const statusCard = document.querySelector('.status-card .metric-value');
        statusCard.style.color = getStatusColor(data.campaign_status);
        
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
        } else {
            showNotification('Upload failed', 'error');
        }
    } catch (error) {
        showNotification('Upload failed: ' + error.message, 'error');
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

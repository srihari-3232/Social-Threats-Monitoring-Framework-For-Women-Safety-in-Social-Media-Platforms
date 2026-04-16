// API Configuration
const API_CONFIG = {
    BASE_URL: 'http://127.0.0.1:5000/api',
    ENDPOINTS: {
        HEALTH: '/health'
    }
};

async function callAPI(endpoint, params = {}) {
    try {
        const url = new URL(API_CONFIG.BASE_URL + endpoint);
        const response = await fetch(url.toString());
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Vanta.js background
    try {
        if (typeof VANTA !== 'undefined') {
            VANTA.NET({
                el: "#vanta-bg",
                color: 0x0072ff,
                backgroundColor: 0x021027,
                points: 12.00,
                maxDistance: 22.00,
                spacing: 18.00
            });
        }
    } catch (error) {
        console.warn('Vanta.js initialization failed:', error);
    }

    // Get Started button with API health check
    const getStartedBtn = document.getElementById('getStartedBtn');
    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', async function() {
            if (this.classList.contains('clicked')) return;

            this.classList.add('clicked');
            this.disabled = true;

            const originalText = this.textContent;
            this.textContent = 'Checking System...';

            try {
                // Check API health before proceeding
                await callAPI(API_CONFIG.ENDPOINTS.HEALTH);
                this.textContent = 'System Ready! Redirecting...';

                setTimeout(() => {
                    window.location.href = "dashboard.html";
                }, 500);

            } catch (error) {
                console.error('API health check failed:', error);
                alert('System not ready. Please ensure the API server is running.');
                this.disabled = false;
                this.textContent = originalText;
                this.classList.remove('clicked');
            }
        });
    }

    // Check API status on page load
    checkAPIStatus();
});

async function checkAPIStatus() {
    try {
        const healthData = await callAPI(API_CONFIG.ENDPOINTS.HEALTH);
        showConnectionStatus(true, healthData);
    } catch (error) {
        showConnectionStatus(false);
    }
}

function showConnectionStatus(isConnected, healthData = null) {
    const statusElement = document.querySelector('.api-status');
    if (statusElement) {
        if (isConnected) {
            statusElement.textContent = 'System Online';
            statusElement.className = 'api-status online';
        } else {
            statusElement.textContent = 'System Offline';
            statusElement.className = 'api-status offline';
        }
    }
}

 //API Configuration
const API_CONFIG = {
    BASE_URL: 'http://127.0.0.1:5000/api',
    ENDPOINTS: {
        HEALTH: '/health',
        SCAN_ALL: '/scan/all',
        REDDIT: '/reddit/scan',
        TWITTER: '/twitter/scan',
        YOUTUBE: '/youtube/scan',
        GNEWS: '/gnews/scan',
        NEWSAPI: '/newsapi/scan'
    },
    DEFAULT_PARAMS: {
        LIMIT: 10,
        QUERY: 'harassment OR abuse',
        SUBREDDIT: 'TwoXChromosomes'
    }
};

// Utility function for API calls
async function callAPI(endpoint, params = {}) {
    try {
        const url = new URL(API_CONFIG.BASE_URL + endpoint);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                url.searchParams.append(key, value);
            }
        });

        const response = await fetch(url.toString());

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM Content Loaded - Initializing Social Threat Monitor');

    // Initialize Vanta.js background with error handling
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
            console.log('✅ Vanta.js initialized successfully');
        } else {
            console.warn('⚠️ VANTA is not defined - background animation disabled');
        }
    } catch (error) {
        console.warn('⚠️ Vanta.js initialization failed:', error);
    }

    // **FIXED TERMS AGREEMENT FUNCTIONALITY**
    const agreeBtn = document.getElementById('agreeBtn');
    const disclaimerBox = document.querySelector('.disclaimer-box');
    const detectSection = document.getElementById('detectSection');

    // Debug: Check if elements exist
    console.log('🔍 Checking DOM elements:');
    console.log('  agreeBtn:', agreeBtn);
    console.log('  disclaimerBox:', disclaimerBox);
    console.log('  detectSection:', detectSection);

    if (agreeBtn) {
        console.log('✅ Agree button found, adding click listener');
        agreeBtn.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent any default behavior
            console.log('🔘 Agree button clicked');

            try {
                if (disclaimerBox) {
                    disclaimerBox.style.display = 'none';
                    console.log('✅ Disclaimer box hidden');
                } else {
                    console.warn('⚠️ Disclaimer box not found');
                }

                if (detectSection) {
                    detectSection.style.display = 'block';
                    console.log('✅ Detect section shown');
                } else {
                    console.warn('⚠️ Detect section not found');
                }

                // Add smooth transition effect
                if (detectSection) {
                    detectSection.scrollIntoView({ behavior: 'smooth' });
                }

            } catch (error) {
                console.error('❌ Error in agree button handler:', error);
            }
        });
    } else {
        console.error('❌ Agree button not found! Check your HTML for element with id="agreeBtn"');
    }

    // **ENHANCED THREAT DETECTION BUTTON**
    const detectBtn = document.getElementById('detectBtn');
    console.log('🔍 Detect button:', detectBtn);

    if (detectBtn) {
        console.log('✅ Detect button found, adding click listener');
        detectBtn.addEventListener('click', async function(e) {
            e.preventDefault();

            if (this.disabled) {
                console.log('🚫 Button already disabled, ignoring click');
                return;
            }

            console.log('🔘 Detect button clicked - starting scan');
            this.disabled = true;
            const originalText = this.textContent;
            this.textContent = 'Scanning All Platforms...';

            try {
                console.log('📡 Calling backend API...');
                const results = await callAPI(API_CONFIG.ENDPOINTS.SCAN_ALL, {
                    query: API_CONFIG.DEFAULT_PARAMS.QUERY,
                    limit: API_CONFIG.DEFAULT_PARAMS.LIMIT
                });

                console.log('✅ API call successful:', results);

                // Store results for next page
                localStorage.setItem('threatScanResults', JSON.stringify(results));
                localStorage.setItem('scanTimestamp', new Date().toISOString());
                console.log('💾 Results stored in localStorage');

                // Show brief results summary
                if (results.success !== false) {
                    this.textContent = `Found ${results.total_threats_found || 0} threats! Redirecting...`;
                }

                // Navigate to results page
                console.log('🔄 Redirecting to detection.html in 1.5 seconds...');
                setTimeout(() => {
                    window.location.href = "detection.html";
                }, 1500);

            } catch (error) {
                console.error('❌ Scan failed:', error);
                const errorMessage = error.message.includes('Failed to fetch')
                    ? 'Unable to connect to server. Please ensure API is running.'
                    : 'Scan failed. Please try again.';

                alert(errorMessage);
                this.disabled = false;
                this.textContent = originalText;
            }
        });
    } else {
        console.error('❌ Detect button not found! Check your HTML for element with id="detectBtn"');
    }

    // Load live dashboard stats
    console.log('📊 Loading dashboard stats...');
    loadDashboardStats();
    setInterval(loadDashboardStats, 30000);

    console.log('🎉 Initialization complete!');
});

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        console.log('📡 Fetching health data...');
        const healthData = await callAPI(API_CONFIG.ENDPOINTS.HEALTH);
        updateServiceStatus(healthData);

        // Optional: Load recent threats count
        console.log('📡 Fetching recent threats data...');
        const recentData = await callAPI(API_CONFIG.ENDPOINTS.SCAN_ALL, {
            query: 'harassment',
            limit: 5
        });
        updateDashboardCounters(recentData);
        console.log('✅ Dashboard stats updated');

    } catch (error) {
        console.error('❌ Failed to load dashboard stats:', error);
    }
}

function updateServiceStatus(healthData) {
    Object.entries(healthData.services || {}).forEach(([service, status]) => {
        const serviceElement = document.querySelector(`[data-service="${service}"]`);
        if (serviceElement) {
            serviceElement.className = `service-status ${status}`;
            serviceElement.textContent = status.toUpperCase();
        }
    });
}

function updateDashboardCounters(data) {
    const totalThreats = document.querySelector('.total-threats-counter');
    if (totalThreats && data.total_threats_found !== undefined) {
        totalThreats.textContent = data.total_threats_found;
    }

    const servicesScanned = document.querySelector('.services-scanned-counter');
    if (servicesScanned && data.services_scanned !== undefined) {
        servicesScanned.textContent = data.services_scanned;
    }
}

// Alternative method using event delegation (in case elements are dynamically created)
document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'agreeBtn') {
        console.log('🔘 Agree button clicked via event delegation');
        e.preventDefault();

        const disclaimerBox = document.querySelector('.disclaimer-box');
        const detectSection = document.getElementById('detectSection');

        if (disclaimerBox) disclaimerBox.style.display = 'none';
        if (detectSection) {
            detectSection.style.display = 'block';
            detectSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
});

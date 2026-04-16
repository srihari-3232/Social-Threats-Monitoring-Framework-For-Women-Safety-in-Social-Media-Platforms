// API Configuration (same as above)
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
    }
};

async function callAPI(endpoint, params = {}) {
    try {
        const url = new URL(API_CONFIG.BASE_URL + endpoint);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                url.searchParams.append(key, value);
            }
        });

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
                points: 15.00,
                maxDistance: 25.00,
                spacing: 20.00
            });
        }
    } catch (error) {
        console.warn('Vanta.js initialization failed:', error);
    }

    // Initialize 3D visualization
    initThreatVisualization();

    // Platform click handlers
    document.querySelectorAll('.platform-card').forEach(card => {
        card.addEventListener('click', function() {
            const platform = this.getAttribute('data-platform');
            if (platform) {
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    window.location.href = `platform-${platform}.html?platform=${platform}`;
                }, 300);
            }
        });
    });

    // **LOAD REAL BACKEND RESULTS**
    loadBackendResults();
});

function initThreatVisualization() {
    const threatVizElement = document.getElementById('threatViz');
    if (!threatVizElement || typeof THREE === 'undefined') return;

    try {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75,
            threatVizElement.clientWidth / threatVizElement.clientHeight,
            0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

        renderer.setSize(threatVizElement.clientWidth, threatVizElement.clientHeight);
        threatVizElement.appendChild(renderer.domElement);

        // Create floating platform spheres
        const platforms = ['twitter', 'reddit', 'youtube', 'newsapi', 'gnews'];
        const platformObjects = [];

        platforms.forEach((platform, i) => {
            const geometry = new THREE.SphereGeometry(0.5, 32, 32);
            const material = new THREE.MeshBasicMaterial({
                color: i % 2 === 0 ? 0xff4444 : 0x4444ff,
                transparent: true,
                opacity: 0.8
            });
            const sphere = new THREE.Mesh(geometry, material);

            sphere.position.x = Math.cos(i * 2 * Math.PI / platforms.length) * 3;
            sphere.position.z = Math.sin(i * 2 * Math.PI / platforms.length) * 3;
            sphere.position.y = 0;

            sphere.userData.platform = platform;
            scene.add(sphere);
            platformObjects.push(sphere);
        });

        camera.position.z = 5;

        function animate() {
            requestAnimationFrame(animate);

            platformObjects.forEach((obj, i) => {
                obj.rotation.x += 0.01;
                obj.rotation.y += 0.01;
                obj.position.y = Math.sin(Date.now() * 0.001 + i) * 0.5;
            });

            renderer.render(scene, camera);
        }
        animate();

        // Handle resize
        window.addEventListener('resize', () => {
            camera.aspect = threatVizElement.clientWidth / threatVizElement.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(threatVizElement.clientWidth, threatVizElement.clientHeight);
        });

    } catch (error) {
        console.warn('3D visualization initialization failed:', error);
    }
}

// **LOAD REAL BACKEND RESULTS**
function loadBackendResults() {
    const savedResults = localStorage.getItem('threatScanResults');
    if (savedResults) {
        try {
            const results = JSON.parse(savedResults);
            displayRealResults(results);
        } catch (e) {
            console.error('Error parsing saved results:', e);
            loadLiveResults();
        }
    } else {
        loadLiveResults();
    }
}

// **DISPLAY REAL API RESULTS**
function displayRealResults(results) {
    try {
        // Update main statistics
        const mainCounter = document.querySelector('.main-threat-counter');
        if (mainCounter) {
            mainCounter.textContent = results.total_threats_found || 0;
        }

        const servicesCounter = document.querySelector('.services-counter');
        if (servicesCounter) {
            servicesCounter.textContent = results.services_scanned || 0;
        }

        // Update platform cards with real data
        Object.entries(results.services || {}).forEach(([platform, data]) => {
            const platformCard = document.querySelector(`[data-platform="${platform}"]`);
            if (platformCard && data && data.success) {
                const threatsFound = data.data?.threats_found || 0;
                const totalScanned = getItemsScanned(data.data);

                // Update platform card stats
                const statsDiv = platformCard.querySelector('.platform-stats');
                if (statsDiv) {
                    statsDiv.innerHTML = `
                        <div class="stat">
                            <span class="stat-number">${threatsFound}</span>
                            <span class="stat-label">Threats</span>
                        </div>
                        <div class="stat">
                            <span class="stat-number">${totalScanned}</span>
                            <span class="stat-label">Scanned</span>
                        </div>
                    `;
                }

                // Update platform status
                const statusIndicator = platformCard.querySelector('.status-indicator');
                if (statusIndicator) {
                    statusIndicator.className = `status-indicator ${threatsFound > 0 ? 'has-threats' : 'clean'}`;
                }
            }
        });

        // Update timestamp
        const timestampElement = document.querySelector('.scan-timestamp');
        if (timestampElement) {
            const scanTime = results.scan_timestamp || new Date().toISOString();
            timestampElement.textContent = `Scanned: ${new Date(scanTime).toLocaleString()}`;
        }

    } catch (error) {
        console.error('Error displaying results:', error);
    }
}

async function loadLiveResults() {
    try {
        const results = await callAPI(API_CONFIG.ENDPOINTS.SCAN_ALL, {
            query: 'harassment OR abuse',
            limit: 10
        });

        displayRealResults(results);
        localStorage.setItem('threatScanResults', JSON.stringify(results));

    } catch (error) {
        console.error('Failed to load live results:', error);
        showErrorMessage('Failed to load scan results. Please check if the API is running.');
    }
}

function getItemsScanned(data) {
    return data?.posts_scanned || data?.tweets_scanned || data?.videos_scanned || data?.articles_scanned || 0;
}

function showErrorMessage(message) {
    const errorElement = document.querySelector('.error-message');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

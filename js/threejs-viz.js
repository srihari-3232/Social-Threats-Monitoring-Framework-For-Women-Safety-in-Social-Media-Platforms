// API Configuration (same as above)
const API_CONFIG = {
    BASE_URL: 'http://127.0.0.1:5000/api',
    ENDPOINTS: {
        HEALTH: '/health',
        SCAN_ALL: '/scan/all'
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
    const threatViz = document.getElementById('threatViz');
    if (!threatViz || typeof THREE === 'undefined') {
        console.warn('3D visualization requirements not met');
        return;
    }

    let scene, camera, renderer, particles, dangerParticles;

    function initThreatVisualization() {
        try {
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75,
                threatViz.clientWidth / threatViz.clientHeight,
                0.1, 1000);
            renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

            renderer.setSize(threatViz.clientWidth, threatViz.clientHeight);
            threatViz.appendChild(renderer.domElement);

            // Create main particles
            const geometry = new THREE.BufferGeometry();
            const particleCount = 100;
            const positions = new Float32Array(particleCount * 3);

            for (let i = 0; i < particleCount; i++) {
                positions[i * 3] = (Math.random() - 0.5) * 10;
                positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
                positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
            }

            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

            const material = new THREE.PointsMaterial({
                color: 0x00c6ff,
                size: 0.1,
                transparent: true,
                opacity: 0.8,
                sizeAttenuation: true
            });

            particles = new THREE.Points(geometry, material);
            scene.add(particles);

            // Create danger particles
            const dangerGeometry = new THREE.BufferGeometry();
            const dangerPositions = new Float32Array(10 * 3);

            for (let i = 0; i < 10; i++) {
                dangerPositions[i * 3] = (Math.random() - 0.5) * 8;
                dangerPositions[i * 3 + 1] = (Math.random() - 0.5) * 8;
                dangerPositions[i * 3 + 2] = (Math.random() - 0.5) * 8;
            }

            dangerGeometry.setAttribute('position', new THREE.BufferAttribute(dangerPositions, 3));

            const dangerMaterial = new THREE.PointsMaterial({
                color: 0xff3e3e,
                size: 0.15,
                transparent: true,
                opacity: 0.9,
                sizeAttenuation: true
            });

            dangerParticles = new THREE.Points(dangerGeometry, dangerMaterial);
            scene.add(dangerParticles);

            camera.position.z = 5;

            animate();

            window.addEventListener('resize', handleResize);

        } catch (error) {
            console.error('3D visualization initialization failed:', error);
        }
    }

    function animate() {
        requestAnimationFrame(animate);

        if (particles) {
            particles.rotation.x += 0.001;
            particles.rotation.y += 0.002;
        }

        if (dangerParticles) {
            dangerParticles.rotation.x += 0.002;
            dangerParticles.rotation.y += 0.001;
        }

        if (renderer && scene && camera) {
            renderer.render(scene, camera);
        }
    }

    function handleResize() {
        if (!threatViz || !camera || !renderer) return;

        const width = threatViz.clientWidth;
        const height = threatViz.clientHeight;

        if (width > 0 && height > 0) {
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }
    }

    // **UPDATE VISUALIZATION WITH REAL API DATA**
    async function updateVisualizationWithAPIData() {
        try {
            const results = await callAPI(API_CONFIG.ENDPOINTS.SCAN_ALL, {
                query: 'harassment',
                limit: 5
            });

            // Update danger particles based on threat level
            if (dangerParticles && results.total_threats_found !== undefined) {
                const threatLevel = Math.min(results.total_threats_found / 10, 1); // Normalize to 0-1
                dangerParticles.material.opacity = 0.5 + (threatLevel * 0.4); // 0.5 to 0.9 opacity
                dangerParticles.material.size = 0.1 + (threatLevel * 0.1); // Grow with more threats
            }

        } catch (error) {
            console.warn('Could not update visualization with API data:', error);
        }
    }

    // Initialize
    initThreatVisualization();
    updateVisualizationWithAPIData();

    // Update every 30 seconds
    setInterval(updateVisualizationWithAPIData, 30000);
});

// ================== API CONFIG ==================
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

// ================== GLOBALS ==================
let confidenceChart = null;
let lastScan = null;

// ================== API CALLER ==================
async function callAPI(endpoint, params = {}) {
  const url = new URL(API_CONFIG.BASE_URL + endpoint);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined) url.searchParams.append(k, v);
  });

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
}

// ================== CHART.JS ==================
function updateConfidenceChart(detections) {
  const canvas = document.getElementById('confidenceChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');

  if (!detections || detections.length === 0) {
    if (confidenceChart) {
      confidenceChart.destroy();
      confidenceChart = null;
    }
    return;
  }

  const labels = detections.map((d, i) => {
    const type = d.type === 'video'
      ? 'Video'
      : d.type === 'comment'
      ? 'Comment'
      : 'Item';
    return `${type} #${i + 1}`;
  });

  const scores = detections.map(d => (d.confidence || 0) * 100);

  const bg = scores.map(s => {
    if (s >= 80) return 'rgba(220, 38, 38, 0.6)';
    if (s >= 50) return 'rgba(251, 146, 60, 0.6)';
    return 'rgba(252, 211, 77, 0.6)';
  });

  const border = scores.map(s => {
    if (s >= 80) return 'rgba(220, 38, 38, 1)';
    if (s >= 50) return 'rgba(251, 146, 60, 1)';
    return 'rgba(252, 211, 77, 1)';
  });

  if (confidenceChart) {
    confidenceChart.data.labels = labels;
    confidenceChart.data.datasets[0].data = scores;
    confidenceChart.data.datasets[0].backgroundColor = bg;
    confidenceChart.data.datasets[0].borderColor = border;
    confidenceChart.update();
  } else {
    confidenceChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Confidence Score (%)',
          data: scores,
          backgroundColor: bg,
          borderColor: border,
          borderWidth: 2,
          borderRadius: 5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: v => v + '%',
              color: '#ffffff'
            },
            grid: { color: 'rgba(255,255,255,0.1)' }
          },
          x: {
            ticks: { color: '#ffffff' },
            grid: { display: false }
          }
        },
        plugins: {
          legend: {
            labels: { color: '#ffffff' }
          },
          tooltip: {
            callbacks: {
              label: ctx => 'Confidence: ' + ctx.parsed.y.toFixed(1) + '%'
            }
          }
        }
      }
    });
  }
}
async function generatePDFReport() {
  const btn = document.getElementById('generateReportBtn');

  if (!lastScan || !lastScan.results || !lastScan.results.success) {
    return alert('Run analysis first.');
  }
  if (typeof html2pdf === 'undefined') {
    return alert('html2pdf not loaded.');
  }

  btn.textContent = 'Generating PDF...';
  btn.disabled = true;

  try {
    const data = lastScan.results.data || {};
    const detections = data.detections || [];
    const scannedCount =
      data.posts_scanned ||
      data.tweets_scanned ||
      data.videos_scanned ||
      data.articles_scanned ||
      0;
    const threatsFound = data.threats_found || detections.length;

    // Build a plain HTML container ONLY for the PDF
    const pdfRoot = document.createElement('div');
    pdfRoot.style.fontFamily = 'Arial, sans-serif';
    pdfRoot.style.color = '#000';
    pdfRoot.style.padding = '10px';

    pdfRoot.innerHTML = `
      <h1>${(lastScan.platform || 'Platform').toUpperCase()} Threat Analysis Report</h1>
      <p><strong>Platform:</strong> ${lastScan.platform}</p>
      <p><strong>Keywords:</strong> ${lastScan.keywords}</p>
      <p><strong>Scan Time:</strong> ${lastScan.timestamp}</p>
      <hr>
      <h2>Summary</h2>
      <p><strong>Items Scanned:</strong> ${scannedCount}</p>
      <p><strong>Threats Found:</strong> ${threatsFound}</p>
      <p><strong>Detection Rate:</strong> ${
        scannedCount > 0
          ? Math.round((threatsFound / scannedCount) * 100)
          : 0
      }%</p>
      <hr>
      <h2>Detailed Threat Log</h2>
    `;

    detections.forEach((raw, index) => {
      const d = raw || {};
      const content =
        d.content ||
        d.text_preview ||
        d.title ||
        'No content available';

      const created =
        d.created_at ||
        d.created_utc ||
        d.published_at ||
        null;

      const block = document.createElement('div');
      block.style.marginBottom = '12px';

      block.innerHTML = `
        <h3>Threat #${index + 1}</h3>
        <p><strong>Confidence:</strong> ${Math.round(
          (d.confidence || 0) * 100
        )}%</p>
        <p><strong>Author:</strong> ${
          d.author || d.username || 'Unknown User'
        }</p>
        <p><strong>Type:</strong> ${d.type || 'content'}</p>
        <p><strong>Time:</strong> ${formatDate(created)}</p>
        <p><strong>Content:</strong><br>${content}</p>
        ${
          d.keywords_found && d.keywords_found.length
            ? `<p><strong>Keywords Found:</strong> ${d.keywords_found.join(
                ', '
              )}</p>`
            : ''
        }
        ${
          getDetectionUrl(d)
            ? `<p><strong>URL:</strong> ${getDetectionUrl(d)}</p>`
            : ''
        }
        <hr>
      `;

      pdfRoot.appendChild(block);
    });

    const opt = {
      margin: 10,
      filename: `Threat-Report-${lastScan.platform}-${new Date()
        .toISOString()
        .slice(0, 10)}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: {
        scale: 2,
        useCORS: true
      },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // ⬇️ IMPORTANT: delete the first (blank) page before saving
    await html2pdf()
      .set(opt)
      .from(pdfRoot)
      .toPdf()
      .get('pdf')
      .then(pdf => {
        const total = pdf.internal.getNumberOfPages();
        if (total > 1) {
          pdf.deletePage(1); // remove empty first page
        }
      })
      .save();

    alert('PDF generated.');
  } catch (e) {
    console.error(e);
    alert('PDF error: ' + e.message);
  } finally {
    btn.textContent = 'Generate Comprehensive Report';
    btn.disabled = false;
  }
}


// ================== 3D VIZ ==================
function initThreatVisualization() {
  const threatVizElement = document.getElementById('threatViz');
  if (!threatVizElement || typeof THREE === 'undefined') return;

  try {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      threatVizElement.clientWidth / threatVizElement.clientHeight,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

    renderer.setSize(threatVizElement.clientWidth, threatVizElement.clientHeight);
    threatVizElement.appendChild(renderer.domElement);

    const particlesGeo = new THREE.BufferGeometry();
    const particlesCnt = 500;
    const posArray = new Float32Array(particlesCnt * 3);

    for (let i = 0; i < particlesCnt * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 10;
    }

    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

    const particlesMat = new THREE.PointsMaterial({
      size: 0.05,
      color: 0x1DA1F2,
      transparent: true,
      opacity: 0.8
    });

    const particlesMesh = new THREE.Points(particlesGeo, particlesMat);
    scene.add(particlesMesh);

    const dangerParticlesGeo = new THREE.BufferGeometry();
    const dangerPosArray = new Float32Array(30 * 3);

    for (let i = 0; i < dangerPosArray.length; i++) {
      dangerPosArray[i] = (Math.random() - 0.5) * 8;
    }

    dangerParticlesGeo.setAttribute('position', new THREE.BufferAttribute(dangerPosArray, 3));

    const dangerParticlesMat = new THREE.PointsMaterial({
      size: 0.1,
      color: 0xff4d4d,
      transparent: true,
      opacity: 0.9
    });

    const dangerParticlesMesh = new THREE.Points(dangerParticlesGeo, dangerParticlesMat);
    scene.add(dangerParticlesMesh);

    camera.position.z = 5;

    function animate() {
      requestAnimationFrame(animate);

      particlesMesh.rotation.x += 0.001;
      particlesMesh.rotation.y += 0.002;
      dangerParticlesMesh.rotation.x += 0.003;
      dangerParticlesMesh.rotation.y += 0.001;

      renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
      camera.aspect = threatVizElement.clientWidth / threatVizElement.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(threatVizElement.clientWidth, threatVizElement.clientHeight);
    });

  } catch (error) {
    console.warn('3D visualization initialization failed:', error);
  }
}

// ================== ANALYZE KEYWORDS ==================
async function analyzeKeywords() {
  const searchInput = document.getElementById('searchInput');
  const keywords = searchInput ? searchInput.value.trim() : '';

  if (!keywords) {
    alert('Please enter keywords to search for');
    return;
  }

  const searchBtn = document.getElementById('searchBtn');
  if (searchBtn) {
    searchBtn.textContent = 'Analyzing...';
    searchBtn.disabled = true;
  }

  try {
    const platform = 'youtube'; // this page is fixed to YouTube

    let endpoint = API_CONFIG.ENDPOINTS.YOUTUBE;
    let params = { query: keywords, limit: 15 };

    const results = await callAPI(endpoint, params);
    showRealResults(results, keywords, platform);

  } catch (error) {
    console.error('Analysis failed:', error);

    const errorMessage = error.message.includes('Failed to fetch')
      ? 'Unable to connect to server. Please ensure API is running.'
      : `Analysis failed: ${error.message}`;

    alert(errorMessage);
    showFallbackResults();

  } finally {
    if (searchBtn) {
      searchBtn.textContent = 'Analyze';
      searchBtn.disabled = false;
    }
  }
}

// ================== SHOW REAL RESULTS ==================
function showRealResults(results, keywords, platform) {
  const resultsSection = document.getElementById('resultsSection');
  const container = document.getElementById('tweetsContainer');

  if (!resultsSection || !container) return;

  lastScan = {
    results,
    keywords,
    platform,
    timestamp: new Date().toLocaleString()
  };

  resultsSection.style.display = 'block';
  container.innerHTML = '';

  const data = results.data || {};
  const detections = data.detections || [];
  const scannedCount = getItemsScanned(data);
  const threatsFound = data.threats_found || detections.length;

  if (results.success && detections.length > 0) {
    const statsDiv = document.createElement('div');
    statsDiv.className = 'scan-stats';
    statsDiv.innerHTML = `
      <div class="stat-grid">
        <div class="stat-item">
          <span class="stat-number">${threatsFound}</span>
          <span class="stat-label">Threats Found</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">${scannedCount}</span>
          <span class="stat-label">Items Scanned</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">
            ${scannedCount > 0 ? Math.round((threatsFound / scannedCount) * 100) : 0}%
          </span>
          <span class="stat-label">Detection Rate</span>
        </div>
      </div>
    `;
    container.appendChild(statsDiv);

    detections.forEach((detectionRaw) => {
      const detection = detectionRaw || {};
      const content = detection.content || detection.text_preview || detection.title || 'No content available';
      const created = detection.created_at || detection.created_utc || detection.published_at || null;

      const detectionEl = document.createElement('div');
      detectionEl.className = 'detection-card';
      detectionEl.innerHTML = `
        <div class="detection-header">
          <div class="detection-user">
            <strong>${detection.author || detection.username || 'Unknown User'}</strong>
            <span class="detection-type">${detection.type || 'content'}</span>
          </div>
          <div class="confidence-badge confidence-${getConfidenceLevel(detection.confidence)}">
            ${Math.round((detection.confidence || 0) * 100)}% Confidence
          </div>
        </div>
        <div class="detection-content">
          ${content}
        </div>
        <div class="detection-meta">
          <span class="detection-time">
            📅 ${formatDate(created)}
          </span>
          ${detection.keywords_found && detection.keywords_found.length > 0 ?
            `<span class="detection-keywords">🔍 ${detection.keywords_found.join(', ')}</span>` : ''}
          ${getDetectionUrl(detection) ?
            `<a href="${getDetectionUrl(detection)}" target="_blank" class="view-original">View Original</a>` : ''}
        </div>
      `;
      container.appendChild(detectionEl);
    });

    updateConfidenceChart(detections);
  } else if (results.success) {
    container.innerHTML = `
      <div class="no-results">
        <h4>✅ No threats detected</h4>
        <p>No threatening content found with "${keywords}" on ${platform}.</p>
        <p>This platform appears clean for these search terms.</p>
      </div>
    `;
    updateConfidenceChart([]);
  } else {
    container.innerHTML = `
      <div class="error-results">
        <h4>❌ Scan Error</h4>
        <p>Error: ${results.error || 'Unknown error'}</p>
        <p>Please try again or contact support.</p>
      </div>
    `;
  }

  resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// ================== HELPERS ==================
function getItemsScanned(data) {
  return data?.posts_scanned ||
         data?.tweets_scanned ||
         data?.videos_scanned ||
         data?.articles_scanned ||
         0;
}

function getConfidenceLevel(confidence) {
  const conf = confidence || 0;
  if (conf >= 0.8) return 'high';
  if (conf >= 0.5) return 'medium';
  return 'low';
}

function formatDate(dateString) {
  if (!dateString) return 'Recent';
  try {
    return new Date(dateString).toLocaleString();
  } catch {
    return dateString;
  }
}

function getDetectionUrl(detection) {
  return detection.url ||
         detection.post_url ||
         detection.tweet_url ||
         detection.video_url ||
         '';
}

function showFallbackResults() {
  const resultsSection = document.getElementById('resultsSection');
  const container = document.getElementById('tweetsContainer');

  if (!resultsSection || !container) return;

  resultsSection.style.display = 'block';
  container.innerHTML = `
    <div class="fallback-results">
      <h4>⚠️ API Connection Failed</h4>
      <p>Could not connect to the threat detection API.</p>
      <ul>
        <li>Ensure API server is running on http://127.0.0.1:5000</li>
        <li>Check your internet connection</li>
        <li>Verify no firewall is blocking the connection</li>
      </ul>
    </div>
  `;
}

// ================== DOM READY ==================
document.addEventListener('DOMContentLoaded', function () {
  try {
    if (typeof VANTA !== 'undefined') {
      VANTA.NET({
        el: "#vanta-bg",
        color: 0x1DA1F2,
        backgroundColor: 0x021027,
        points: 15.00,
        maxDistance: 25.00,
        spacing: 20.00
      });
    }
  } catch (err) {
    console.warn('Vanta.js initialization failed:', err);
  }

  initThreatVisualization();

  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');
  const generateReportBtn = document.getElementById('generateReportBtn');

  if (searchBtn) searchBtn.addEventListener('click', analyzeKeywords);
  if (searchInput) {
    searchInput.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') analyzeKeywords();
    });
  }

  if (generateReportBtn) {
    generateReportBtn.addEventListener('click', generatePDFReport);
  }
});
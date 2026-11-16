/**
 * app.js - Frontend Logic for Wormhole Web Dashboard
 * Handles API calls, Canvas drawing, and Chart.js updates.
 */

const API_BASE = "http://127.0.0.1:5000";
let networkChart = null;
let currentSimulationData = null;

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // Add event listeners for window resize to redraw canvas
    window.addEventListener('resize', drawNetwork);

    // Initialize empty chart
    initChart();
});

// ============================================================================
// API Calls
// ============================================================================
async function runSimulation() {
    const profileSelect = document.getElementById('profileSelect');
    const attackSelect = document.getElementById('attackSelect');
    const scenarioSelect = document.getElementById('scenarioSelect');

    const profile = profileSelect.value;
    const attack_mode = attackSelect ? attackSelect.value : "out-of-band";
    const scenario = scenarioSelect ? scenarioSelect.value : "defence";

    const btn = document.getElementById('runBtn');
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');
    const statusBadge = document.getElementById('status-badge');
    const canvasEmptyMsg = document.getElementById('canvasEmptyMsg');

    // UI Loading State
    btn.disabled = true;
    profileSelect.disabled = true;
    if (attackSelect) attackSelect.disabled = true;
    if (scenarioSelect) scenarioSelect.disabled = true;

    btnText.textContent = "Running Simulation...";
    btnLoader.classList.remove('hidden');
    statusBadge.textContent = "Simulating...";
    statusBadge.className = "px-3 py-1 rounded-full text-xs font-medium bg-amber-500/20 text-amber-400 border border-amber-500/30";

    try {
        const randomSeed = Math.floor(Math.random() * 1000000);
        const response = await fetch(`${API_BASE}/api/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profile: profile,
                attack_mode: attack_mode,
                scenario: scenario,
                seed: randomSeed
            })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        currentSimulationData = data;
        canvasEmptyMsg.style.display = 'none';

        updateDashboard(data);
        drawNetwork();
        updatePhaseIndicator(data);

        // Success state
        statusBadge.textContent = "Simulation Complete";
        statusBadge.className = "px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30";

    } catch (error) {
        console.error("Simulation failed:", error);
        alert(`Simulation failed: ${error.message}`);
        statusBadge.textContent = "Error";
        statusBadge.className = "px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30";
    } finally {
        // Restore UI
        btn.disabled = false;
        profileSelect.disabled = false;
        const attackSelect = document.getElementById('attackSelect');
        if (attackSelect) attackSelect.disabled = false;
        const scenarioSelect = document.getElementById('scenarioSelect');
        if (scenarioSelect) scenarioSelect.disabled = false;
        btnText.textContent = "Run New Simulation";
        btnLoader.classList.add('hidden');

        // Remove pulse animation after 1s
        setTimeout(() => {
            document.querySelectorAll('.animate-update').forEach(el => {
                el.classList.remove('animate-update');
            });
        }, 1000);
    }
}


// ============================================================================
// Phase Indicator — honest context label in the header
// ============================================================================
function updatePhaseIndicator(data) {
    const el = document.getElementById('phase-indicator');
    if (!el) return;
    const profile = (data.profile_name || '').replace(/_/g, ' ');
    const mode = (data.attack_mode || '').replace(/-/g, ' ');
    if (data.scenario === 'baseline') {
        el.textContent = `Phase 1 — Warm-up / No Attack · ${profile}`;
        el.className = 'text-xs font-mono tracking-wide phase-baseline';
    } else if (data.scenario === 'attack_only') {
        el.textContent = `Phase 2 — Attack Injected (${mode}) · No Defence · ${profile}`;
        el.className = 'text-xs font-mono tracking-wide phase-attack';
    } else {
        const wdr = data.summary && data.summary.wormhole_detection_rate != null
            ? (data.summary.wormhole_detection_rate * 100).toFixed(0) + '% WDR'
            : '';
        el.textContent = `Phase 3 — Attack + Defence Engine · ${profile} · ${wdr}`;
        el.className = 'text-xs font-mono tracking-wide phase-defence';
    }
}

// ============================================================================
// UI Updates
// ============================================================================
function updateDashboard(data) {
    const summary = data.summary;

    // Helper to format and trigger pulse animation
    const setVal = (id, val, formatFx = x => x) => {
        const el = document.getElementById(id);
        el.textContent = formatFx(val);
        el.parentElement.parentElement.classList.add('animate-update');
    };

    // Core Metrics
    setVal('metric-dr', summary.detection_rate * 100, x => x.toFixed(1));
    setVal('metric-fpr', summary.false_positive_rate * 100, x => x.toFixed(1));
    setVal('metric-latency', summary.avg_latency, x => x.toFixed(1));
    setVal('metric-overhead', summary.overhead * 100, x => `Overhead: ${x.toFixed(1)}%`);

    // ML Metrics if available
    const mlDrContainer = document.getElementById('ml-dr-container');
    const mlFprContainer = document.getElementById('ml-fpr-container');
    if (data.ml_available) {
        if (mlDrContainer) {
            mlDrContainer.classList.remove('hidden');
            setVal('metric-ml-dr', data.ml_detection_rate, x => x.toFixed(1));
        }
        if (mlFprContainer) {
            mlFprContainer.classList.remove('hidden');
            setVal('metric-ml-fpr', data.ml_false_positive_rate, x => x.toFixed(1));
        }
    } else {
        if (mlDrContainer) mlDrContainer.classList.add('hidden');
        if (mlFprContainer) mlFprContainer.classList.add('hidden');
    }

    // Wormhole Detection Rate (the accurate metric)
    const wdr = summary.wormhole_detection_rate != null ? summary.wormhole_detection_rate * 100 : null;
    const wUsage = summary.wormhole_usage != null ? summary.wormhole_usage : null;
    const wdrEl = document.getElementById('metric-wdr');
    if (wdrEl) wdrEl.textContent = wdr != null ? wdr.toFixed(1) : '--';
    const wUsageEl = document.getElementById('metric-wormhole-usage');
    if (wUsageEl && wUsage != null) {
        const whPkts = Math.round(wUsage * (summary.attack_packets || 0));
        wUsageEl.textContent = `${whPkts} wormhole packets in run (${(wUsage * 100).toFixed(0)}% of attack traffic)`;
    }
    const mlWdrContainer = document.getElementById('ml-wdr-container');
    if (data.ml_available && mlWdrContainer) {
        mlWdrContainer.classList.remove('hidden');
        const mlWdrEl = document.getElementById('metric-ml-wdr');
        if (mlWdrEl) mlWdrEl.textContent = data.ml_detection_rate != null ? data.ml_detection_rate.toFixed(1) : '--';
    } else if (mlWdrContainer) {
        mlWdrContainer.classList.add('hidden');
    }

    // Update Rules vs ML comparison chart
    updateRulesVsMLChart(data);

    document.getElementById('metric-tp').textContent = `${summary.true_positives} / ${summary.attack_packets} Attack Pkts Found`;
    document.getElementById('metric-fp').textContent = `${summary.false_positives} / ${summary.normal_packets} Normal Pkts Flagged`;
    document.getElementById('tp-badge').textContent = `${summary.true_positives} Packets Caught`;

    // Config Parameters
    document.getElementById('param-rtt').textContent = data.baseline_thresholds.rtt_anomaly_factor + "x";
    document.getElementById('param-hop').textContent = "≥ " + data.baseline_thresholds.hop_count_drop + " hops";
    document.getElementById('param-stretch').textContent = "> " + data.baseline_thresholds.stretch_threshold + " ratio";
    document.getElementById('param-fwd').textContent = data.baseline_thresholds.fwd_spike_factor + "x base";
    if (data.scenario === "baseline") {
        document.getElementById('param-wh').textContent = "None (Baseline)";
        document.getElementById('param-wh').className = "text-slate-400 bg-slate-800 px-1 rounded";
    } else {
        document.getElementById('param-wh').textContent = `Node ${data.wormhole_endpoints[0]} ↔ Node ${data.wormhole_endpoints[1]}`;
        document.getElementById('param-wh').className = "text-white bg-red-500/20 px-1 rounded";
    }

    // New Features & Simulation Params
    document.getElementById('feat-warmup').textContent = data.simulation_params.warmup_duration;
    document.getElementById('param-pkts').textContent = `${summary.total_packets} pkts at ${data.simulation_params.traffic_rate} p/s`;

    // Update Alerts Table (Show all detected anomalies)
    updateAlertsTable(data.packet_feed || []);

    // Update Rule Distribution Chart
    updateChart(data.rule_counts || {});
}

function updateAlertsTable(packets) {
    const tbody = document.getElementById('alertsTableBody');
    tbody.innerHTML = '';

    // Filter for ALL detected anomalies (True Positives AND False Positives by either Rules or ML)
    const flagged = packets.filter(p => p.detected || p.ml_detected);

    if (flagged.length === 0) {
        const isBaseline = currentSimulationData && currentSimulationData.scenario === 'baseline';
        const msg = isBaseline
            ? 'Warm-up phase — no attack injected. This is expected.'
            : 'No anomalies detected in this run.';
        tbody.innerHTML = `<tr><td colspan="7" class="px-3 py-6 text-center text-slate-500 italic">${msg}</td></tr>`;
        return;
    }

    // Show top 50 to avoid DOM lag
    const displayPkts = flagged.slice(0, 50);

    displayPkts.forEach(p => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/50 transition-colors";

        // Format path with highlight on wormhole traversal if applicable
        const pathStr = Array.isArray(p.path) ? p.path.join(" → ") :
            (typeof p.path === 'string' ? p.path.replace(/->/g, " → ") : `${p.src || '?'} → ${p.dst || '?'}`);
        const ruleStr = Array.isArray(p.alerts) ? p.alerts.join(", ") :
            (typeof p.alerts === 'string' ? p.alerts.replace(/;/g, ", ") : "");

        let confBadge = "";
        if (p.confidence === "High") {
            confBadge = `<span class="bg-red-500/20 text-red-400 px-2 py-0.5 rounded border border-red-500/30 text-[10px] font-bold tracking-wider">HIGH</span>`;
        } else if (p.confidence === "Medium") {
            confBadge = `<span class="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded border border-amber-500/30 text-[10px] font-bold tracking-wider">MED</span>`;
        } else {
            confBadge = `<span class="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/30 text-[10px] font-bold tracking-wider">LOW</span>`;
        }

        // Add TP/FP Badge — p.wormhole = true means packet traversed the wormhole (TP candidate)
        const isTP = p.wormhole;
        const typeBadge = isTP
            ? `<span class="text-[10px] uppercase font-bold text-red-400 tracking-wider">TP</span>`
            : `<span class="text-[10px] uppercase font-bold text-slate-500 tracking-wider">FP</span>`;

        const mlBadge = (p.ml_detected !== undefined) ?
            (p.ml_detected ? `<span class="text-green-400 font-bold">DETECTED</span>` : `<span class="text-slate-500">MISSED</span>`) :
            `<span class="text-slate-600">N/A</span>`;

        const ruleDetectedIcon = p.detected ? `<span class="text-green-400">✓</span>` : `<span class="text-slate-500">✗</span>`;

        tr.innerHTML = `
            <td class="px-3 py-2 font-mono text-slate-400">#${p.id}</td>
            <td class="px-3 py-2 text-slate-300 truncate max-w-xs" title="${pathStr}">${pathStr}</td>
            <td class="px-3 py-2"><span class="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">${p.hops}</span></td>
            <td class="px-3 py-2">${typeBadge}</td>
            <td class="px-3 py-2 flex items-center gap-2">${ruleDetectedIcon} ${confBadge}</td>
            <td class="px-3 py-2 text-xs">${mlBadge}</td>
            <td class="px-3 py-2"><span class="text-slate-400 text-xs">${ruleStr.replace(/_/g, " ")}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// ============================================================================
// Canvas Drawing
// ============================================================================
function drawNetwork() {
    if (!currentSimulationData) return;

    const canvas = document.getElementById('networkCanvas');
    const container = canvas.parentElement;
    const ctx = canvas.getContext('2d');

    // Set internal resolution to match display size for crisp rendering
    // Use devicePixelRatio for Retina displays
    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    // Add some padding inside the canvas
    const padding = 40;
    const drawWidth = rect.width - (padding * 2);
    const drawHeight = rect.height - (padding * 2);

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);

    const nodes = currentSimulationData.nodes;
    const areaSize = currentSimulationData.area_size;

    // Scale mapping function (Sim Coordinates -> Canvas Coordinates)
    // Map the square area_size to fit inside the rectangular canvas while maintaining aspect ratio
    const scale = Math.min(drawWidth / areaSize, drawHeight / areaSize);

    // Center the square drawing area in the rectangular canvas
    const xOffset = padding + (drawWidth - (areaSize * scale)) / 2;
    const yOffset = padding + (drawHeight - (areaSize * scale)) / 2;

    const getX = (simX) => xOffset + (simX * scale);
    const getY = (simY) => yOffset + (simY * scale);

    // 1. Draw Normal Links
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.2)'; // Faint blue

    nodes.forEach(node => {
        const nx = getX(node.x);
        const ny = getY(node.y);

        node.neighbours.forEach(nbId => {
            // Only draw one way to avoid double drawing
            if (node.id < nbId) {
                const nb = nodes.find(n => n.id === nbId);
                // Check if this is the wormhole link
                const isWormhole =
                    (node.is_attacker && nb.is_attacker &&
                        currentSimulationData.wormhole_endpoints.includes(node.id) &&
                        currentSimulationData.wormhole_endpoints.includes(nb.id));

                if (!isWormhole) {
                    ctx.beginPath();
                    ctx.moveTo(nx, ny);
                    ctx.lineTo(getX(nb.x), getY(nb.y));
                    ctx.stroke();
                }
            }
        });
    });

    // 2. Draw Wormhole Link (Glowing Red)
    const whEndpoints = currentSimulationData.wormhole_endpoints;
    const whNodeA = nodes.find(n => n.id === whEndpoints[0]);
    const whNodeB = nodes.find(n => n.id === whEndpoints[1]);

    if (whNodeA && whNodeB) {
        ctx.beginPath();
        ctx.moveTo(getX(whNodeA.x), getY(whNodeA.y));
        ctx.lineTo(getX(whNodeB.x), getY(whNodeB.y));

        // Add glow
        ctx.shadowBlur = 15;
        ctx.shadowColor = '#ef4444';
        ctx.lineWidth = 3;
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.8)'; // Solid Red

        // Make it dashed to represent a tunnel
        ctx.setLineDash([10, 5]);
        ctx.stroke();

        // Reset styles
        ctx.setLineDash([]);
        ctx.shadowBlur = 0;
    }

    // 3. Draw Nodes
    nodes.forEach(node => {
        const nx = getX(node.x);
        const ny = getY(node.y);

        ctx.beginPath();

        // Base node sizes
        const radius = node.is_attacker ? 8 : 6;

        // Node fill and style
        if (node.is_attacker) {
            ctx.fillStyle = '#ef4444'; // Red for attackers
            ctx.shadowBlur = 10;
            ctx.shadowColor = '#ef4444';
        } else {
            // Map forwarding count to brightness (hotter = more forwards)
            const heat = Math.min(node.forwarded / 50, 1); // Normalize roughly
            const r = Math.floor(59 + (255 - 59) * heat); // Fade to white-ish
            const g = Math.floor(130 + (255 - 130) * heat);
            const b = 246; // Base blue

            ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
            ctx.shadowBlur = heat > 0.5 ? 8 : 0;
            ctx.shadowColor = '#60a5fa';
        }

        ctx.arc(nx, ny, radius, 0, Math.PI * 2);
        ctx.fill();

        // Reset shadow
        ctx.shadowBlur = 0;

        // Node labels (IDs)
        ctx.fillStyle = '#f8fafc';
        ctx.font = '10px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // Draw text slightly offset if it's a normal node, center if large attacker
        if (node.is_attacker) {
            ctx.fillText(node.id, nx, ny);
        } else {
            ctx.fillText(node.id, nx, ny - 10);
        }
    });
}

// ============================================================================
// ChartJS
// ============================================================================
function initChart() {
    const ctx = document.getElementById('ruleChart').getContext('2d');

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Inter';

    networkChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['No Data'],
            datasets: [{
                data: [1],
                backgroundColor: ['#1e293b'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 10, padding: 15, font: { size: 10 } }
                }
            }
        }
    });
}

function updateChart(ruleCounts) {
    if (!networkChart) return;

    const totalDetected = Object.values(ruleCounts).reduce((a, b) => a + b, 0);

    if (totalDetected === 0) {
        networkChart.data.labels = ['No Anomalies'];
        networkChart.data.datasets[0].data = [1];
        networkChart.data.datasets[0].backgroundColor = ['#1e293b'];
    } else {
        const labels = Object.keys(ruleCounts).map(l => l.replace(/_/g, " "));
        const data = Object.values(ruleCounts);

        // Colors mapping
        const colorMap = {
            'RTT_ANOMALY': '#8b5cf6',           // Purple
            'NEIGHBOUR_INCONSISTENCY': '#ef4444', // Red
            'PATH_STRETCH_ANOMALY': '#f59e0b',    // Amber
            'HOP_COUNT_DROP': '#3b82f6',          // Blue
            'FORWARDED_SPIKE': '#10b981'          // Green
        };

        const colors = Object.keys(ruleCounts).map(r => colorMap[r] || '#64748b');

        networkChart.data.labels = labels;
        networkChart.data.datasets[0].data = data;
        networkChart.data.datasets[0].backgroundColor = colors;
    }

    networkChart.update();
}

// ============================================================================
// Tab Switching (Simulate / Scan)
// ============================================================================
let currentMode = "sim";

function switchTab(mode) {
    currentMode = mode;
    const tabSim = document.getElementById('tabSim');
    const tabScan = document.getElementById('tabScan');
    const simControls = document.getElementById('simControls');
    const scanControls = document.getElementById('scanControls');
    const canvasPanel = document.getElementById('canvasContainer')?.closest('.glass-panel');

    if (mode === 'sim') {
        tabSim.className = "flex-1 px-4 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-blue-600 to-blue-500 text-white border border-blue-500/30 transition-all";
        tabScan.className = "flex-1 px-4 py-2.5 rounded-lg text-sm font-semibold bg-dark-panel text-slate-400 border border-dark-border hover:border-purple-500/50 transition-all";
        simControls.classList.remove('hidden');
        scanControls.classList.add('hidden');
        if (canvasPanel) canvasPanel.style.display = '';
    } else {
        tabScan.className = "flex-1 px-4 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-purple-600 to-purple-500 text-white border border-purple-500/30 transition-all";
        tabSim.className = "flex-1 px-4 py-2.5 rounded-lg text-sm font-semibold bg-dark-panel text-slate-400 border border-dark-border hover:border-blue-500/50 transition-all";
        scanControls.classList.remove('hidden');
        simControls.classList.add('hidden');
        if (canvasPanel) canvasPanel.style.display = 'none';
    }
}

function updateFileName() {
    const file = document.getElementById('uploadFile').files[0];
    const display = document.getElementById('fileNameDisplay');
    display.textContent = file ? file.name : "Drop CSV or JSON here";
}

// ============================================================================
// Static Scan
// ============================================================================
async function runScan() {
    const fileInput = document.getElementById('uploadFile');
    const btn = document.getElementById('scanBtn');
    const btnText = document.getElementById('scanBtnText');
    const btnLoader = document.getElementById('scanBtnLoader');
    const statusBadge = document.getElementById('status-badge');

    if (!fileInput.files.length) {
        statusBadge.textContent = "No file selected";
        statusBadge.className = "px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30";
        return;
    }

    btn.disabled = true;
    btnText.textContent = "Scanning...";
    btnLoader.classList.remove('hidden');
    statusBadge.textContent = "Scanning...";
    statusBadge.className = "px-3 py-1 rounded-full text-xs font-medium bg-amber-500/20 text-amber-400 border border-amber-500/30";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch(`${API_BASE}/api/scan`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.error) throw new Error(data.error);

        updateScanDashboard(data);

        statusBadge.textContent = "Scan Complete";
        statusBadge.className = "px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30";
    } catch (error) {
        console.error("Scan failed:", error);
        statusBadge.textContent = "Scan Error";
        statusBadge.className = "px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30";
    } finally {
        btn.disabled = false;
        btnText.textContent = "\ud83d\udd0d Run Static Scan";
        btnLoader.classList.add('hidden');
    }
}

function updateScanDashboard(data) {
    const s = data.summary;

    // Update metric cards
    const setVal = (id, val, formatFx = x => x) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = formatFx(val);
            el.parentElement.parentElement.classList.add('animate-update');
        }
    };

    setVal('metric-dr', s.detection_rate * 100, x => x.toFixed(1));
    setVal('metric-fpr', s.false_positive_rate * 100, x => x.toFixed(1));
    setVal('metric-latency', s.avg_latency, x => x.toFixed(1));

    const tpEl = document.getElementById('metric-tp');
    if (tpEl) tpEl.textContent = `${s.true_positives} / ${s.attack_packets} Attack Pkts Found`;
    const fpEl = document.getElementById('metric-fp');
    if (fpEl) fpEl.textContent = `${s.false_positives} / ${s.normal_packets} Normal Pkts Flagged`;
    const tpBadge = document.getElementById('tp-badge');
    if (tpBadge) tpBadge.textContent = `${s.true_positives} Packets Caught`;

    // Update alerts table with scan results
    const tbody = document.getElementById('alertsTableBody');
    tbody.innerHTML = '';
    const flagged = (data.packet_feed || []).filter(p => p.detected || p.ml_detected);

    if (flagged.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="px-3 py-6 text-center text-slate-500 italic">No anomalies detected in uploaded data.</td></tr>`;
    } else {
        flagged.slice(0, 50).forEach(p => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-800/50 transition-colors";
            const pathStr = `${p.src} \u2192 ${p.dst}`;
            const ruleStr = p.alerts || '';
            let confBadge = '';
            if (p.confidence === 'High') confBadge = `<span class="bg-red-500/20 text-red-400 px-2 py-0.5 rounded border border-red-500/30 text-[10px] font-bold">HIGH</span>`;
            else if (p.confidence === 'Medium') confBadge = `<span class="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded border border-amber-500/30 text-[10px] font-bold">MED</span>`;
            else confBadge = `<span class="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/30 text-[10px] font-bold">LOW</span>`;
            const typeBadge = p.wormhole
                ? `<span class="text-[10px] uppercase font-bold text-red-400">TP</span>`
                : `<span class="text-[10px] uppercase font-bold text-slate-500">FP</span>`;

            const mlBadge = (p.ml_detected !== undefined) ?
                (p.ml_detected ? `<span class="text-green-400 font-bold">DETECTED</span>` : `<span class="text-slate-500">MISSED</span>`) :
                `<span class="text-slate-600">N/A</span>`;

            const ruleDetectedIcon = p.detected ? `<span class="text-green-400">✓</span>` : `<span class="text-slate-500">✗</span>`;

            tr.innerHTML = `
                <td class="px-3 py-2 font-mono text-slate-400">#${p.id}</td>
                <td class="px-3 py-2 text-slate-300">${pathStr}</td>
                <td class="px-3 py-2"><span class="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">${p.hops}</span></td>
                <td class="px-3 py-2">${typeBadge}</td>
                <td class="px-3 py-2 flex items-center gap-2">${ruleDetectedIcon} ${confBadge}</td>
                <td class="px-3 py-2 text-xs">${mlBadge}</td>
                <td class="px-3 py-2"><span class="text-slate-400 text-xs">${ruleStr.replace(/_/g, " ")}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Update rule chart with scan data
    if (networkChart && data.rule_counts) {
        const ruleCounts = data.rule_counts;
        const labels = Object.keys(ruleCounts).map(l => l.replace(/_/g, " "));
        const vals = Object.values(ruleCounts);
        const colorMap = {
            'RTT_ANOMALY': '#8b5cf6', 'NEIGHBOUR_INCONSISTENCY': '#ef4444',
            'PATH_STRETCH_ANOMALY': '#f59e0b', 'HOP_COUNT_DROP': '#3b82f6', 'FORWARDED_SPIKE': '#10b981'
        };
        const colors = Object.keys(ruleCounts).map(r => colorMap[r] || '#64748b');
        networkChart.data.labels = labels;
        networkChart.data.datasets[0].data = vals;
        networkChart.data.datasets[0].backgroundColor = colors;
        networkChart.update();
    }

    // Remove animation after 1s
    setTimeout(() => {
        document.querySelectorAll('.animate-update').forEach(el => el.classList.remove('animate-update'));
    }, 1000);
}


// ============================================================================
// Rules vs ML Comparison Chart
// ============================================================================
let rulesVsMLChart = null;

function updateRulesVsMLChart(data) {
    const ctx = document.getElementById('rulesVsMLChart');
    if (!ctx) return;
    const s = data.summary;

    const rulesWDR = s.wormhole_detection_rate != null ? (s.wormhole_detection_rate * 100) : 0;
    const rulesFPR = s.false_positive_rate != null ? (s.false_positive_rate * 100) : 0;
    const mlWDR = data.ml_available ? (data.ml_detection_rate || 0) : null;
    const mlFPR = data.ml_available ? (data.ml_false_positive_rate || 0) : null;

    const labels = ['Wormhole Detection Rate (%)', 'False Positive Rate (%)'];
    const datasets = [
        {
            label: 'Rule Engine',
            data: [rulesWDR, rulesFPR],
            backgroundColor: ['rgba(251,191,36,0.8)', 'rgba(239,68,68,0.6)'],
            borderColor: ['#fbbf24', '#ef4444'],
            borderWidth: 1,
        }
    ];
    if (mlWDR !== null) {
        datasets.push({
            label: 'Random Forest (ML)',
            data: [mlWDR, mlFPR],
            backgroundColor: ['rgba(139,92,246,0.8)', 'rgba(139,92,246,0.4)'],
            borderColor: ['#8b5cf6', '#8b5cf6'],
            borderWidth: 1,
        });
    }

    if (rulesVsMLChart) rulesVsMLChart.destroy();
    rulesVsMLChart = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8', font: { size: 10 } } },
                tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%` } }
            },
            scales: {
                x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8', font: { size: 10 }, callback: v => v + '%' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true, max: 100 }
            }
        }
    });
}

// ============================================================================
// Heterogeneity Table — fetched live from /api/heterogeneity_results
// ============================================================================
async function loadAndRenderHeteroTable() {
    const tbody = document.getElementById('heteroTableBody');
    if (!tbody) return;

    let data = [];
    try {
        const res = await fetch(`${API_BASE}/api/heterogeneity_results`);
        if (res.ok) {
            data = await res.json();
        }
    } catch (e) {
        // fall through to fallback
    }

    // Fallback to last-known results if CSV not present on server
    if (!data || data.error || data.length === 0) {
        data = [
            { profile: 'small_flat', attack_mode: 'out-of-band', wdr_mean: 0.0167, fpr_mean: 0.0133 },
            { profile: 'small_flat', attack_mode: 'encapsulation', wdr_mean: 0.0000, fpr_mean: 0.0000 },
            { profile: 'small_flat', attack_mode: 'intermittent', wdr_mean: 0.0286, fpr_mean: 0.0067 },
            { profile: 'medium_apartment', attack_mode: 'out-of-band', wdr_mean: 0.1405, fpr_mean: 0.0131 },
            { profile: 'medium_apartment', attack_mode: 'encapsulation', wdr_mean: 0.1670, fpr_mean: 0.0131 },
            { profile: 'medium_apartment', attack_mode: 'intermittent', wdr_mean: 0.1872, fpr_mean: 0.0164 },
            { profile: 'large_house', attack_mode: 'out-of-band', wdr_mean: 0.0648, fpr_mean: 0.0066 },
            { profile: 'large_house', attack_mode: 'encapsulation', wdr_mean: 0.0926, fpr_mean: 0.0093 },
            { profile: 'large_house', attack_mode: 'intermittent', wdr_mean: 0.0491, fpr_mean: 0.0079 },
        ];
    }

    const profiles = ['small_flat', 'medium_apartment', 'large_house'];
    const modes = ['out-of-band', 'encapsulation', 'intermittent'];
    tbody.innerHTML = '';
    modes.forEach(mode => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-800/30 transition-colors';
        let html = `<td class="px-3 py-2 font-medium text-slate-300 capitalize">${mode}</td>`;
        profiles.forEach(p => {
            const cell = data.find(r => r.profile === p && r.attack_mode === mode);
            if (cell) {
                const wdr = (cell.wdr_mean * 100).toFixed(0);
                const fpr = (cell.fpr_mean * 100).toFixed(0);
                const wdrColor = cell.wdr_mean > 0.15 ? 'text-green-400' : cell.wdr_mean > 0.05 ? 'text-amber-400' : 'text-slate-400';
                const fprColor = cell.fpr_mean < 0.02 ? 'text-green-400' : 'text-red-400';
                const stdev = cell.wdr_stdev != null ? ` ±${(cell.wdr_stdev * 100).toFixed(0)}%` : '';
                html += `<td class="px-3 py-2 text-center">
                    <span class="${wdrColor} font-bold">${wdr}%</span><span class="text-slate-600 text-xs">${stdev}</span>
                    <span class="text-slate-500 mx-1">WDR</span>
                    <span class="text-slate-500">/</span>
                    <span class="${fprColor} font-bold ml-1">${fpr}%</span>
                    <span class="text-slate-500">FPR</span>
                </td>`;
            } else {
                html += `<td class="px-3 py-2 text-center text-slate-500">N/A</td>`;
            }
        });
        tr.innerHTML = html;
        tbody.appendChild(tr);
    });
}

// Load hetero table on page load
document.addEventListener('DOMContentLoaded', loadAndRenderHeteroTable);
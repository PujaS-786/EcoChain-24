// Dashboard Controller for EcoChain 24

document.addEventListener("DOMContentLoaded", () => {
    fetchDashboardData();
    // Auto-refresh logs every 10 seconds
    setInterval(fetchLogs, 10000);
});

// Tab Switching logic
function switchTab(tabId) {
    // Update nav link active states
    document.querySelectorAll(".nav-links a").forEach(link => {
        link.classList.remove("active");
    });
    
    // Find link matching active tab and activate
    const activeLink = document.querySelector(`.nav-links a[href="#${tabId}"]`);
    if (activeLink) activeLink.classList.add("active");
    
    // Switch active view container
    document.querySelectorAll(".dashboard-tab-content").forEach(content => {
        content.classList.remove("active-tab");
    });
    
    const targetTab = document.getElementById(`${tabId}-tab`);
    if (targetTab) targetTab.classList.add("active-tab");
}

// REST Api Operations
async function fetchDashboardData() {
    try {
        await Promise.all([
            fetchStats(),
            fetchSuppliers(),
            fetchAnomalies(),
            fetchCompliance(),
            fetchRecommendations(),
            fetchLogs()
        ]);
    } catch (e) {
        showToast("Error loading registry data: " + e.message, "error");
    }
}

async function fetchStats() {
    const res = await fetch("/api/stats");
    const data = await res.json();
    
    document.getElementById("stat-co2-loc").innerText = data.total_co2e_location.toFixed(2) + " t";
    document.getElementById("stat-co2-mkt").innerText = data.total_co2e_market.toFixed(2) + " t";
    document.getElementById("stat-coverage").innerText = data.data_coverage_pct.toFixed(1) + "%";
    document.getElementById("stat-confidence").innerText = data.avg_confidence.toFixed(2);
    document.getElementById("stat-anomalies").innerText = data.open_anomalies;
    document.getElementById("stat-gaps").innerText = data.compliance_gaps;
}

async function fetchSuppliers() {
    const res = await fetch("/api/suppliers");
    const suppliers = await res.json();
    
    // Update summary table
    const summaryTable = document.getElementById("summary-suppliers-table");
    summaryTable.innerHTML = "";
    
    // Update full table
    const fullTable = document.getElementById("suppliers-table-body");
    fullTable.innerHTML = "";
    
    if (suppliers.length === 0) {
        summaryTable.innerHTML = `<tr><td colspan="5" class="empty-state">No suppliers audited yet.</td></tr>`;
        fullTable.innerHTML = `<tr><td colspan="7" class="empty-state">No profiles found. Run the pipeline.</td></tr>`;
        return;
    }
    
    suppliers.forEach(s => {
        const tierLetter = s.tier.replace("Tier ", "").toLowerCase();
        
        // Summary Table Row
        const sumRow = document.createElement("tr");
        sumRow.innerHTML = `
            <td><strong>${s.name}</strong></td>
            <td><span class="badge badge-${tierLetter}">${s.tier}</span></td>
            <td>${s.dq_score.toFixed(2)}</td>
            <td>${s.intensity.toFixed(4)}</td>
            <td>${s.trend}</td>
        `;
        summaryTable.appendChild(sumRow);
        
        // Full Table Row
        const fullRow = document.createElement("tr");
        fullRow.innerHTML = `
            <td><code>${s.supplier_id}</code></td>
            <td><strong>${s.name}</strong></td>
            <td><span class="badge badge-${tierLetter}">${s.tier}</span></td>
            <td>${s.dq_score.toFixed(2)}</td>
            <td>${s.intensity.toFixed(4)}</td>
            <td>${s.trend}</td>
            <td>${s.last_disclosure ? new Date(s.last_disclosure).toLocaleString() : "N/A"}</td>
        `;
        fullTable.appendChild(fullRow);
    });
}

async function fetchAnomalies() {
    const res = await fetch("/api/anomalies");
    const anomalies = await res.json();
    
    const summaryFeed = document.getElementById("summary-anomalies-list");
    summaryFeed.innerHTML = "";
    
    const fullBody = document.getElementById("anomalies-table-body");
    fullBody.innerHTML = "";
    
    const openAnms = anomalies.filter(a => a.status === "open");
    
    if (openAnms.length === 0) {
        summaryFeed.innerHTML = `<div class="empty-state">No anomalies logged.</div>`;
    } else {
        openAnms.forEach(a => {
            const isCrit = a.severity === "CRITICAL" ? "critical" : "";
            const item = document.createElement("div");
            item.className = `anomaly-item ${isCrit}`;
            item.innerHTML = `
                <div class="anomaly-item-header">
                    <span class="anomaly-title">${a.anomaly_type.toUpperCase()}</span>
                    <span class="badge badge-${a.severity.toLowerCase()}">${a.severity}</span>
                </div>
                <div class="anomaly-desc">${a.description}</div>
            `;
            summaryFeed.appendChild(item);
        });
    }
    
    if (anomalies.length === 0) {
        fullBody.innerHTML = `<div class="empty-state">No active anomalies in this reporting cycle.</div>`;
        return;
    }
    
    anomalies.forEach(a => {
        const severityClass = a.severity.toLowerCase();
        const card = document.createElement("div");
        card.className = `anomaly-card-full ${a.status} ${severityClass}`;
        
        let actionButton = "";
        if (a.status === "open") {
            actionButton = `<button class="btn btn-primary" onclick="openResolveModal('${a.anomaly_id}')">Resolve Override</button>`;
        } else {
            actionButton = `<span class="badge badge-met">RESOLVED (${a.resolved_by})</span>`;
        }
        
        card.innerHTML = `
            <div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="badge badge-${severityClass}">${a.severity}</span>
                    <h3>${a.anomaly_type.replace('_', ' ').toUpperCase()}</h3>
                </div>
                <p style="margin: 10px 0; color: #e2e8f0; font-size: 13px;">${a.description}</p>
                <div class="anomaly-meta">
                    <div><strong>Record ID:</strong> <code>${a.record_id}</code> | <strong>Supplier:</strong> <code>${a.supplier_id}</code></div>
                    <div style="margin-top: 5px;"><strong>Recommended Next Action:</strong> ${a.recommended_action}</div>
                    <div style="margin-top: 5px;"><strong>Detected At:</strong> ${new Date(a.detected_at).toLocaleString()}</div>
                </div>
            </div>
            <div>
                ${actionButton}
            </div>
        `;
        fullBody.appendChild(card);
    });
}

async function fetchCompliance() {
    const res = await fetch("/api/compliance");
    const compliance = await res.json();
    
    const body = document.getElementById("compliance-table-body");
    body.innerHTML = "";
    
    if (compliance.length === 0) {
        body.innerHTML = `<tr><td colspan="6" class="empty-state">No compliance audits checked. Run the pipeline.</td></tr>`;
        return;
    }
    
    compliance.forEach(c => {
        const statusClass = c.status.toLowerCase();
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><strong>${c.framework.replace('_', ' ')}</strong></td>
            <td><code>${c.requirement_id}</code></td>
            <td><span class="badge badge-${statusClass}">${c.status}</span></td>
            <td>${c.missing_data || "MET"}</td>
            <td><span class="badge badge-${c.risk_level === 'critical' ? 'd' : c.risk_level === 'high' ? 'c' : 'b'}">${c.risk_level.toUpperCase()}</span></td>
            <td>$${c.financial_exposure.toLocaleString()}</td>
        `;
        body.appendChild(row);
    });
}

async function fetchRecommendations() {
    const res = await fetch("/api/recommendations");
    const recs = await res.json();
    
    const body = document.getElementById("recommendations-table-body");
    body.innerHTML = "";
    
    if (recs.length === 0) {
        body.innerHTML = `<tr><td colspan="6" class="empty-state">No optimization opportunities computed yet. Run pipeline.</td></tr>`;
        return;
    }
    
    recs.forEach(r => {
        const costStr = r.estimated_cost_delta > 0 
            ? `+$${r.estimated_cost_delta.toLocaleString()}/yr` 
            : `-$${Math.abs(r.estimated_cost_delta).toLocaleString()}/yr`;
        const costClass = r.estimated_cost_delta > 0 ? "color: #10b981;" : "color: #ef4444;";
        
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><strong>${r.category}</strong></td>
            <td style="font-weight: bold; color: #60a5fa;">${r.estimated_co2e_saving.toFixed(1)} t</td>
            <td><span class="badge badge-${r.implementation_effort === 'low' ? 'a' : r.implementation_effort === 'medium' ? 'b' : 'c'}">${r.implementation_effort.toUpperCase()}</span></td>
            <td style="${costClass}">${costStr}</td>
            <td>${r.confidence_in_estimate.toUpperCase()}</td>
            <td><code>${r.data_basis.join(', ')}</code></td>
        `;
        body.appendChild(row);
    });
}

async function fetchLogs() {
    const res = await fetch("/api/logs");
    const logs = await res.json();
    
    const terminal = document.getElementById("audit-log-body");
    terminal.innerHTML = "";
    
    if (logs.length === 0) {
        terminal.innerHTML = `<div class="terminal-line">[SYSTEM]: Audit database empty. Run orchestrator.</div>`;
        return;
    }
    
    // Display in chronological order
    const chronological = [...logs].reverse();
    
    chronological.forEach(l => {
        const line = document.createElement("div");
        line.className = "terminal-line";
        
        let colorClass = "";
        if (l.action.includes("success") || l.action.includes("verified")) colorClass = "success";
        else if (l.action.includes("quarantine") || l.action.includes("warning") || l.action.includes("conflict")) colorClass = "warning";
        else if (l.action.includes("failure") || l.action.includes("tamper")) colorClass = "danger";
        
        line.innerHTML = `
            <span style="color: #64748b;">[${new Date(l.timestamp).toLocaleTimeString()}]</span> 
            <span style="color: #f472b6; font-weight: 600;">[${l.agent_name.toUpperCase()}]</span> 
            <span class="${colorClass}">${l.action.toUpperCase()}</span> 
            - ${JSON.stringify(l.details)}
            <br>
            <span style="color: #64748b; font-size: 10px; padding-left: 20px;">Prev: <code>${l.previous_hash.slice(0, 16)}...</code> | Content Hash: <code>${l.content_hash.slice(0, 16)}...</code></span>
        `;
        terminal.appendChild(line);
    });
    
    // Auto Scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
}

// Button actions
async function triggerPipeline() {
    showToast("⚙️ Orchestrator: Starting carbon pipeline run...", "success");
    try {
        const res = await fetch("/api/pipeline/run", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({period: "2024-Q1", load_samples: true})
        });
        const data = await res.json();
        
        if (data.status === "success") {
            showToast(`✅ Carbon pipeline complete. Processed ${data.processed_records} records.`, "success");
            fetchDashboardData();
        } else {
            showToast("❌ Pipeline incomplete: " + data.message, "error");
        }
    } catch (e) {
        showToast("Error executing pipeline: " + e.message, "error");
    }
}

async function verifyAuditTrail() {
    showToast("🛡️ Cryptographic Agent: Verifying log hash chains...", "success");
    try {
        const res = await fetch("/api/logs/verify");
        const data = await res.json();
        
        if (data.valid) {
            showToast("🛡️ Audit log hash chains verified! 0 tampered entries detected.", "success");
        } else {
            showToast("⚠️ SECURITY ALERT: Audit trail hash mismatch detected!", "error");
        }
        fetchLogs();
    } catch (e) {
        showToast("Error verifying audit trail: " + e.message, "error");
    }
}

function exportAuditTrail() {
    // Emulates a direct download by linking to a mock CSV generation
    showToast("📥 Exporting audit trail to CSV...", "success");
    window.open("/api/logs?format=csv");
}

// Modal Resolution management
function openResolveModal(anomalyId) {
    document.getElementById("modal-anomaly-id").value = anomalyId;
    document.getElementById("resolution-modal").style.display = "flex";
}

function closeModal() {
    document.getElementById("resolution-modal").style.display = "none";
}

async function submitResolution() {
    const id = document.getElementById("modal-anomaly-id").value;
    const reason = document.getElementById("reason-code").value;
    const approver = document.getElementById("approver-name").value;
    
    if (!approver) {
        showToast("Approver name is required.", "error");
        return;
    }
    
    try {
        const res = await fetch("/api/anomalies/resolve", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({anomaly_id: id, reason_code: reason, approver: approver})
        });
        const data = await res.json();
        
        if (data.status === "success") {
            showToast("✅ Anomaly override logged successfully.", "success");
            closeModal();
            fetchDashboardData();
        } else {
            showToast("Error saving override: " + data.message, "error");
        }
    } catch (e) {
        showToast("Network error submitting override: " + e.message, "error");
    }
}

// Toast helper
function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.className = `toast ${type}`;
    toast.innerText = message;
    toast.style.display = "block";
    
    setTimeout(() => {
        toast.style.display = "none";
    }, 4000);
}

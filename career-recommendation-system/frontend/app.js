'use strict';

/* ═══════════════════════════════════════════
   CONSTANTS & STATE
═══════════════════════════════════════════ */
const API_URL = 'http://127.0.0.1:8000/api/resume/upload';
const HEALTH_URL = 'http://127.0.0.1:8000/health';
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];
const LS_KEY = 'careerlens_progress';

let selectedFile     = null;
let apiData          = null;
let activeCareerName = null;
let activeSkillName  = null;

/* ═══════════════════════════════════════════
   DOM REFS
═══════════════════════════════════════════ */
const sidebar           = document.getElementById('sidebar');
const sidebarToggle     = document.getElementById('sidebarToggle');
const topbarTitle       = document.getElementById('topbarTitle');
const backendStatusText = document.getElementById('backendStatusText');
const statusDot         = document.querySelector('.status-dot');

const dropZone          = document.getElementById('dropZone');
const fileInput         = document.getElementById('fileInput');
const fileInfo          = document.getElementById('fileInfo');
const fileName          = document.getElementById('fileName');
const fileRemove        = document.getElementById('fileRemove');
const uploadError       = document.getElementById('uploadError');
const errorMessage      = document.getElementById('errorMessage');
const analyzeBtn        = document.getElementById('analyzeBtn');
const btnLoader         = document.getElementById('btnLoader');
const analyzeAnotherBtn = document.getElementById('analyzeAnotherBtn');

/* ═══════════════════════════════════════════
   LIVE BACKEND CONNECTION HEALTH MONITOR
═══════════════════════════════════════════ */
async function checkBackendHealth() {
  if (!backendStatusText) return;
  try {
    const res = await fetch(HEALTH_URL, { method: 'GET' });
    if (res.ok) {
      backendStatusText.textContent = 'Connected (Online)';
      if (statusDot) {
        statusDot.classList.remove('offline');
        statusDot.classList.add('online');
      }
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    backendStatusText.textContent = 'Disconnected';
    if (statusDot) {
      statusDot.classList.remove('online');
      statusDot.classList.add('offline');
    }
  }
}
checkBackendHealth();
setInterval(checkBackendHealth, 10000);

/* DOM REFS — result containers */
const resumeSummaryBody   = document.getElementById('resumeSummaryBody');
const extractedSkillsBody = document.getElementById('extractedSkillsBody');
const careerRecsBody      = document.getElementById('careerRecsBody');
const clusterAnalysisCard = document.getElementById('clusterAnalysisCard');
const clusterAnalysisBody = document.getElementById('clusterAnalysisBody');
const ensembleAnalysisCard = document.getElementById('ensembleAnalysisCard');
const ensembleAnalysisBody = document.getElementById('ensembleAnalysisBody');
const careerAnalysisBody  = document.getElementById('careerAnalysisBody');
const unifiedExplanationBody = document.getElementById('unifiedExplanationBody');
const whatToLearnBody     = document.getElementById('whatToLearnBody');
const recommendedCoursesBody = document.getElementById('recommendedCoursesBody');
const selectedCareerBadge = document.getElementById('selectedCareerBadge');
const roadmapCareerBadge  = document.getElementById('roadmapCareerBadge');
const roadmapProgressSummary = document.getElementById('roadmapProgressSummary');
const careerRoadmapStagesBody = document.getElementById('careerRoadmapStagesBody');
const roadmapSkillList    = document.getElementById('roadmapSkillList');
const roadmapPlaceholder  = document.getElementById('roadmapPlaceholder');
const roadmapContent      = document.getElementById('roadmapContent');
const roadmapSkillName    = document.getElementById('roadmapSkillName');
const roadmapSkillWhy     = document.getElementById('roadmapSkillWhy');
const roadmapRecText      = document.getElementById('roadmapRecText');
const roadmapStages       = document.getElementById('roadmapStages');
const learningStrategyBody = document.getElementById('learningStrategyBody');
const ytButtons           = document.getElementById('ytButtons');
const progressTrackerBody = document.getElementById('progressTrackerBody');
const progressSummary     = document.getElementById('progressSummary');
const progressCareerBadge = document.getElementById('progressCareerBadge');
const compareSelectA      = document.getElementById('compareSelectA');
const compareSelectB      = document.getElementById('compareSelectB');
const swapCompareBtn      = document.getElementById('swapCompareBtn');
const resetCompareBtn     = document.getElementById('resetCompareBtn');
const careerComparisonBody= document.getElementById('careerComparisonBody');

/* ═══════════════════════════════════════════
   SECTION TITLES MAP
═══════════════════════════════════════════ */
const SECTION_TITLES = {
  'section-home':     'Dashboard',
  'section-upload':   'Resume Analysis',
  'section-careers':  'Career Matches',
  'section-compare':  'Career Comparison',
  'section-skills':   'Skill Gap Analysis',
  'section-roadmap':  'Learning Roadmap',
  'section-resources':'Learning Resources',
  'section-progress': 'Progress Tracker'
};

/* ═══════════════════════════════════════════
   SIDEBAR NAVIGATION
═══════════════════════════════════════════ */
function showSection(sectionId) {
  /* Scroll workspace section into view */
  const target = document.getElementById(sectionId);
  if (!target) return;

  /* Remove hidden from target, keep all others visible (page scrolls) */
  target.hidden = false;
  setTimeout(() => {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 30);

  /* Update active sidebar link */
  document.querySelectorAll('.sidebar-link').forEach(link => {
    link.classList.toggle('active', link.dataset.section === sectionId);
  });

  /* Update topbar title */
  if (topbarTitle) topbarTitle.textContent = SECTION_TITLES[sectionId] || 'Dashboard';

  /* Close sidebar on mobile after navigation */
  if (window.innerWidth <= 900 && sidebar) {
    sidebar.classList.remove('open');
    if (sidebarToggle) sidebarToggle.classList.remove('open');
  }
}

/* Wire all sidebar-link clicks (sidebar nav + topbar button + hero buttons) */
document.querySelectorAll('.sidebar-link').forEach(link => {
  link.addEventListener('click', e => {
    const sectionId = link.dataset.section;
    if (!sectionId) return;
    e.preventDefault();
    showSection(sectionId);
  });
});

/* Mobile sidebar toggle */
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    sidebarToggle.classList.toggle('open');
  });
}

/* ═══════════════════════════════════════════
   BACKEND HEALTH CHECK
═══════════════════════════════════════════ */
async function checkBackendHealth() {
  try {
    const res = await fetch(HEALTH_URL, { method: 'GET' });
    if (res.ok) {
      if (statusDot) { statusDot.classList.add('online'); statusDot.classList.remove('offline'); }
      if (backendStatusText) backendStatusText.textContent = 'Online';
    } else {
      throw new Error('not ok');
    }
  } catch (_) {
    if (statusDot) { statusDot.classList.add('offline'); statusDot.classList.remove('online'); }
    if (backendStatusText) backendStatusText.textContent = 'Offline';
  }
}
checkBackendHealth();

/* ═══════════════════════════════════════════
   FILE VALIDATION & HANDLING
═══════════════════════════════════════════ */
function getExtension(name) {
  return name.slice(name.lastIndexOf('.')).toLowerCase();
}
function isValidFile(file) {
  return ALLOWED_EXTENSIONS.includes(getExtension(file.name));
}
function setFile(file) {
  if (!isValidFile(file)) {
    showError('Invalid file type. Please upload a PDF, DOCX, or TXT file.');
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  fileInfo.hidden = false;
  hideError();
  analyzeBtn.disabled = false;
}
function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  fileInfo.hidden = true;
  fileName.textContent = '';
  analyzeBtn.disabled = true;
  hideError();
}
function showError(msg) {
  errorMessage.textContent = msg;
  uploadError.hidden = false;
}
function hideError() {
  uploadError.hidden = true;
  errorMessage.textContent = '';
}

fileInput.addEventListener('change', () => {
  if (fileInput.files.length) setFile(fileInput.files[0]);
});
fileRemove.addEventListener('click', clearFile);

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') fileInput.click();
});
['dragenter', 'dragover'].forEach(evt => {
  dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
});
['dragleave', 'drop'].forEach(evt => {
  dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove('drag-over'); });
});
dropZone.addEventListener('drop', e => {
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});

/* ═══════════════════════════════════════════
   ANALYZE BUTTON & API CALL
═══════════════════════════════════════════ */
analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  await analyzeResume(selectedFile);
});

async function analyzeResume(file) {
  setLoadingState(true);
  hideError();

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(API_URL, { method: 'POST', body: formData });

    if (!response.ok) {
      let detail = `Server error (${response.status})`;
      try { const err = await response.json(); if (err.detail) detail = err.detail; } catch (_) {}
      throw new Error(detail);
    }

    const data = await response.json();
    apiData = data;
    renderResults(data);

  } catch (err) {
    if (err.name === 'TypeError') {
      showError('Cannot reach the backend. Make sure the FastAPI server is running on http://127.0.0.1:8000');
    } else {
      showError(err.message);
    }
  } finally {
    setLoadingState(false);
  }
}

function setLoadingState(loading) {
  analyzeBtn.disabled = loading;
  document.querySelector('.btn-text').style.display = loading ? 'none' : '';
  btnLoader.style.display = loading ? 'flex' : 'none';
}

/* ═══════════════════════════════════════════
   SHOW RESULTS & ANALYZE ANOTHER
═══════════════════════════════════════════ */
function showResults() {
  /* Unhide result sections so they are reachable */
  ['section-careers', 'section-compare', 'section-skills', 'section-roadmap',
   'section-resources', 'section-progress'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.hidden = false;
  });
  /* Navigate to career matches */
  showSection('section-careers');
}

analyzeAnotherBtn.addEventListener('click', () => {
  apiData = null;
  activeCareerName = null;
  activeSkillName = null;
  compareCareerA = null;
  compareCareerB = null;
  clearFile();
  showSection('section-upload');
});


/* ═══════════════════════════════════════════
   RENDER HELPERS
═══════════════════════════════════════════ */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function skillTag(skill, colorClass) {
  return `<span class="result-skill-tag ${colorClass}">${escHtml(skill)}</span>`;
}

function scoreColor(score) {
  if (score >= 70) return 'var(--green)';
  if (score >= 40) return 'var(--orange)';
  return 'var(--pink)';
}

function pct(val) {
  return Math.min(100, Math.max(0, Number(val) || 0));
}

/* ═══════════════════════════════════════════
   RENDER: RESUME SUMMARY
═══════════════════════════════════════════ */
function renderResumeSummary(resume) {
  resumeSummaryBody.innerHTML = `
    <div class="summary-row">
      <span class="summary-label">File Name</span>
      <span class="summary-value">${escHtml(resume.filename || '')}</span>
    </div>
    <div class="summary-row">
      <span class="summary-label">File Type</span>
      <span class="summary-value">${escHtml((resume.file_type || '').toUpperCase())}</span>
    </div>
    <div class="summary-row">
      <span class="summary-label">Characters Extracted</span>
      <span class="summary-value">${(resume.character_count || 0).toLocaleString()}</span>
    </div>
  `;
}

/* ═══════════════════════════════════════════
   RENDER: EXTRACTED SKILLS
═══════════════════════════════════════════ */
function renderExtractedSkills(skills) {
  const list = skills.extracted_skills || [];
  const categoriesCount = Object.keys(skills.skill_categories || {}).length;

  if (!list.length) {
    extractedSkillsBody.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">No skills detected.</p>';
    return;
  }

  const tags = list.map(s => skillTag(s, 'tag-cyan')).join('');
  extractedSkillsBody.innerHTML = `
    <div class="summary-row" style="margin-bottom:16px;">
      <span class="summary-label">Skills Identified</span>
      <span class="summary-value">${list.length}</span>
    </div>
    <div class="summary-row" style="margin-bottom:20px;">
      <span class="summary-label">Skill Categories</span>
      <span class="summary-value">${categoriesCount}</span>
    </div>
    <div class="skills-wrap">${tags}</div>
  `;
}

/* ═══════════════════════════════════════════
   RENDER: CLUSTER ANALYSIS
═══════════════════════════════════════════ */
function renderClusterAnalysis(data) {
  const cluster = data.cluster_analysis;
  if (!cluster || cluster.status === 'fallback') {
    if (clusterAnalysisCard) clusterAnalysisCard.hidden = true;
    return;
  }

  if (clusterAnalysisCard) clusterAnalysisCard.hidden = false;

  const similarity       = pct(cluster.profile_cluster_similarity);
  const dominantSkills   = (cluster.dominant_skills || []).map(s => skillTag(s, 'tag-purple')).join('');
  const matchedSkills    = (cluster.matched_cluster_skills || []).map(s => skillTag(s, 'tag-green')).join('');
  const similarCareers   = (cluster.similar_career_group || []).map(c =>
    `<span class="cluster-career-tag">${escHtml(c)}</span>`
  ).join('');
  const clusterCount     = cluster.cluster_count || '—';

  clusterAnalysisBody.innerHTML = `
    <div class="cluster-summary">
      <div class="cluster-name-row">
        <span class="cluster-label">Matched Cluster</span>
        <span class="cluster-name">${escHtml(cluster.cluster_name || 'Unknown')}</span>
      </div>
      <div class="cluster-similarity-row">
        <span class="cluster-label">Cluster Similarity</span>
        <div class="cluster-sim-bar-wrap">
          <div class="cluster-sim-bar-track">
            <div class="cluster-sim-bar-fill" style="width:${similarity}%"></div>
          </div>
          <span class="cluster-sim-pct" style="color:${scoreColor(similarity)}">${similarity}%</span>
        </div>
      </div>
      <div class="cluster-count-row">
        <span class="cluster-label">Total Clusters</span>
        <span class="cluster-count-value">${clusterCount}</span>
      </div>
    </div>
    <div class="cluster-details">
      <div class="cluster-detail-col">
        <div class="cluster-detail-title">🧠 Dominant Cluster Skills</div>
        <div class="skills-wrap">${dominantSkills || '<span style="color:var(--text-muted);font-size:0.8rem;">None</span>'}</div>
      </div>
      <div class="cluster-detail-col">
        <div class="cluster-detail-title">✓ Your Matching Skills</div>
        <div class="skills-wrap">${matchedSkills || '<span style="color:var(--text-muted);font-size:0.8rem;">No overlap detected</span>'}</div>
      </div>
    </div>
    ${similarCareers ? `
    <div class="cluster-careers-section">
      <div class="cluster-detail-title">🏢 Similar Careers in This Cluster</div>
      <div class="cluster-careers-wrap">${similarCareers}</div>
    </div>` : ''}
    <div class="cluster-explanation">
      <span class="cluster-explanation-icon">💡</span>
      <span>${escHtml(cluster.explanation || '')}</span>
    </div>
  `;
}

/* ═══════════════════════════════════════════
   RENDER: ENSEMBLE ANALYSIS
═══════════════════════════════════════════ */
function renderEnsembleAnalysis(data) {
  const ens = data.ensemble_analysis;
  if (!ens || ens.status === 'fallback') {
    if (ensembleAnalysisCard) ensembleAnalysisCard.hidden = true;
    return;
  }

  if (ensembleAnalysisCard) ensembleAnalysisCard.hidden = false;

  const metrics = ens.model_metrics || {};
  const acc = metrics.ensemble_accuracy ? pct(metrics.ensemble_accuracy * 100) : '—';
  const rfAcc = metrics.random_forest_accuracy ? pct(metrics.random_forest_accuracy * 100) : '—';
  const gbAcc = metrics.gradient_boosting_accuracy ? pct(metrics.gradient_boosting_accuracy * 100) : '—';
  const cvAcc = metrics.cross_validation_mean_accuracy ? pct(metrics.cross_validation_mean_accuracy * 100) : '—';
  const topPredictions = ens.top_predictions || [];
  const topFeatures = ens.top_features || [];

  const predictionsHtml = topPredictions.map(p => `
    <div class="ens-pred-item">
      <div class="ens-pred-header">
        <span class="ens-pred-name">${escHtml(p.career)}</span>
        <span class="ens-pred-conf">${pct(p.confidence)}%</span>
      </div>
      <div class="ens-pred-bar-track">
        <div class="ens-pred-bar-fill" style="width:${pct(p.confidence)}%"></div>
      </div>
      <div class="ens-pred-models">
        <span>RF: ${pct(p.rf_probability)}%</span>
        <span>GB: ${pct(p.gb_probability)}%</span>
        <span class="ens-agree-tag ${p.model_agreement === 'agree' ? 'agree' : 'split'}">${escHtml(p.model_agreement)}</span>
      </div>
    </div>
  `).join('');

  const topSkillsHtml = (ens.contributing_skills || []).map(s =>
    `<span class="result-skill-tag tag-cyan">${escHtml(s.skill)} <small>(${s.importance})</small></span>`
  ).join('');

  ensembleAnalysisBody.innerHTML = `
    <div class="ensemble-metrics-grid">
      <div class="ens-metric-card">
        <span class="ens-metric-label">Ensemble Accuracy</span>
        <span class="ens-metric-value">${acc}%</span>
        <span class="ens-metric-sub">VotingClassifier (Soft)</span>
      </div>
      <div class="ens-metric-card">
        <span class="ens-metric-label">Random Forest</span>
        <span class="ens-metric-value">${rfAcc}%</span>
        <span class="ens-metric-sub">160 Estimators</span>
      </div>
      <div class="ens-metric-card">
        <span class="ens-metric-label">Gradient Boosting</span>
        <span class="ens-metric-value">${gbAcc}%</span>
        <span class="ens-metric-sub">35 Estimators</span>
      </div>
      <div class="ens-metric-card">
        <span class="ens-metric-label">5-Fold CV Mean</span>
        <span class="ens-metric-value">${cvAcc}%</span>
        <span class="ens-metric-sub">Stratified K-Fold</span>
      </div>
    </div>

    ${topPredictions.length ? `
    <div class="ens-predictions-section">
      <div class="cluster-detail-title">🎯 Top Ensemble Recommended Roles</div>
      <div class="ens-predictions-grid">${predictionsHtml}</div>
    </div>` : ''}

    ${topSkillsHtml ? `
    <div class="ens-features-section">
      <div class="cluster-detail-title">⭐ Contributing Resume Features (Feature Importance)</div>
      <div class="skills-wrap">${topSkillsHtml}</div>
    </div>` : ''}

    <div class="ensemble-explanation">
      <span class="cluster-explanation-icon">🤖</span>
      <span>${escHtml(ens.explanation || '')}</span>
    </div>
  `;
}

/* ═══════════════════════════════════════════
   RENDER: CAREER RECOMMENDATION CARDS
═══════════════════════════════════════════ */
function renderCareerRecs(recs) {
  if (!recs || !recs.length) {
    careerRecsBody.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">No recommendations available.</p>';
    return;
  }

  careerRecsBody.innerHTML = recs.map((rec, i) => {
    const finalScore = pct(rec.final_score !== undefined ? rec.final_score : rec.final_recommendation_score || rec.compatibility_score);
    const compatScore = pct(rec.compatibility_score);
    const clusterScore = pct(rec.cluster_relevance_score || rec.cluster_relevance || 0);
    const ensembleScore = pct(rec.ensemble_confidence || rec.ensemble_prediction_score || 0);
    const explanation = rec.explanation || '';

    const sc = rec.score_components || {};
    const weights = sc.weights || {};
    const weightedContribs = sc.weighted_contributions || {};

    const skillWeight = rec.skill_weight !== undefined ? rec.skill_weight : Math.round((weights.skill_match || 0.60) * 100);
    const clusterWeight = rec.cluster_weight !== undefined ? rec.cluster_weight : Math.round((weights.cluster_relevance || 0.20) * 100);
    const ensembleWeight = rec.ensemble_weight !== undefined ? rec.ensemble_weight : Math.round((weights.ensemble_prediction || 0.20) * 100);

    const skillContrib = rec.skill_contribution !== undefined ? rec.skill_contribution : (weightedContribs.skill_match !== undefined ? weightedContribs.skill_match : +(compatScore * (skillWeight / 100)).toFixed(1));
    const clusterContrib = rec.cluster_contribution !== undefined ? rec.cluster_contribution : (weightedContribs.cluster_relevance !== undefined ? weightedContribs.cluster_relevance : +(clusterScore * (clusterWeight / 100)).toFixed(1));
    const ensembleContrib = rec.ensemble_contribution !== undefined ? rec.ensemble_contribution : (weightedContribs.ensemble_prediction !== undefined ? weightedContribs.ensemble_prediction : +(ensembleScore * (ensembleWeight / 100)).toFixed(1));

    return `
    <div class="career-card" data-career="${escHtml(rec.career)}">
      <div class="career-card-top">
        <div class="career-card-rank">${i + 1}</div>
        <div class="career-card-info">
          <div class="career-card-name-row">
            <span class="career-card-name">${escHtml(rec.career)}</span>
            ${rec.cluster_alignment ? '<span class="cluster-badge">✓ Cluster Aligned</span>' : ''}
          </div>
          <div class="career-card-desc">${escHtml(rec.description || '')}</div>
        </div>
        <div class="career-card-score-box">
          <div class="career-card-score">${finalScore}%</div>
          <span class="score-type-label">Hybrid Match</span>
          <button class="btn-compare-card" onclick="event.stopPropagation(); quickCompareCareer('${escHtml(rec.career)}')" title="Compare this career with another">⚖️ Compare</button>
        </div>
      </div>

      <div class="hybrid-breakdown-pills">
        <span class="breakdown-pill pill-compat" title="Primary Rule-Based Match">🎯 Skill Match: <strong>${compatScore}%</strong></span>
        <span class="breakdown-pill pill-cluster" title="K-Means Cluster Proximity">🔬 Cluster: <strong>${clusterScore}%</strong></span>
        <span class="breakdown-pill pill-ensemble" title="VotingClassifier Probability">🤖 Ensemble: <strong>${ensembleScore}%</strong></span>
      </div>

      <div class="career-card-bars">
        <div class="career-bar-row">
          <span class="career-bar-label">Hybrid Recommendation</span>
          <div class="career-bar-track"><div class="career-bar-fill fill-hybrid" style="width:${finalScore}%"></div></div>
          <span class="career-bar-pct" style="color:var(--cyan)">${finalScore}%</span>
        </div>
        <div class="career-bar-row">
          <span class="career-bar-label">Skill Compatibility</span>
          <div class="career-bar-track"><div class="career-bar-fill fill-compat" style="width:${compatScore}%"></div></div>
          <span class="career-bar-pct">${compatScore}%</span>
        </div>
        <div class="career-bar-row">
          <span class="career-bar-label">Required Skill Match</span>
          <div class="career-bar-track"><div class="career-bar-fill fill-required" style="width:${pct(rec.required_skill_match)}%"></div></div>
          <span class="career-bar-pct">${pct(rec.required_skill_match)}%</span>
        </div>
      </div>

      <details class="score-breakdown-details" onclick="event.stopPropagation()">
        <summary class="score-breakdown-summary">
          <span>📊 View Score Breakdown</span>
          <span class="score-breakdown-arrow">▾</span>
        </summary>
        <div class="score-breakdown-content">
          <p class="score-breakdown-desc">Your final recommendation score combines direct skill match with cluster relevance and ensemble model support:</p>
          <div class="score-breakdown-table">
            <div class="score-breakdown-row">
              <span class="sb-col-label">🎯 Skill Compatibility:</span>
              <span class="sb-col-calc">${compatScore}% × ${skillWeight}% weight</span>
              <span class="sb-col-points">= <strong>${skillContrib} pts</strong></span>
            </div>
            <div class="score-breakdown-row">
              <span class="sb-col-label">🔬 Cluster Relevance:</span>
              <span class="sb-col-calc">${clusterScore}% × ${clusterWeight}% weight</span>
              <span class="sb-col-points">= <strong>${clusterContrib} pts</strong></span>
            </div>
            <div class="score-breakdown-row">
              <span class="sb-col-label">🤖 Ensemble Support:</span>
              <span class="sb-col-calc">${ensembleScore}% × ${ensembleWeight}% weight</span>
              <span class="sb-col-points">= <strong>${ensembleContrib} pts</strong></span>
            </div>
            <div class="score-breakdown-row total-row">
              <span class="sb-col-label">⭐ Final Recommendation Score:</span>
              <span class="sb-col-calc">${skillContrib} + ${clusterContrib} + ${ensembleContrib}</span>
              <span class="sb-col-points">= <strong>${finalScore}%</strong></span>
            </div>
          </div>
        </div>
      </details>

      ${explanation ? `
      <div class="rec-explanation-box">
        <span class="rec-exp-icon">💡</span>
        <span class="rec-exp-text">${escHtml(explanation)}</span>
      </div>` : ''}
    </div>
  `;
  }).join('');

  /* Wire click via delegation — no inline onclick, safe for any career name */
  careerRecsBody.querySelectorAll('.career-card').forEach(card => {
    card.addEventListener('click', () => selectCareer(card.dataset.career));
  });
}

/* ═══════════════════════════════════════════
   SELECT CAREER — links cards → analysis
═══════════════════════════════════════════ */
function selectCareer(careerName) {
  activeCareerName = careerName;

  /* Highlight selected card */
  document.querySelectorAll('.career-card').forEach(card => {
    card.classList.toggle('selected', card.dataset.career === careerName);
  });

  /* Find matching career_analysis entry */
  const analysis = (apiData && apiData.career_analysis) ? apiData.career_analysis : [];
  const entry = analysis.find(a => a.career === careerName) || null;

  /* Update badge */
  if (selectedCareerBadge) selectedCareerBadge.textContent = careerName;

  /* Render skill analysis panel */
  renderSkillAnalysis(entry);

  /* Render unified explainability breakdown */
  renderUnifiedExplanation(entry);

  /* Render what-to-learn panel */
  renderWhatToLearn(entry, careerName);

  /* Render course & certification recommendations */
  renderCourseRecommendations(entry);

  /* Render career progression roadmap (6 stages) */
  renderCareerRoadmap(entry);

  /* Refresh roadmap skill list */
  renderRoadmapSkillList(entry);

  /* Refresh progress tracker */
  renderProgressTracker();
}

/* ═══════════════════════════════════════════
   RENDER: UNIFIED EXPLAINABILITY BREAKDOWN
═══════════════════════════════════════════ */
function renderUnifiedExplanation(entry) {
  if (!unifiedExplanationBody) return;
  if (!entry || !entry.unified_explanation) {
    unifiedExplanationBody.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">Select a career to view explainability breakdown.</p>';
    return;
  }

  const exp = entry.unified_explanation;
  const sb = exp.score_breakdown || {};
  const ml = exp.ml_influence || {};
  const lr = exp.learning_rationale || {};
  const strengths = exp.key_strengths || [];
  const gaps = exp.critical_gaps || [];

  const strengthsHtml = strengths.map(s => `
    <div class="exp-strength-item">
      <span class="exp-skill-name">✓ ${escHtml(s.skill)}</span>
      <span class="exp-badge ${s.is_required ? 'badge-req' : 'badge-pref'}">${escHtml(s.type)}</span>
    </div>
  `).join('') || '<span style="color:var(--text-muted);font-size:0.8rem;">No direct matching skills recorded</span>';

  const gapsHtml = gaps.map(g => `
    <div class="exp-gap-item">
      <span class="exp-gap-name">✗ ${escHtml(g.skill)}</span>
      <span class="exp-urgency-tag">${escHtml(g.urgency)}</span>
    </div>
  `).join('') || '<span style="color:var(--text-muted);font-size:0.8rem;">No critical gaps remaining!</span>';

  const scWeights = sb.weights || {};
  const scContribs = sb.weighted_contributions || {};
  const scSkillWeight = sb.skill_weight !== undefined ? sb.skill_weight : Math.round((scWeights.skill_match || 0.60) * 100);
  const scClusterWeight = sb.cluster_weight !== undefined ? sb.cluster_weight : Math.round((scWeights.cluster_relevance || 0.20) * 100);
  const scEnsembleWeight = sb.ensemble_weight !== undefined ? sb.ensemble_weight : Math.round((scWeights.ensemble_prediction || 0.20) * 100);

  const scSkillContrib = sb.skill_contribution !== undefined ? sb.skill_contribution : (scContribs.skill_match !== undefined ? scContribs.skill_match : scContribs.skill_compatibility || 0);
  const scClusterContrib = sb.cluster_contribution !== undefined ? sb.cluster_contribution : (scContribs.cluster_relevance || 0);
  const scEnsembleContrib = sb.ensemble_contribution !== undefined ? sb.ensemble_contribution : (scContribs.ensemble_prediction || 0);

  unifiedExplanationBody.innerHTML = `
    <!-- Executive Summary Box -->
    <div class="exp-summary-banner">
      <span class="exp-summary-icon">💡</span>
      <div class="exp-summary-text">${escHtml(exp.executive_summary || '')}</div>
    </div>

    <!-- Strengths & Gaps Grid -->
    <div class="exp-grid-2col">
      <div class="exp-panel">
        <div class="exp-panel-title">🌟 Your Verified Strengths</div>
        <div class="exp-strengths-list">${strengthsHtml}</div>
      </div>
      <div class="exp-panel">
        <div class="exp-panel-title">⚠️ Priority Gaps to Close</div>
        <div class="exp-gaps-list">${gapsHtml}</div>
      </div>
    </div>

    <!-- Transparent Score Math Formula -->
    <div class="exp-math-card">
      <div class="exp-math-title">📐 Transparent Score Calculation Formula</div>
      <div class="exp-math-formula">${escHtml(sb.math_formula_explanation || '')}</div>
      <p class="score-breakdown-desc" style="margin: 10px 0 12px 0;">Your final recommendation score combines direct skill match with cluster relevance and ensemble model support:</p>
      <div class="score-breakdown-table" style="margin-bottom:14px;">
        <div class="score-breakdown-row">
          <span class="sb-col-label">🎯 Skill Compatibility:</span>
          <span class="sb-col-calc">${pct(sb.compatibility_score)}% × ${scSkillWeight}% weight</span>
          <span class="sb-col-points">= <strong>${scSkillContrib} pts</strong></span>
        </div>
        <div class="score-breakdown-row">
          <span class="sb-col-label">🔬 Cluster Relevance:</span>
          <span class="sb-col-calc">${pct(sb.cluster_relevance)}% × ${scClusterWeight}% weight</span>
          <span class="sb-col-points">= <strong>${scClusterContrib} pts</strong></span>
        </div>
        <div class="score-breakdown-row">
          <span class="sb-col-label">🤖 Ensemble Support:</span>
          <span class="sb-col-calc">${pct(sb.ensemble_confidence)}% × ${scEnsembleWeight}% weight</span>
          <span class="sb-col-points">= <strong>${scEnsembleContrib} pts</strong></span>
        </div>
        <div class="score-breakdown-row total-row">
          <span class="sb-col-label">⭐ Final Recommendation Score:</span>
          <span class="sb-col-calc">${scSkillContrib} + ${scClusterContrib} + ${scEnsembleContrib}</span>
          <span class="sb-col-points">= <strong>${pct(sb.final_score)}%</strong></span>
        </div>
      </div>
      <div class="exp-math-pills">
        <span class="math-pill pill-green">Skill Compatibility: <strong>${pct(sb.compatibility_score)}%</strong></span>
        <span class="math-pill pill-purple">Cluster Relevance: <strong>${pct(sb.cluster_relevance)}%</strong></span>
        <span class="math-pill pill-cyan">Ensemble Support: <strong>${pct(sb.ensemble_confidence)}%</strong></span>
        <span class="math-pill pill-gold">Final Hybrid Score: <strong>${pct(sb.final_score)}%</strong></span>
      </div>
    </div>

    <!-- Machine Learning Influence -->
    <div class="exp-ml-card">
      <div class="exp-panel-title">🤖 Machine Learning Signals &amp; Influence</div>
      <div class="exp-ml-grid">
        <div class="exp-ml-item">
          <span class="exp-ml-label">K-Means Cluster</span>
          <span class="exp-ml-val">${escHtml(ml.cluster_name || 'General Engineering')}</span>
          <span class="exp-ml-sub">${pct(ml.cluster_similarity_percentage)}% Centroid Proximity</span>
        </div>
        <div class="exp-ml-item">
          <span class="exp-ml-label">Ensemble Model</span>
          <span class="exp-ml-val">${pct(ml.ensemble_confidence_percentage)}% Affinity</span>
          <span class="exp-ml-sub">RF &amp; GB (${escHtml(ml.ensemble_model_agreement)})</span>
        </div>
        <div class="exp-ml-item">
          <span class="exp-ml-label">Skill Gate Protection</span>
          <span class="exp-ml-val">${ml.skill_gate_factor === 1.0 ? 'Active (1.0x)' : 'Clamped (' + ml.skill_gate_factor + 'x)'}</span>
          <span class="exp-ml-sub">${escHtml(ml.skill_gate_explanation || '')}</span>
        </div>
      </div>
    </div>

    <!-- Learning & Roadmap Sequencing Rationale -->
    <div class="exp-learning-card">
      <div class="exp-panel-title">🧭 Learning &amp; Sequencing Rationale</div>
      <div class="exp-rationale-item">
        <strong>Course Selection:</strong> ${escHtml(lr.course_recommendation_reason || '')}
      </div>
      <div class="exp-rationale-item" style="margin-top:8px;">
        <strong>Roadmap Order:</strong> ${escHtml(lr.roadmap_sequencing_reason || '')}
      </div>
    </div>
  `;
}

/* ═══════════════════════════════════════════
   RENDER: COURSE & CERTIFICATION RECOMMENDATIONS
═══════════════════════════════════════════ */
function renderCourseRecommendations(entry) {
  if (!recommendedCoursesBody) return;
  if (!entry || !entry.course_recommendations) {
    recommendedCoursesBody.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">Select a career to view matching courses.</p>';
    return;
  }

  const recs = entry.course_recommendations;
  const essentials = recs.essential_courses || [];
  const certs = recs.recommended_certifications || [];
  const summary = recs.summary || '';

  if (!essentials.length && !certs.length) {
    recommendedCoursesBody.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">🎉</span>
        <p>No missing skills for this career! Your profile covers all requirements.</p>
      </div>`;
    return;
  }

  const renderCourseItem = (c) => `
    <div class="course-rec-card">
      <div class="course-card-top-row">
        <div class="course-card-info">
          <div class="course-card-title">${escHtml(c.course_name)}</div>
          <div class="course-card-meta">
            <span class="course-provider-tag">${escHtml(c.provider)}</span>
            <span class="course-badge-pill diff-${(c.difficulty || 'beginner').toLowerCase()}">${escHtml(c.difficulty)}</span>
            <span class="course-duration-pill">⏱ ${escHtml(c.duration)}</span>
            ${c.certification_available ? '<span class="course-cert-badge">🏆 Certificate</span>' : ''}
          </div>
        </div>
        ${c.url ? `
        <a href="${escHtml(c.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-course-link">
          View Course ↗
        </a>` : ''}
      </div>
      <div class="course-skills-covered">
        <span class="course-skills-label">${(c.matched_gaps && c.matched_gaps.length) ? 'Covers Gaps:' : 'Skills Covered:'}</span>
        ${((c.matched_gaps && c.matched_gaps.length) ? c.matched_gaps : (c.skills_covered || [])).map(s => `<span class="result-skill-tag tag-cyan">${escHtml(s)}</span>`).join('')}
      </div>
    </div>
  `;

  recommendedCoursesBody.innerHTML = `
    <div class="course-recs-summary">
      <span class="rec-exp-icon">💡</span>
      <span>${escHtml(summary)}</span>
    </div>

    ${certs.length ? `
    <div class="course-section-group">
      <div class="course-section-heading">🏆 Recommended Industry Certifications</div>
      <div class="courses-list">${certs.map(renderCourseItem).join('')}</div>
    </div>` : ''}

    <div class="course-section-group">
      <div class="course-section-heading">${recs.has_missing_skills === false ? '📚 Recommended Advanced Courses' : '📚 Priority Courses for Missing Skills'}</div>
      <div class="courses-list">${essentials.map(renderCourseItem).join('')}</div>
    </div>
  `;
}

/* ═══════════════════════════════════════════
   RENDER: SKILL ANALYSIS PANEL
═══════════════════════════════════════════ */
function renderSkillAnalysis(entry) {
  if (!entry) {
    careerAnalysisBody.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">Select a career to see skill analysis.</p>';
    return;
  }

  const readiness = pct(entry.readiness_score);
  const gap       = pct(entry.skill_gap_percentage);

  const matchedTags = (entry.matched_skills || []).map(s => skillTag(s, 'tag-green')).join('') ||
    '<span style="color:var(--text-muted);font-size:0.8rem;">None matched</span>';

  const missingBadges = (entry.missing_skills || []).map(s => `
    <span class="missing-skill-badge" data-skill="${escHtml(s)}" title="Click to open learning roadmap">
      ${escHtml(s)} <span class="badge-arrow">→</span>
    </span>
  `).join('') || '<span style="color:var(--text-muted);font-size:0.8rem;">None missing — great job!</span>';

  careerAnalysisBody.innerHTML = `
    <div class="score-bar-section">
      <div class="score-bar-row">
        <span class="score-bar-label">Readiness Score</span>
        <div class="score-bar-track">
          <div class="score-bar-fill fill-readiness" style="width:${readiness}%"></div>
        </div>
        <span class="score-bar-pct" style="color:${scoreColor(readiness)}">${readiness}%</span>
      </div>
      <div class="score-bar-row">
        <span class="score-bar-label">Skill Gap</span>
        <div class="score-bar-track">
          <div class="score-bar-fill fill-gap" style="width:${gap}%"></div>
        </div>
        <span class="score-bar-pct" style="color:${scoreColor(100 - gap)}">${gap}%</span>
      </div>
    </div>
    <div style="margin-bottom:20px;">
      <div class="analysis-col-title col-title-green" style="margin-bottom:10px;">
        ✓ Matched Skills (${(entry.matched_skills || []).length})
      </div>
      <div class="skills-wrap">${matchedTags}</div>
    </div>
    <div>
      <div class="analysis-col-title col-title-pink" style="margin-bottom:10px;">
        ✗ Missing Skills (${(entry.missing_skills || []).length}) — click any to open roadmap
      </div>
      <div class="skills-wrap">${missingBadges}</div>
    </div>
  `;
  /* Wire missing-skill badge clicks via delegation — after innerHTML is set */
  careerAnalysisBody.querySelectorAll('.missing-skill-badge').forEach(badge => {
    badge.addEventListener('click', () => openSkillRoadmap(badge.dataset.skill));
  });
}

/* ═══════════════════════════════════════════
   RENDER: WHAT TO LEARN PANEL
═══════════════════════════════════════════ */
function renderWhatToLearn(entry, careerName) {
  if (!entry || !(entry.what_to_learn || []).length) {
    whatToLearnBody.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">Nothing to learn — you already have all required skills!</p>';
    return;
  }

  whatToLearnBody.innerHTML = entry.what_to_learn.map(w => `
    <div class="wtl-item" data-skill="${escHtml(w.skill)}">
      <div class="wtl-skill">${escHtml(w.skill)}</div>
      <div class="wtl-rec">${escHtml(w.recommendation)}</div>
      <button class="btn-start-learning" data-skill="${escHtml(w.skill)}">
        🗺️ Start Learning
      </button>
    </div>
  `).join('');
  /* Wire start-learning buttons via delegation */
  whatToLearnBody.querySelectorAll('.btn-start-learning').forEach(btn => {
    btn.addEventListener('click', () => openSkillRoadmap(btn.dataset.skill));
  });
}

/* ═══════════════════════════════════════════
   RENDER: CAREER PROGRESSION ROADMAP (6 Stages)
═══════════════════════════════════════════ */
function renderCareerRoadmap(entry) {
  if (!careerRoadmapStagesBody) return;
  if (roadmapCareerBadge) roadmapCareerBadge.textContent = activeCareerName || 'Selected Career';

  if (!entry || !entry.career_roadmap) {
    careerRoadmapStagesBody.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">Select a career to view its learning roadmap.</p>';
    return;
  }

  const rm = entry.career_roadmap;
  const stages = rm.stages || [];
  const progress = loadProgress();

  /* Calculate dynamic progress based on localStorage */
  const missing = entry.missing_skills || [];
  const completedSkills = missing.filter(s => progress[progressKey(activeCareerName, s)] === 'completed');
  const completedSet = new Set(completedSkills.map(s => s.toLowerCase()));

  if (roadmapProgressSummary) {
    roadmapProgressSummary.textContent = `${completedSkills.length} of ${missing.length} missing skills completed (${missing.length ? Math.round(completedSkills.length / missing.length * 100) : 100}%)`;
  }

  careerRoadmapStagesBody.innerHTML = stages.map(stage => {
    const stageSkills = stage.skills || [];
    const allStageSkillsCompleted = stageSkills.length > 0 && stageSkills.every(s => completedSet.has(s.skill.toLowerCase()));
    const hasAnyInProg = stageSkills.some(s => progress[progressKey(activeCareerName, s.skill)] === 'in-progress');

    let stageStatusClass = 'status-pending';
    let stageStatusLabel = '🔒 Pending';

    if (stageSkills.length === 0) {
      stageStatusClass = 'status-unlocked';
      stageStatusLabel = '✨ Milestone';
    } else if (allStageSkillsCompleted) {
      stageStatusClass = 'status-completed';
      stageStatusLabel = '✓ Completed';
    } else if (hasAnyInProg || stage.stage_number === 1 || completedSkills.length > 0) {
      stageStatusClass = 'status-inprogress';
      stageStatusLabel = '▶ In Progress';
    }

    const skillsHtml = stageSkills.map(s => {
      const isDone = completedSet.has(s.skill.toLowerCase());
      const inProg = progress[progressKey(activeCareerName, s.skill)] === 'in-progress';
      const statusIcon = isDone ? '✓ ' : inProg ? '⏳ ' : '';
      const unmet = s.unmet_prerequisites && s.unmet_prerequisites.length
        ? `<small class="unmet-prereq">Needs: ${escHtml(s.unmet_prerequisites.join(', '))}</small>`
        : '';

      return `
        <span class="roadmap-stage-skill-pill ${isDone ? 'done' : ''} ${s.is_required ? 'required' : 'preferred'}"
              data-skill="${escHtml(s.skill)}"
              title="${escHtml(s.why_prioritized)} — ${escHtml(s.enables_next)}">
          ${statusIcon}${escHtml(s.skill)}
          ${s.is_required ? '<span class="pill-req-dot" title="Required Skill">•</span>' : ''}
          ${unmet}
        </span>
      `;
    }).join('');

    const actionsHtml = (stage.action_items || []).map(a => `<li>${escHtml(a)}</li>`).join('');

    return `
      <div class="career-stage-card ${stageStatusClass}">
        <div class="career-stage-header">
          <div class="career-stage-num">${stage.stage_number}</div>
          <div class="career-stage-title-wrap">
            <div class="career-stage-title">${escHtml(stage.title)}</div>
            <div class="career-stage-theme">${escHtml(stage.theme)} • <span class="stage-duration">${escHtml(stage.estimated_duration)}</span></div>
          </div>
          <div class="career-stage-badge ${stageStatusClass}">${stageStatusLabel}</div>
        </div>

        <div class="career-stage-desc">${escHtml(stage.description)}</div>

        ${stageSkills.length ? `
        <div class="career-stage-skills-section">
          <div class="stage-section-label">Assigned Skill Targets:</div>
          <div class="stage-skills-wrap">${skillsHtml}</div>
        </div>` : ''}

        ${actionsHtml ? `
        <div class="career-stage-actions">
          <ul class="stage-action-list">${actionsHtml}</ul>
        </div>` : ''}
      </div>
    `;
  }).join('');

  /* Wire skill pill clicks to open individual skill roadmap */
  careerRoadmapStagesBody.querySelectorAll('.roadmap-stage-skill-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.stopPropagation();
      openSkillRoadmap(pill.dataset.skill);
    });
  });
}

/* ═══════════════════════════════════════════
   RENDER: ROADMAP SKILL LIST (sidebar)
═══════════════════════════════════════════ */
function renderRoadmapSkillList(entry) {
  if (!roadmapSkillList) return;
  const missing = (entry && entry.missing_skills) ? entry.missing_skills : [];

  if (!missing.length) {
    roadmapSkillList.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;padding:8px 0;">No missing skills for this career.</p>';
    return;
  }

  const progress = loadProgress();
  roadmapSkillList.innerHTML = missing.map(skill => {
    const key = progressKey(activeCareerName, skill);
    const status = progress[key] || 'not-started';
    const progClass = status !== 'not-started' ? 'prog-' + status : '';
    return `
      <button class="roadmap-skill-btn ${progClass} ${activeSkillName === skill ? 'active' : ''}"
              data-skill="${escHtml(skill)}">
        ${escHtml(skill)}
        <span class="skill-progress-dot"></span>
      </button>
    `;
  }).join('');
  /* Wire roadmap skill buttons via delegation */
  roadmapSkillList.querySelectorAll('.roadmap-skill-btn').forEach(btn => {
    btn.addEventListener('click', () => openSkillRoadmap(btn.dataset.skill));
  });
}

/* ═══════════════════════════════════════════
   OPEN SKILL ROADMAP
═══════════════════════════════════════════ */
function openSkillRoadmap(skillName) {
  activeSkillName = skillName;

  /* Navigate to roadmap section */
  showSection('section-roadmap');

  /* Highlight active button in roadmap skill list — exact match via data-skill */
  document.querySelectorAll('.roadmap-skill-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.skill === skillName);
  });

  /* Highlight active missing-skill badge — exact match via data-skill */
  document.querySelectorAll('.missing-skill-badge').forEach(b => {
    b.classList.toggle('active', b.dataset.skill === skillName);
  });

  /* Highlight active wtl item — exact match via data-skill */
  document.querySelectorAll('.wtl-item').forEach(el => {
    el.classList.toggle('active', el.dataset.skill === skillName);
  });

  /* Find recommendation from what_to_learn */
  const analysis = (apiData && apiData.career_analysis) ? apiData.career_analysis : [];
  const entry = analysis.find(a => a.career === activeCareerName) || null;
  const wtlEntry = entry ? (entry.what_to_learn || []).find(w => w.skill === skillName) : null;
  const recommendation = wtlEntry ? wtlEntry.recommendation : `Develop or learn ${skillName}`;

  /* Show roadmap content */
  roadmapPlaceholder.hidden = true;
  roadmapContent.hidden = false;

  roadmapSkillName.textContent = skillName;
  roadmapSkillWhy.textContent = `This skill is required for ${activeCareerName || 'your target career'} and is currently missing from your resume.`;
  roadmapRecText.textContent = recommendation;

  /* Render 5 stages */
  roadmapStages.innerHTML = buildStages(skillName).map((stage, i) => `
    <div class="roadmap-stage">
      <div class="stage-num">${i + 1}</div>
      <div class="stage-body">
        <div class="stage-title">${escHtml(stage.title)}</div>
        <div class="stage-desc">${escHtml(stage.desc)}</div>
      </div>
    </div>
  `).join('');

  /* Render learning strategy */
  learningStrategyBody.innerHTML = buildStrategy(skillName).map(item => `
    <div class="strategy-item">
      <div class="strategy-item-title">${escHtml(item.title)}</div>
      <div class="strategy-item-text">${escHtml(item.text)}</div>
    </div>
  `).join('');
  if (learningStrategyBody.children.length) {
    learningStrategyBody.innerHTML = `<div class="strategy-grid">${learningStrategyBody.innerHTML}</div>`;
  }

  /* Render YouTube buttons */
  const q = encodeURIComponent(skillName);
  ytButtons.innerHTML = `
    <a class="btn-yt btn-yt-beginner" href="https://www.youtube.com/results?search_query=${q}+tutorial+for+beginners" target="_blank" rel="noopener">
      ▶ Beginner Tutorial
    </a>
    <a class="btn-yt btn-yt-project" href="https://www.youtube.com/results?search_query=${q}+practical+project+tutorial" target="_blank" rel="noopener">
      🛠 Practical Project
    </a>
    <a class="btn-yt btn-yt-advanced" href="https://www.youtube.com/results?search_query=${q}+advanced+concepts" target="_blank" rel="noopener">
      🚀 Advanced Concepts
    </a>
  `;
}

/* ═══════════════════════════════════════════
   LEARNING STAGES GENERATOR
═══════════════════════════════════════════ */
function buildStages(skill) {
  return [
    {
      title: 'Stage 1: Understand Fundamentals',
      desc: `Learn what ${skill} is, why it exists, and the core concepts behind it. Read official documentation or a beginner guide.`
    },
    {
      title: 'Stage 2: Practice Core Concepts',
      desc: `Work through exercises and small examples that reinforce the key ideas of ${skill}. Use interactive platforms or coding challenges.`
    },
    {
      title: 'Stage 3: Build a Mini Project',
      desc: `Create a small self-contained project using ${skill}. This solidifies your understanding and gives you something to show.`
    },
    {
      title: 'Stage 4: Apply in a Real Project',
      desc: `Integrate ${skill} into a larger, real-world project. Combine it with other skills you already have to solve a genuine problem.`
    },
    {
      title: 'Stage 5: Add to Resume',
      desc: `Document your ${skill} experience with specific examples, project names, and measurable outcomes. Add it to your skills section.`
    }
  ];
}

/* ═══════════════════════════════════════════
   LEARNING STRATEGY GENERATOR
═══════════════════════════════════════════ */
function buildStrategy(skill) {
  return [
    {
      title: 'Where to Start',
      text: `Begin with the official documentation or a highly-rated beginner course for ${skill}. Focus on understanding the "why" before the "how".`
    },
    {
      title: 'Core Concepts to Master',
      text: `Identify the 3–5 foundational concepts of ${skill} that appear in most job descriptions. Master those before moving to advanced topics.`
    },
    {
      title: 'Practice Strategy',
      text: `Dedicate 30–60 minutes daily to hands-on practice with ${skill}. Consistency beats intensity — short daily sessions build stronger retention.`
    },
    {
      title: 'Mini-Project Idea',
      text: `Build a small project that uses ${skill} as its primary technology. Keep scope tight so you finish it within a week and can showcase it.`
    },
    {
      title: 'Common Mistakes to Avoid',
      text: `Avoid tutorial hell — don't just watch videos. After each concept, immediately write code. Also avoid skipping fundamentals to jump to advanced topics.`
    }
  ];
}

/* ═══════════════════════════════════════════
   PROGRESS TRACKER
═══════════════════════════════════════════ */
function progressKey(career, skill) {
  return `${career}||${skill}`;
}

function loadProgress() {
  try { return JSON.parse(localStorage.getItem(LS_KEY)) || {}; } catch (_) { return {}; }
}

function saveProgress(data) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(data)); } catch (_) {}
}

function renderProgressTracker() {
  if (!progressTrackerBody) return;

  if (progressCareerBadge) {
    progressCareerBadge.textContent = activeCareerName || 'No career selected';
  }

  const entry = getActiveAnalysisEntry();
  const progress = loadProgress();

  if (!entry) {
    progressTrackerBody.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">📈</span>
        <p>Select a career from Career Matches to start tracking your progress</p>
      </div>`;
    if (progressSummary) progressSummary.textContent = '0 of 0 skills completed';
    return;
  }

  const missing = entry.missing_skills || [];

  if (!missing.length) {
    progressTrackerBody.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">🎉</span>
        <p><strong>No missing skills for ${escHtml(entry.career)}!</strong><br><span style="color:var(--text-muted);font-size:0.83rem;margin-top:6px;display:inline-block;">Your profile satisfies all core skill requirements for this selected career.</span></p>
      </div>`;
    if (progressSummary) progressSummary.textContent = 'All skills matched (100%)';
    return;
  }

  const rows = missing.map(skill => ({ career: entry.career, skill }));

  progressTrackerBody.innerHTML = rows.map(({ career, skill }) => {
    const key    = progressKey(career, skill);
    const status = progress[key] || 'not-started';
    return `
      <div class="progress-item">
        <span class="progress-skill-name">${escHtml(skill)}</span>
        <span class="progress-career-label">${escHtml(career)}</span>
        <select class="progress-select status-${status}"
                data-key="${escHtml(key)}"
                onchange="updateSkillProgress(this)">
          <option value="not-started" ${status === 'not-started' ? 'selected' : ''}>Not Started</option>
          <option value="learning"    ${status === 'learning'    ? 'selected' : ''}>Learning</option>
          <option value="practicing"  ${status === 'practicing'  ? 'selected' : ''}>Practicing</option>
          <option value="completed"   ${status === 'completed'   ? 'selected' : ''}>Completed</option>
        </select>
      </div>
    `;
  }).join('');

  updateProgressSummary(progress, rows);
}

function updateSkillProgress(selectEl) {
  const key    = selectEl.dataset.key;
  const status = selectEl.value;
  const data   = loadProgress();
  data[key]    = status;
  saveProgress(data);

  selectEl.className = `progress-select status-${status}`;

  const entry = getActiveAnalysisEntry();
  renderRoadmapSkillList(entry);
  renderCareerRoadmap(entry);

  const missing = (entry && entry.missing_skills) ? entry.missing_skills : [];
  const rows = missing.map(skill => ({ career: entry.career, skill }));
  updateProgressSummary(data, rows);
}

function updateProgressSummary(progress, rows) {
  if (!progressSummary) return;
  const entry = getActiveAnalysisEntry();
  if (!rows || !rows.length) {
    if (entry && (!entry.missing_skills || !entry.missing_skills.length)) {
      progressSummary.textContent = 'All skills matched (100%)';
    } else {
      progressSummary.textContent = '0 of 0 skills completed';
    }
    return;
  }
  const completed = rows.filter(({ career, skill }) => progress[progressKey(career, skill)] === 'completed').length;
  const pctValue = Math.round((completed / rows.length) * 100);
  progressSummary.textContent = `${completed} of ${rows.length} missing skills completed (${pctValue}%)`;
}

function getActiveAnalysisEntry() {
  if (!apiData || !activeCareerName) return null;
  return (apiData.career_analysis || []).find(a => a.career === activeCareerName) || null;
}

/* ═══════════════════════════════════════════
   CAREER COMPARISON STATE & LOGIC
═══════════════════════════════════════════ */
let compareCareerA = null;
let compareCareerB = null;

function populateCompareDropdowns() {
  if (!compareSelectA || !compareSelectB) return;
  const recs = (apiData && apiData.career_recommendations) ? apiData.career_recommendations : [];

  const createOptions = (selectedVal, disabledVal) => {
    let opts = '<option value="">-- Select Career --</option>';
    recs.forEach((r, idx) => {
      const isSelected = r.career === selectedVal;
      const isDisabled = r.career === disabledVal;
      opts += `<option value="${escHtml(r.career)}" ${isSelected ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}>#${idx + 1} ${escHtml(r.career)} (${pct(r.final_score)}%)</option>`;
    });
    return opts;
  };

  compareSelectA.innerHTML = createOptions(compareCareerA, compareCareerB);
  compareSelectB.innerHTML = createOptions(compareCareerB, compareCareerA);
}

function onCompareSelectChange(slot, value) {
  if (slot === 'A') {
    if (value && value === compareCareerB) {
      compareCareerB = null;
    }
    compareCareerA = value || null;
  } else if (slot === 'B') {
    if (value && value === compareCareerA) {
      compareCareerA = null;
    }
    compareCareerB = value || null;
  }
  populateCompareDropdowns();
  renderCareerComparison();
}

function quickCompareCareer(careerName) {
  const recs = (apiData && apiData.career_recommendations) ? apiData.career_recommendations : [];
  if (!recs.length) return;

  if (!compareCareerA || compareCareerA === careerName) {
    compareCareerA = careerName;
    if (!compareCareerB || compareCareerB === careerName) {
      const other = recs.find(r => r.career !== careerName);
      compareCareerB = other ? other.career : null;
    }
  } else {
    compareCareerB = careerName;
  }

  populateCompareDropdowns();
  renderCareerComparison();
  showSection('section-compare');
}

function resetCareerComparison() {
  const recs = (apiData && apiData.career_recommendations) ? apiData.career_recommendations : [];
  if (recs.length >= 2) {
    compareCareerA = recs[0].career;
    compareCareerB = recs[1].career;
  } else if (recs.length === 1) {
    compareCareerA = recs[0].career;
    compareCareerB = null;
  } else {
    compareCareerA = null;
    compareCareerB = null;
  }
  populateCompareDropdowns();
  renderCareerComparison();
}

function swapCareerComparison() {
  const temp = compareCareerA;
  compareCareerA = compareCareerB;
  compareCareerB = temp;
  populateCompareDropdowns();
  renderCareerComparison();
}

if (compareSelectA) {
  compareSelectA.addEventListener('change', e => onCompareSelectChange('A', e.target.value));
}
if (compareSelectB) {
  compareSelectB.addEventListener('change', e => onCompareSelectChange('B', e.target.value));
}
if (swapCompareBtn) {
  swapCompareBtn.addEventListener('click', swapCareerComparison);
}
if (resetCompareBtn) {
  resetCompareBtn.addEventListener('click', resetCareerComparison);
}

function generateComparisonInsights(itemA, itemB) {
  if (!itemA || !itemB) return [];

  const insights = [];
  const scoreA = Number(itemA.final_score) || 0;
  const scoreB = Number(itemB.final_score) || 0;
  const scoreDiff = Math.round((scoreA - scoreB) * 10) / 10;
  const absScoreDiff = Math.abs(scoreDiff);

  // 1. Overall Score insight
  if (absScoreDiff <= 1.0) {
    insights.push(`<strong>Overall Suitability:</strong> Both careers demonstrate very close suitability for your profile (within 1% score margin).`);
  } else if (scoreDiff > 0) {
    insights.push(`<strong>Overall Match:</strong> <em>${escHtml(itemA.career)}</em> leads with a higher overall hybrid recommendation score (${scoreA}% vs ${scoreB}%).`);
  } else {
    insights.push(`<strong>Overall Match:</strong> <em>${escHtml(itemB.career)}</em> leads with a higher overall hybrid recommendation score (${scoreB}% vs ${scoreA}%).`);
  }

  // 2. Skill Gap insight
  const gapsA = itemA.missing_skills ? itemA.missing_skills.length : 0;
  const gapsB = itemB.missing_skills ? itemB.missing_skills.length : 0;

  if (gapsA === 0 && gapsB === 0) {
    insights.push(`<strong>Skill Readiness:</strong> Your resume profile currently satisfies all core skill requirements for both roles.`);
  } else if (gapsA < gapsB) {
    insights.push(`<strong>Skill Readiness:</strong> <em>${escHtml(itemA.career)}</em> requires fewer additional skills (${gapsA} missing vs ${gapsB} for <em>${escHtml(itemB.career)}</em>).`);
  } else if (gapsB < gapsA) {
    insights.push(`<strong>Skill Readiness:</strong> <em>${escHtml(itemB.career)}</em> requires fewer additional skills (${gapsB} missing vs ${gapsA} for <em>${escHtml(itemA.career)}</em>).`);
  } else {
    insights.push(`<strong>Skill Readiness:</strong> Both careers require learning ${gapsA} additional skills to satisfy all core criteria.`);
  }

  // 3. Cluster Relevance insight
  const clustA = Number(itemA.cluster_relevance) || 0;
  const clustB = Number(itemB.cluster_relevance) || 0;
  if (clustA >= clustB + 3.0) {
    insights.push(`<strong>Cluster Alignment:</strong> Your profile has stronger clustering relevance to <em>${escHtml(itemA.career)}</em> (${clustA}% vs ${clustB}%).`);
  } else if (clustB >= clustA + 3.0) {
    insights.push(`<strong>Cluster Alignment:</strong> Your profile has stronger clustering relevance to <em>${escHtml(itemB.career)}</em> (${clustB}% vs ${clustA}%).`);
  }

  // 4. Ensemble ML Model Support
  const ensA = Number(itemA.ensemble_confidence) || 0;
  const ensB = Number(itemB.ensemble_confidence) || 0;
  if (ensA >= ensB + 3.0) {
    insights.push(`<strong>Ensemble Support:</strong> Machine learning ensemble models indicate stronger affinity toward <em>${escHtml(itemA.career)}</em> (${ensA}% vs ${ensB}%).`);
  } else if (ensB >= ensA + 3.0) {
    insights.push(`<strong>Ensemble Support:</strong> Machine learning ensemble models indicate stronger affinity toward <em>${escHtml(itemB.career)}</em> (${ensB}% vs ${ensA}%).`);
  }

  return insights;
}

function renderCareerComparison() {
  if (!careerComparisonBody) return;
  const recs = (apiData && apiData.career_recommendations) ? apiData.career_recommendations : [];

  if (!recs || recs.length < 2) {
    careerComparisonBody.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">⚖️</span>
        <p>At least 2 career recommendations are required to perform a side-by-side comparison.</p>
      </div>`;
    return;
  }

  if (!compareCareerA || !compareCareerB) {
    careerComparisonBody.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">⚖️</span>
        <p>Please select two careers from the dropdowns above to view their side-by-side comparison.</p>
      </div>`;
    return;
  }

  if (compareCareerA === compareCareerB) {
    careerComparisonBody.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">⚠️</span>
        <p>Please select two different careers to compare.</p>
      </div>`;
    return;
  }

  const rankA = recs.findIndex(r => r.career === compareCareerA) + 1;
  const rankB = recs.findIndex(r => r.career === compareCareerB) + 1;
  const itemA = recs.find(r => r.career === compareCareerA);
  const itemB = recs.find(r => r.career === compareCareerB);

  if (!itemA || !itemB) {
    careerComparisonBody.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">⚠️</span>
        <p>Selected comparison careers could not be found in recommendations.</p>
      </div>`;
    return;
  }

  const scoreA = pct(itemA.final_score !== undefined ? itemA.final_score : itemA.final_recommendation_score);
  const scoreB = pct(itemB.final_score !== undefined ? itemB.final_score : itemB.final_recommendation_score);
  const compatA = pct(itemA.compatibility_score);
  const compatB = pct(itemB.compatibility_score);
  const clustA = pct(itemA.cluster_relevance_score || itemA.cluster_relevance || 0);
  const clustB = pct(itemB.cluster_relevance_score || itemB.cluster_relevance || 0);
  const ensA = pct(itemA.ensemble_confidence || itemA.ensemble_prediction_score || 0);
  const ensB = pct(itemB.ensemble_confidence || itemB.ensemble_prediction_score || 0);

  const matchedA = (itemA.matched_skills || []).length;
  const matchedB = (itemB.matched_skills || []).length;
  const missingA = (itemA.missing_skills || []);
  const missingB = (itemB.missing_skills || []);

  const insights = generateComparisonInsights({
    ...itemA,
    final_score: scoreA,
    compatibility_score: compatA,
    cluster_relevance: clustA,
    ensemble_confidence: ensA
  }, {
    ...itemB,
    final_score: scoreB,
    compatibility_score: compatB,
    cluster_relevance: clustB,
    ensemble_confidence: ensB
  });

  const renderTags = (list, tagClass) => {
    if (!list || !list.length) {
      return '<span class="compare-tag tag-green">🎉 0 missing gaps</span>';
    }
    return list.map(s => `<span class="compare-tag ${tagClass}">${escHtml(s)}</span>`).join('');
  };

  const getWinnerClass = (valA, valB, lowerIsBetter = false) => {
    if (valA === valB) return { classA: '', classB: '' };
    if (lowerIsBetter) {
      return valA < valB ? { classA: 'winner-cell', classB: '' } : { classA: '', classB: 'winner-cell' };
    }
    return valA > valB ? { classA: 'winner-cell', classB: '' } : { classA: '', classB: 'winner-cell' };
  };

  const winScore = getWinnerClass(scoreA, scoreB);
  const winCompat = getWinnerClass(compatA, compatB);
  const winClust = getWinnerClass(clustA, clustB);
  const winEns = getWinnerClass(ensA, ensB);
  const winMatched = getWinnerClass(matchedA, matchedB);
  const winMissing = getWinnerClass(missingA.length, missingB.length, true);

  careerComparisonBody.innerHTML = `
    <!-- Comparison Insights Banner -->
    <div class="compare-insights-banner">
      <div class="compare-insights-header">
        <span class="compare-insights-icon">💡</span>
        <h4 class="compare-insights-title">Deterministic Comparison Summary</h4>
      </div>
      <ul class="compare-insights-list">
        ${insights.map(ins => `<li>${ins}</li>`).join('')}
      </ul>
    </div>

    <!-- Side-by-Side Comparison Table -->
    <div class="compare-table-wrap">
      <table class="compare-table">
        <thead>
          <tr>
            <th class="col-metric">Metric / Attribute</th>
            <th class="col-career">
              <div class="career-col-header">
                <span class="compare-rank-pill">#${rankA}</span>
                <span class="compare-career-title">${escHtml(itemA.career)}</span>
                <button class="btn btn-outline btn-xs" onclick="selectCareer('${escHtml(itemA.career)}'); showSection('section-skills')" style="margin-top:6px;">Select for Roadmap</button>
              </div>
            </th>
            <th class="col-career">
              <div class="career-col-header">
                <span class="compare-rank-pill">#${rankB}</span>
                <span class="compare-career-title">${escHtml(itemB.career)}</span>
                <button class="btn btn-outline btn-xs" onclick="selectCareer('${escHtml(itemB.career)}'); showSection('section-skills')" style="margin-top:6px;">Select for Roadmap</button>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="metric-name">⭐ Final Hybrid Score</td>
            <td class="metric-val ${winScore.classA}"><strong>${scoreA}%</strong></td>
            <td class="metric-val ${winScore.classB}"><strong>${scoreB}%</strong></td>
          </tr>
          <tr>
            <td class="metric-name">🎯 Skill Compatibility</td>
            <td class="metric-val ${winCompat.classA}"><strong>${compatA}%</strong></td>
            <td class="metric-val ${winCompat.classB}"><strong>${compatB}%</strong></td>
          </tr>
          <tr>
            <td class="metric-name">🔬 Cluster Relevance</td>
            <td class="metric-val ${winClust.classA}">${clustA}%</td>
            <td class="metric-val ${winClust.classB}">${clustB}%</td>
          </tr>
          <tr>
            <td class="metric-name">🤖 Ensemble Support</td>
            <td class="metric-val ${winEns.classA}">${ensA}%</td>
            <td class="metric-val ${winEns.classB}">${ensB}%</td>
          </tr>
          <tr>
            <td class="metric-name">✅ Matched Skills Count</td>
            <td class="metric-val ${winMatched.classA}">${matchedA} skills</td>
            <td class="metric-val ${winMatched.classB}">${matchedB} skills</td>
          </tr>
          <tr>
            <td class="metric-name">⚠️ Missing Skills Count</td>
            <td class="metric-val ${winMissing.classA}">${missingA.length} missing</td>
            <td class="metric-val ${winMissing.classB}">${missingB.length} missing</td>
          </tr>
          <tr>
            <td class="metric-name">📋 Missing Skill Details</td>
            <td class="metric-tags">${renderTags(missingA, 'tag-pink')}</td>
            <td class="metric-tags">${renderTags(missingB, 'tag-pink')}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `;
}

/* ═══════════════════════════════════════════
   MASTER RENDER
═══════════════════════════════════════════ */
function renderResults(data) {
  renderResumeSummary(data.resume || {});
  renderExtractedSkills(data.skills || {});
  renderCareerRecs(data.career_recommendations || []);
  renderClusterAnalysis(data);
  renderEnsembleAnalysis(data);
  renderProgressTracker();
  resetCareerComparison();
  /* Auto-select first career AFTER sections are visible */
  const recs = data.career_recommendations || [];
  if (recs.length) {
    showResults();
    selectCareer(recs[0].career);
  } else {
    showResults();
  }
}

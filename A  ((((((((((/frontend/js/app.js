// TruthCheck AI - Frontend Application (app.js)
// Deployed on Vercel (static). Communicates with Flask backend on Render.
// IMPORTANT: Change API_BASE_URL to your actual Render backend URL after deploying.

const API_BASE_URL = window.TRUTHCHECK_API_URL || 'https://truthcheck-ai-backend.onrender.com';
let currentPage = 'home';
let _cameraStream = null;

// ── ROUTING
function navigate(page, data) {
  currentPage = page; updateNav(page); stopCamera();
  const content = document.getElementById('page-content');
  const footer = document.getElementById('app-footer');
  const appPage = document.getElementById('app-page');
  if (page === 'home') { appPage.className = 'page'; if(footer) footer.style.display = ''; }
  else { appPage.className = 'page scrollable'; if(footer) footer.style.display = 'none'; }
  if (!content) return;
  if (page === 'home') content.innerHTML = renderHome();
  else if (page === 'text-check') content.innerHTML = renderTextCheck();
  else if (page === 'image-scanner') { content.innerHTML = renderImageScanner(); initCamera(); }
  else if (page === 'history') { content.innerHTML = renderHistoryLoading(); loadHistory(data); }
  else if (page === 'about') { content.innerHTML = renderAboutLoading(); loadAbout(); }
  else if (page === 'result') content.innerHTML = renderResult(data);
  else content.innerHTML = renderHome();
  bindPageEvents(page);
  if (page === 'home') setTimeout(initStatsCountUp, 100);
}

function updateNav(page) {
  const map = { 'home':'home','text-check':'text-check','image-scanner':'image-scanner','history':'history','about':'about' };
  const activeId = map[page] || null;
  ['home','text-check','image-scanner','history','about'].forEach(id => {
    const el = document.getElementById('nav-' + id);
    const mob = document.getElementById('mobile-nav-' + id);
    if(el) el.classList.toggle('active', id === activeId);
    if(mob) mob.classList.toggle('active', id === activeId);
  });
}

function showFlash(message, type='error') {
  const container = document.getElementById('flash-container');
  if (!container) return;
  const iconMap = { error:'fa-circle-exclamation', warning:'fa-triangle-exclamation', success:'fa-circle-check' };
  container.innerHTML = '';
  const div = document.createElement('div');
  div.className = 'flash-alert ' + type;
  div.innerHTML = '<i class="fa-solid ' + (iconMap[type]||iconMap.error) + '"></i><span>' + escHtml(message) + '</span>';
  container.appendChild(div);
  setTimeout(() => { if(div.parentNode) div.parentNode.removeChild(div); }, 6000);
}
function clearFlash() { const c = document.getElementById('flash-container'); if(c) c.innerHTML = ''; }
function closeMobileMenu() {
  const btn=document.getElementById('burger-btn'), ov=document.getElementById('mobile-overlay'), mn=document.getElementById('mobile-menu');
  if(btn) btn.setAttribute('aria-expanded','false');
  if(ov) ov.setAttribute('hidden',''); if(mn) mn.setAttribute('hidden','');
  document.body.classList.remove('menu-open');
}
function escHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function capitalize(s){ return s ? s.charAt(0).toUpperCase()+s.slice(1) : ''; }
// ── PAGE TEMPLATES
function renderHome() {
  return '<main class="hero"><div class="trust-row anim" style="--d:0.05s"><div class="trust-avatar"><div class="trust-avatar-inner"><i class="fa-solid fa-shield-halved"></i></div></div><div class="trust-avatar"><div class="trust-avatar-inner"><i class="fa-solid fa-brain"></i></div></div><div class="trust-avatar"><div class="trust-avatar-inner"><i class="fa-solid fa-camera-retro"></i></div></div><div class="trust-pill">AI Verification &bull; 96.8% Accuracy</div></div><h1 class="headline"><span class="headline-line" style="--d:0.12s">Detect Fake News</span><span class="headline-line" style="--d:0.28s">With Machine Learning</span></h1><p class="subhead anim" style="--d:0.25s">Check news articles or scan a news photo using advanced OCR and machine learning.</p><div class="hero-actions anim-pulse" style="--d:0.35s"><a href="#" onclick="navigate(\'text-check\'); return false;" class="cta-btn"><i class="fa-solid fa-pen-to-square"></i><span>Check News Text</span></a><a href="#" onclick="navigate(\'image-scanner\'); return false;" class="cta-btn-secondary"><i class="fa-solid fa-camera"></i><span>Scan News Photo</span></a></div><div class="features-grid anim" style="--d:0.45s"><a href="#" onclick="navigate(\'text-check\'); return false;" class="feature-card"><div class="feature-icon-box"><i class="fa-solid fa-robot"></i></div><h3 class="feature-title">AI Analysis</h3><p class="feature-desc">Machine-learning based text classification trained on multi-source datasets with TF-IDF vectorization.</p></a><a href="#" onclick="navigate(\'image-scanner\'); return false;" class="feature-card"><div class="feature-icon-box"><i class="fa-solid fa-image"></i></div><h3 class="feature-title">Image OCR</h3><p class="feature-desc">Extract news text directly from photographs or newspapers using OpenCV and high-precision OCR.</p></a><a href="#" onclick="navigate(\'history\'); return false;" class="feature-card"><div class="feature-icon-box"><i class="fa-solid fa-clock-rotate-left"></i></div><h3 class="feature-title">Scan History</h3><p class="feature-desc">Keep track of previous analyses, search past records, and audit veracity confidence metrics.</p></a></div></main>';
}

function renderTextCheck() {
  return '<div class="main-content-container anim" style="--d:0.1s"><div class="glass-card"><div class="card-header"><h2 class="card-title"><i class="fa-solid fa-file-lines" style="color:#fff;font-size:22px;"></i><span>Check News Text</span></h2><p class="card-subtitle">Enter a news headline, article excerpt, or full statement to analyze its veracity with our machine learning classification engine.</p></div><div class="quick-samples"><span class="sample-tag"><i class="fa-solid fa-wand-magic-sparkles"></i> Try Sample:</span><button type="button" class="sample-btn" onclick="fillSample(\'real\')"><i class="fa-solid fa-circle-check" style="color:var(--real-color);"></i> Real News (NASA)</button><button type="button" class="sample-btn" onclick="fillSample(\'fake\')"><i class="fa-solid fa-circle-exclamation" style="color:var(--fake-color);"></i> Fake News (Miracle Hoax)</button></div><form id="text-check-form"><div class="form-group"><label for="headline" class="form-label">Headline (Optional)</label><input type="text" id="headline" name="headline" class="form-input" placeholder="e.g., Federal Reserve Holds Benchmark Interest Rates..." autocomplete="off" /></div><div class="form-group"><label for="article_text" class="form-label">News Article / Statement Content *</label><textarea id="article_text" name="article_text" class="form-textarea" placeholder="Paste your news article or headline here..." required></textarea></div><button type="submit" class="submit-btn" id="analyze-submit-btn"><i class="fa-solid fa-magnifying-glass"></i><span>Analyze News</span></button></form></div></div>';
}

function renderImageScanner() {
  return '<div class="main-content-container anim" style="--d:0.1s"><div class="glass-card"><div class="card-header"><h2 class="card-title"><i class="fa-solid fa-camera" style="color:#fff;font-size:22px;"></i><span>Scan News Photo</span></h2><p class="card-subtitle">Extract printed or digital news headlines from newspapers, magazines, or screenshots using high-performance OpenCV and OCR.</p></div><div class="scanner-tabs"><button type="button" class="tab-btn active" id="tab-camera-btn"><i class="fa-solid fa-camera"></i><span>Use Camera</span></button><button type="button" class="tab-btn" id="tab-upload-btn"><i class="fa-solid fa-cloud-arrow-up"></i><span>Upload Image</span></button></div><div class="tab-content active" id="camera-tab-content"><div id="camera-error-message" class="flash-alert warning" style="display:none;margin-bottom:16px;"></div><div class="camera-container"><video id="camera-video" autoplay playsinline muted></video><img id="captured-preview" alt="Captured Photo Preview" hidden /><div class="camera-overlay-guide"><span><i class="fa-solid fa-crosshairs"></i> Align news headline within frame</span></div></div><div class="camera-controls"><button type="button" class="cta-btn" id="capture-btn"><i class="fa-solid fa-camera"></i><span>Capture Photo</span></button><button type="button" class="cta-btn-secondary" id="retake-btn" style="display:none;"><i class="fa-solid fa-rotate-left"></i><span>Retake</span></button><button type="button" class="submit-btn" id="analyze-camera-btn" style="flex:1;min-width:200px;" disabled><i class="fa-solid fa-magnifying-glass"></i><span>Analyze Photo</span></button></div><input type="hidden" id="camera-image-data" /></div><div class="tab-content" id="upload-tab-content"><input type="file" id="image-file-input" accept=".jpg,.jpeg,.png,.webp" style="display:none;" /><div class="dropzone" id="dropzone"><div class="dropzone-icon"><i class="fa-solid fa-file-arrow-up"></i></div><p class="dropzone-text">Click or drag &amp; drop news photo here</p><p class="dropzone-subtext">Supports JPG, PNG, WEBP (Max: 5 MB)</p></div><div class="upload-preview-container" id="upload-preview-container"><img id="upload-preview-img" class="upload-preview-img" alt="Uploaded News Preview" /><p id="upload-filename" style="font-size:13px;color:var(--muted);margin:8px 0;"></p><button type="button" class="sample-btn" id="upload-clear-btn" style="margin-bottom:16px;"><i class="fa-solid fa-xmark"></i> Remove &amp; Choose Another</button></div><button type="button" class="submit-btn" id="analyze-upload-btn" disabled><i class="fa-solid fa-magnifying-glass"></i><span>Analyze Image with OCR</span></button></div></div></div>';
}

function renderHistoryLoading() {
  return '<div class="main-content-container anim" style="--d:0.1s"><div class="glass-card"><div class="card-header"><h2 class="card-title"><i class="fa-solid fa-clock-rotate-left" style="color:#fff;font-size:22px;"></i><span>Scan History</span></h2><p class="card-subtitle">Review past news verifications stored in the backend database.</p></div><div style="text-align:center;padding:40px;color:var(--muted);"><i class="fa-solid fa-circle-notch fa-spin" style="font-size:28px;margin-bottom:12px;display:block;"></i><p>Loading history from backend...</p></div></div></div>';
}
function renderAboutLoading() {
  return '<div class="main-content-container anim" style="--d:0.1s"><div class="glass-card"><div class="card-header"><h2 class="card-title"><i class="fa-solid fa-circle-info" style="color:#fff;font-size:22px;"></i><span>About TruthCheck AI</span></h2></div><div style="text-align:center;padding:40px;color:var(--muted);"><i class="fa-solid fa-circle-notch fa-spin" style="font-size:28px;margin-bottom:12px;display:block;"></i><p>Loading system data from backend...</p></div></div></div>';
}
function renderHistoryContent(records, searchQ, predFilter, typeFilter) {
  const q = searchQ || ''; const pred = predFilter || 'ALL'; const type = typeFilter || 'ALL';
  const filters = '<div class="filter-pills">'
    + '<a href="#" onclick="navigate(\'history\',{q:\'' + q + '\',pred:\'ALL\',type:\'' + type + '\'}); return false;" class="filter-btn ' + (pred==='ALL'?'active':'') + '">All</a>'
    + '<a href="#" onclick="navigate(\'history\',{q:\'' + q + '\',pred:\'LIKELY REAL\',type:\'' + type + '\'}); return false;" class="filter-btn ' + (pred==='LIKELY REAL'?'active':'') + '"><i class="fa-solid fa-circle-check" style="color:var(--real-color);font-size:10px;"></i> Real</a>'
    + '<a href="#" onclick="navigate(\'history\',{q:\'' + q + '\',pred:\'LIKELY FAKE\',type:\'' + type + '\'}); return false;" class="filter-btn ' + (pred==='LIKELY FAKE'?'active':'') + '"><i class="fa-solid fa-circle-xmark" style="color:var(--fake-color);font-size:10px;"></i> Fake</a>'
    + '<a href="#" onclick="navigate(\'history\',{q:\'' + q + '\',pred:\'UNCERTAIN\',type:\'' + type + '\'}); return false;" class="filter-btn ' + (pred==='UNCERTAIN'?'active':'') + '"><i class="fa-solid fa-circle-question" style="color:var(--uncertain-color);font-size:10px;"></i> Uncertain</a>'
    + '</div>';
  let listHTML = '';
  if (records && records.length > 0) {
    listHTML = '<div class="history-card-list">' + records.map(function(item) {
      const pl = (item.prediction||'').toLowerCase();
      const bc = pl.includes('real')?'real':pl.includes('fake')?'fake':'uncertain';
      const txt = item.extracted_text || item.original_text || '';
      const icoType = item.input_type==='text'?'fa-file-lines':'fa-camera';
      return '<div class="history-item-card">'
        + '<div class="history-main-info"><div class="history-title">' + escHtml(txt) + '</div>'
        + '<div class="history-submeta"><span><i class="fa-regular fa-calendar" style="margin-right:4px;"></i>' + escHtml(item.created_at||'') + '</span>'
        + '<span><i class="fa-solid ' + icoType + '" style="margin-right:4px;"></i>' + capitalize(item.input_type||'') + '</span>'
        + '<span class="badge-tag ' + bc + '">' + escHtml(item.prediction) + ' (' + item.confidence + '%)</span></div></div>'
        + '<div class="history-actions">'
        + '<a href="#" onclick="loadHistoryDetail(' + item.id + '); return false;" class="action-icon-btn" title="View Full Details"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>'
        + '<a href="#" onclick="deleteHistoryItem(' + item.id + '); return false;" class="action-icon-btn delete" title="Delete Record"><i class="fa-solid fa-trash-can"></i></a>'
        + '</div></div>';
    }).join('') + '</div>';
  } else {
    listHTML = '<div class="empty-state"><i class="fa-solid fa-folder-open"></i><h4 style="font-size:16px;font-weight:600;color:#fff;margin-bottom:6px;">No scan records found</h4><p style="font-size:13.5px;color:var(--muted);margin-bottom:18px;">' + (q||pred!=='ALL'?'No records match your search or filter.':'No scans yet. Check a news article to get started!') + '</p><a href="#" onclick="navigate(\'text-check\'); return false;" class="cta-btn" style="padding:10px 24px;"><i class="fa-solid fa-magnifying-glass"></i><span>Check First Article</span></a></div>';
  }
  return '<div class="main-content-container anim" style="--d:0.1s"><div class="glass-card"><div class="card-header"><h2 class="card-title"><i class="fa-solid fa-clock-rotate-left" style="color:#fff;font-size:22px;"></i><span>Scan History</span></h2><p class="card-subtitle">Review past news verifications stored in the backend database.</p></div><div class="history-toolbar"><div class="search-box" style="display:flex;align-items:center;gap:8px;"><i class="fa-solid fa-magnifying-glass" style="color:var(--muted);"></i><input type="text" id="history-search-input" class="search-input" placeholder="Search by keywords or text..." value="' + escHtml(q) + '" style="padding-left:8px;" /><button type="button" onclick="doHistorySearch()" class="sample-btn" style="white-space:nowrap;">Search</button></div>' + filters + '</div>' + listHTML + '</div></div>';
}
function renderAboutContent(metadata) {
  let cmp = '';
  if (metadata && metadata.all_model_comparison) {
    cmp = '<div class="meta-grid">';
    for (const [name, stats] of Object.entries(metadata.all_model_comparison)) {
      cmp += '<div class="meta-box"><div style="font-weight:600;color:#fff;margin-bottom:8px;font-size:14.5px;">' + escHtml(name) + '</div><div style="font-size:13px;color:var(--muted);line-height:1.5;"><div>Accuracy: <strong style="color:#fff;">' + stats.accuracy + '%</strong></div><div>Precision: <strong style="color:#fff;">' + stats.precision + '%</strong></div><div>Recall: <strong style="color:#fff;">' + stats.recall + '%</strong></div><div>F1-Score: <strong style="color:#fff;">' + stats.f1_score + '%</strong></div></div></div>';
    }
    cmp += '</div>';
  }
  return '<div class="main-content-container anim" style="--d:0.1s"><div class="glass-card"><div class="card-header"><h2 class="card-title"><i class="fa-solid fa-circle-info" style="color:#fff;font-size:22px;"></i><span>About TruthCheck AI</span></h2><p class="card-subtitle">An end-to-end intelligence system engineered to detect sensationalist misinformation and fabricated news across text and photographic media.</p></div><div class="form-group" style="margin-bottom:28px;"><h3 style="font-size:17px;font-weight:600;color:#fff;margin-bottom:10px;">1. Purpose &amp; Core Capabilities</h3><p style="font-size:14px;line-height:1.6;color:#d1d5db;">TruthCheck AI combines NLP, TF-IDF feature weighting, Machine Learning classifiers, and computer vision OCR to evaluate news authenticity in real-time.</p></div><div class="form-group" style="margin-bottom:28px;"><h3 style="font-size:17px;font-weight:600;color:#fff;margin-bottom:10px;">2. System Processing Architecture</h3><div class="diagram-flow"><div class="flow-node"><i class="fa-solid fa-file-pen"></i><br>News Text</div><div class="flow-arrow"><i class="fa-solid fa-arrow-right"></i></div><div class="flow-node"><i class="fa-solid fa-broom"></i><br>Preprocessing</div><div class="flow-arrow"><i class="fa-solid fa-arrow-right"></i></div><div class="flow-node"><i class="fa-solid fa-wave-square"></i><br>TF-IDF</div><div class="flow-arrow"><i class="fa-solid fa-arrow-right"></i></div><div class="flow-node"><i class="fa-solid fa-brain"></i><br>ML Model</div><div class="flow-arrow"><i class="fa-solid fa-arrow-right"></i></div><div class="flow-node"><i class="fa-solid fa-bullseye"></i><br>Prediction</div></div></div><div class="form-group" style="margin-bottom:28px;"><h3 style="font-size:17px;font-weight:600;color:#fff;margin-bottom:10px;">3. Machine Learning &amp; Model Comparison</h3><p style="font-size:14px;line-height:1.6;color:#d1d5db;margin-bottom:14px;">Multiple candidate architectures trained on n-gram TF-IDF representations and evaluated with stratified cross-validation:</p>' + cmp + '</div><div class="form-group"><h3 style="font-size:17px;font-weight:600;color:#fff;margin-bottom:10px;">4. Limitations &amp; Ethical Considerations</h3><div style="background:rgba(255,255,255,0.04);border-left:3px solid var(--uncertain-color);padding:14px 18px;border-radius:8px;font-size:13.5px;line-height:1.6;color:#d1d5db;"><p style="margin-bottom:8px;"><strong>Statistical Pattern vs Factual Ground Truth:</strong> TruthCheck AI evaluates stylistic and linguistic markers in journalism.</p><p>It is designed as an assistive verification aid and should be complemented by primary source verification and human judgment.</p></div></div></div></div>';
}

function renderResult(data) {
  if (!data) return renderHome();
  const pl = (data.prediction||'').toLowerCase();
  const cat = pl.includes('real')?'real':pl.includes('fake')?'fake':'uncertain';
  const icon = cat==='real'?'fa-circle-check':cat==='fake'?'fa-circle-xmark':'fa-circle-question';
  const label = cat==='real'?'Likely Real News':cat==='fake'?'Likely Fake News':'Uncertain / Inconclusive';
  const displayText = data.extracted_text || data.original_text || '';
  const wordCount = displayText.split(/\s+/).filter(Boolean).length;
  return '<div class="main-content-container anim" style="--d:0.1s"><div class="glass-card"><div class="result-badge-card ' + cat + '"><div class="prediction-pill ' + cat + '"><i class="fa-solid ' + icon + '"></i><span>' + label + '</span></div><div class="confidence-display">' + data.confidence + '%</div><p style="font-size:13.5px;color:#e5e7eb;font-weight:500;">Model Confidence Score</p><div class="confidence-bar-bg"><div class="confidence-bar-fill ' + cat + '" style="width:' + data.confidence + '%;"></div></div><p class="disclaimer-note"><i class="fa-solid fa-circle-info"></i> Confidence represents the statistical model\'s linguistic pattern classification, not absolute legal proof.</p></div><div class="meta-grid"><div class="meta-box"><div class="meta-box-label">Classification Model</div><div class="meta-box-value">' + escHtml(data.model_used||'ML Classifier') + '</div></div><div class="meta-box"><div class="meta-box-label">Input Source</div><div class="meta-box-value">' + escHtml(data.input_type||'') + '</div></div><div class="meta-box"><div class="meta-box-label">Timestamp</div><div class="meta-box-value">' + escHtml(data.timestamp||new Date().toLocaleString()) + '</div></div><div class="meta-box"><div class="meta-box-label">Record Reference</div><div class="meta-box-value">ID #' + (data.scan_id||'—') + ' (Stored in DB)</div></div></div><div class="form-group" style="margin-top:24px;"><label class="form-label" style="display:flex;justify-content:space-between;align-items:center;"><span><i class="fa-solid fa-quote-left" style="color:var(--muted);margin-right:6px;"></i>' + (data.extracted_text?'Extracted OCR Text':'Analyzed Article Content') + '</span><span style="font-size:12px;color:var(--muted);">' + wordCount + ' words</span></label><div class="text-preview-box">' + escHtml(displayText) + '</div></div><div class="hero-actions" style="margin-top:28px;"><a href="#" onclick="navigate(\'text-check\'); return false;" class="cta-btn"><i class="fa-solid fa-plus"></i><span>Check Another Article</span></a><a href="#" onclick="navigate(\'image-scanner\'); return false;" class="cta-btn-secondary"><i class="fa-solid fa-camera"></i><span>Scan Photo</span></a><a href="#" onclick="navigate(\'history\'); return false;" class="cta-btn-secondary"><i class="fa-solid fa-clock-rotate-left"></i><span>View in History</span></a></div></div></div>';
}
// ── API CALLS
async function analyzeText(headline, articleText) {
  const fd = new FormData(); fd.append('headline', headline); fd.append('article_text', articleText);
  const res = await fetch(API_BASE_URL + '/analyze-text', { method:'POST', body:fd });
  if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.error||'Server error: '+res.status); }
  return res.json();
}
async function analyzeImage(imageData, imageFile) {
  const fd = new FormData();
  if (imageData) fd.append('camera_image_data', imageData);
  else if (imageFile) fd.append('image_file', imageFile);
  const res = await fetch(API_BASE_URL + '/analyze-image', { method:'POST', body:fd });
  if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.error||'Server error: '+res.status); }
  return res.json();
}
async function fetchHistory(params) {
  const qs = new URLSearchParams(params||{}).toString();
  const res = await fetch(API_BASE_URL + '/api/history' + (qs?'?'+qs:''));
  if (!res.ok) throw new Error('Failed to load history: '+res.status);
  return res.json();
}
async function fetchHistoryDetail(scanId) {
  const res = await fetch(API_BASE_URL + '/api/history/' + scanId);
  if (!res.ok) throw new Error('Record not found: '+res.status);
  return res.json();
}
async function fetchAbout() {
  const res = await fetch(API_BASE_URL + '/api/about');
  if (!res.ok) throw new Error('Failed to load about data: '+res.status);
  return res.json();
}
async function apiDeleteHistory(scanId) {
  const res = await fetch(API_BASE_URL + '/api/history/' + scanId + '/delete', { method:'POST' });
  if (!res.ok) throw new Error('Delete failed: '+res.status);
  return res.json();
}

// ── DATA LOADERS
async function loadHistory(params) {
  const p = params||{}; const q=p.q||''; const pred=p.pred||'ALL'; const type=p.type||'ALL';
  try {
    const data = await fetchHistory({ q, pred, type });
    document.getElementById('page-content').innerHTML = renderHistoryContent(data.records||[], q, pred, type);
    bindPageEvents('history');
  } catch(e) {
    document.getElementById('page-content').innerHTML = renderHistoryContent([], q, pred, type);
    showFlash('Could not load history from backend. Is the Render server running? ' + e.message, 'error');
  }
}
async function loadAbout() {
  try {
    const data = await fetchAbout();
    document.getElementById('page-content').innerHTML = renderAboutContent(data.metadata||null);
  } catch(e) {
    document.getElementById('page-content').innerHTML = renderAboutContent(null);
    showFlash('Could not load metadata from backend. ' + e.message, 'warning');
  }
}
async function loadHistoryDetail(scanId) {
  try {
    const data = await fetchHistoryDetail(scanId);
    const rec = data.record;
    navigate('result', { prediction:rec.prediction, confidence:rec.confidence, model_used:rec.model_used, input_type:capitalize(rec.input_type), timestamp:rec.created_at, scan_id:rec.id, original_text:rec.original_text, extracted_text:rec.extracted_text });
  } catch(e) { showFlash('Could not load record: ' + e.message, 'error'); }
}
async function deleteHistoryItem(scanId) {
  if (!confirm('Are you sure you want to delete this verification record?')) return;
  try { await apiDeleteHistory(scanId); showFlash('Record deleted successfully.', 'success'); navigate('history'); }
  catch(e) { showFlash('Could not delete record: ' + e.message, 'error'); }
}
function doHistorySearch() {
  const q = document.getElementById('history-search-input')?.value || '';
  navigate('history', { q, pred:'ALL', type:'ALL' });
}
// ── EVENT BINDING
function bindPageEvents(page) {
  if (page==='text-check') bindTextCheckForm();
  if (page==='image-scanner') bindImageScannerEvents();
  if (page==='history') {
    const inp = document.getElementById('history-search-input');
    if(inp) inp.addEventListener('keydown', (e)=>{ if(e.key==='Enter') doHistorySearch(); });
  }
}

function bindTextCheckForm() {
  const form = document.getElementById('text-check-form');
  const btn = document.getElementById('analyze-submit-btn');
  if (!form||!btn) return;
  form.addEventListener('submit', async(e) => {
    e.preventDefault();
    const headline = document.getElementById('headline')?.value?.trim()||'';
    const articleText = document.getElementById('article_text')?.value?.trim()||'';
    if (!headline && !articleText) { showFlash('Please provide a news headline or article text to analyze.', 'error'); return; }
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i><span>Analyzing with ML Model...</span>';
    btn.disabled = true; clearFlash();
    try {
      const data = await analyzeText(headline, articleText);
      navigate('result', data);
    } catch(err) {
      showFlash('Analysis failed: ' + err.message, 'error');
      btn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i><span>Analyze News</span>';
      btn.disabled = false;
    }
  });
}

function bindImageScannerEvents() {
  const tabCamera=document.getElementById('tab-camera-btn'), tabUpload=document.getElementById('tab-upload-btn');
  const contentCamera=document.getElementById('camera-tab-content'), contentUpload=document.getElementById('upload-tab-content');
  if(tabCamera&&tabUpload) {
    tabCamera.addEventListener('click', ()=>{ tabCamera.classList.add('active'); tabUpload.classList.remove('active'); contentCamera.classList.add('active'); contentUpload.classList.remove('active'); startCamera(); });
    tabUpload.addEventListener('click', ()=>{ tabUpload.classList.add('active'); tabCamera.classList.remove('active'); contentUpload.classList.add('active'); contentCamera.classList.remove('active'); stopCamera(); });
  }
  const captureBtn=document.getElementById('capture-btn'), retakeBtn=document.getElementById('retake-btn');
  const analyzeBtn=document.getElementById('analyze-camera-btn'), video=document.getElementById('camera-video');
  const preview=document.getElementById('captured-preview'), dataInput=document.getElementById('camera-image-data');
  if(captureBtn) captureBtn.addEventListener('click', ()=>{
    if(!video||!video.videoWidth) return;
    const canvas=document.createElement('canvas'); canvas.width=video.videoWidth; canvas.height=video.videoHeight;
    canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);
    const dataUrl=canvas.toDataURL('image/jpeg',0.92);
    if(dataInput) dataInput.value=dataUrl;
    if(preview){preview.src=dataUrl;preview.removeAttribute('hidden');}
    video.style.display='none'; captureBtn.style.display='none';
    if(retakeBtn) retakeBtn.style.display='inline-flex';
    if(analyzeBtn) analyzeBtn.disabled=false;
  });
  if(retakeBtn) retakeBtn.addEventListener('click', ()=>{
    if(dataInput) dataInput.value=''; if(preview) preview.setAttribute('hidden','');
    if(video) video.style.display='block'; captureBtn.style.display='inline-flex';
    retakeBtn.style.display='none'; if(analyzeBtn) analyzeBtn.disabled=true;
  });
  if(analyzeBtn) analyzeBtn.addEventListener('click', async()=>{
    const imageData=dataInput?.value||'';
    if(!imageData){showFlash('Please capture a photo first.','error');return;}
    analyzeBtn.innerHTML='<i class="fa-solid fa-circle-notch fa-spin"></i><span>Running OCR &amp; Classifier...</span>';
    analyzeBtn.disabled=true; clearFlash();
    try {
      const data=await analyzeImage(imageData,null);
      if(!data.success){showFlash(data.message||'No readable text detected.','warning');analyzeBtn.innerHTML='<i class="fa-solid fa-magnifying-glass"></i><span>Analyze Photo</span>';analyzeBtn.disabled=false;}
      else navigate('result', data);
    } catch(err){showFlash('OCR failed: '+err.message,'error');analyzeBtn.innerHTML='<i class="fa-solid fa-magnifying-glass"></i><span>Analyze Photo</span>';analyzeBtn.disabled=false;}
  });
  const dropzone=document.getElementById('dropzone'), fileInput=document.getElementById('image-file-input');
  const previewCont=document.getElementById('upload-preview-container'), previewImg=document.getElementById('upload-preview-img');
  const filenameEl=document.getElementById('upload-filename'), clearBtn=document.getElementById('upload-clear-btn');
  const uploadBtn=document.getElementById('analyze-upload-btn'); let selectedFile=null;
  if(dropzone&&fileInput){
    dropzone.addEventListener('click',()=>fileInput.click());
    ['dragenter','dragover'].forEach(ev=>dropzone.addEventListener(ev,(e)=>{e.preventDefault();dropzone.classList.add('dragover');}));
    ['dragleave','drop'].forEach(ev=>dropzone.addEventListener(ev,(e)=>{e.preventDefault();dropzone.classList.remove('dragover');}));
    dropzone.addEventListener('drop',(e)=>{if(e.dataTransfer.files?.length){fileInput.files=e.dataTransfer.files;handleFileSelect(e.dataTransfer.files[0]);}});
    fileInput.addEventListener('change',()=>{if(fileInput.files?.length) handleFileSelect(fileInput.files[0]);});
  }
  function handleFileSelect(file){
    if(!file) return;
    if(file.size>5*1024*1024){alert('File exceeds 5 MB limit.');if(fileInput) fileInput.value='';return;}
    selectedFile=file;
    const reader=new FileReader();
    reader.onload=(e)=>{if(previewImg) previewImg.src=e.target.result;if(filenameEl) filenameEl.textContent=file.name+' ('+(file.size/1024).toFixed(1)+' KB)';if(previewCont) previewCont.style.display='block';if(dropzone) dropzone.style.display='none';if(uploadBtn) uploadBtn.disabled=false;};
    reader.readAsDataURL(file);
  }
  if(clearBtn) clearBtn.addEventListener('click',()=>{selectedFile=null;if(fileInput) fileInput.value='';if(previewCont) previewCont.style.display='none';if(dropzone) dropzone.style.display='block';if(uploadBtn) uploadBtn.disabled=true;});
  if(uploadBtn) uploadBtn.addEventListener('click', async()=>{
    if(!selectedFile){showFlash('Please select an image file first.','error');return;}
    uploadBtn.innerHTML='<i class="fa-solid fa-circle-notch fa-spin"></i><span>Extracting OCR &amp; Classifying...</span>';
    uploadBtn.disabled=true; clearFlash();
    try{
      const data=await analyzeImage(null,selectedFile);
      if(!data.success){showFlash(data.message||'No readable text detected.','warning');uploadBtn.innerHTML='<i class="fa-solid fa-magnifying-glass"></i><span>Analyze Image with OCR</span>';uploadBtn.disabled=false;}
      else navigate('result',data);
    }catch(err){showFlash('OCR failed: '+err.message,'error');uploadBtn.innerHTML='<i class="fa-solid fa-magnifying-glass"></i><span>Analyze Image with OCR</span>';uploadBtn.disabled=false;}
  });
}

// ── CAMERA
async function startCamera(){
  const video=document.getElementById('camera-video'), errMsg=document.getElementById('camera-error-message');
  if(!video) return; if(errMsg) errMsg.style.display='none';
  try{
    if(navigator.mediaDevices?.getUserMedia){
      _cameraStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}});
      video.srcObject=_cameraStream; await video.play();
      const cb=document.getElementById('capture-btn'); if(cb) cb.disabled=false;
    } else { showCameraError('Camera requires a secure HTTPS context.'); }
  }catch(err){
    let msg='Could not access camera. Please allow permissions or upload an image file.';
    if(err.name==='NotAllowedError') msg='Camera permission was denied.';
    else if(err.name==='NotFoundError') msg='No camera hardware detected.';
    showCameraError(msg);
  }
}
function stopCamera(){ if(_cameraStream){_cameraStream.getTracks().forEach(t=>t.stop());_cameraStream=null;} }
function showCameraError(msg){ const el=document.getElementById('camera-error-message'); if(el){el.textContent=msg;el.style.display='block';} }
async function initCamera(){ const c=document.getElementById('camera-tab-content'); if(c?.classList.contains('active')) await startCamera(); }

// ── STATS COUNT-UP
function initStatsCountUp(){
  const statsSection=document.querySelector('.stats'), statNumbers=document.querySelectorAll('.stat-number');
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function easeOut(x){return 1-Math.pow(1-x,3);}
  function startCountUp(){
    statNumbers.forEach((el,i)=>{
      const target=parseFloat(el.getAttribute('data-target')||'0'), decimals=parseInt(el.getAttribute('data-decimals')||'0',10);
      if(reduced){el.textContent=target.toFixed(decimals);return;}
      setTimeout(()=>{
        const st=performance.now();
        function upd(now){const p=Math.min((now-st)/(1400+i*80),1);el.textContent=(easeOut(p)*target).toFixed(decimals);if(p<1)requestAnimationFrame(upd);else el.textContent=target.toFixed(decimals);}
        requestAnimationFrame(upd);
      },400+i*90);
    });
  }
  if(statsSection){let t=false;const obs=new IntersectionObserver((ents)=>{ents.forEach(e=>{if(e.isIntersecting&&!t){t=true;startCountUp();obs.disconnect();}});},{threshold:0.25});obs.observe(statsSection);setTimeout(()=>{if(!t){t=true;startCountUp();obs.disconnect();}},300);}
}

// ── SAMPLE FILLER
window.fillSample = function(type){
  const h=document.getElementById('headline'), a=document.getElementById('article_text');
  if(!h||!a) return;
  if(type==='real'){
    h.value='NASA James Webb Space Telescope Discovers Distant Primitive Galaxy';
    a.value='Astronomers using the James Webb Space Telescope confirmed the detection of a galaxy formed just 300 million years after the Big Bang. The peer-reviewed research published in Nature Astronomy revealed spectroscopic redshift measurements confirming primitive stellar populations.';
  } else if(type==='fake'){
    h.value='SHOCKING: Secret Miracle Lemon Tonic Cures All Stage 4 Cancer Overnight - Doctors BANNED It!';
    a.value='Doctors and big pharma billionaires are terrified! Drinking boiled lemon water with baking soda and secret volcanic minerals completely cures all terminal diseases in 24 hours! Government whistleblowers leaked the classified formula before their laboratory was raided. Share this immediately before it gets taken down!';
  }
};

// ── BOOTSTRAP
document.addEventListener('DOMContentLoaded', ()=>{ navigate('home'); window.addEventListener('beforeunload', stopCamera); });
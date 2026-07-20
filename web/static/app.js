/**
 * Email Production Agent — Frontend
 * Handles brief form submission, sample loading, result display,
 * and mode toggling (structured vs freeform).
 */

const form = document.getElementById('brief-form');
const sampleSelect = document.getElementById('sample-select');
const generateBtn = document.getElementById('generate-btn');
const validationErrors = document.getElementById('validation-errors');
const emptyState = document.getElementById('empty-state');
const loadingState = document.getElementById('loading-state');
const resultsContent = document.getElementById('results-content');
const modeNote = document.getElementById('mode-note');
const freeformInput = document.getElementById('freeform-input');
const freeformTextarea = document.getElementById('freeform_text');
const formFields = document.getElementById('brief-form');
const briefInput = document.getElementById('brief-input');
const campaignDetails = document.getElementById('campaign-details');
const panelHeader = document.querySelector('.brief-panel .panel-header h2');

// Sample briefs injected from server
let samples = {};
let currentMode = 'freeform';

// Initialize: show freeform, hide structured form
freeformInput.classList.remove('hidden');
formFields.classList.add('hidden');

// Load samples on page load
fetch('/api/samples')
  .then(r => r.json())
  .then(data => { samples = data; })
  .catch(() => {});

// ── Mode Toggle ──
document.querySelectorAll('.mode-option').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.mode-option').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentMode = btn.dataset.mode;

    if (currentMode === 'freeform') {
      freeformInput.classList.remove('hidden');
      formFields.classList.add('hidden');
      sampleSelect.closest('.sample-picker').style.opacity = '';
      sampleSelect.closest('.sample-picker').style.pointerEvents = '';
    } else {
      freeformInput.classList.add('hidden');
      formFields.classList.remove('hidden');
      sampleSelect.closest('.sample-picker').style.opacity = '';
      sampleSelect.closest('.sample-picker').style.pointerEvents = '';
    }
  });
});

// ── Sample Picker ──
sampleSelect.addEventListener('change', () => {
  const key = sampleSelect.value;
  if (!key || !samples[key]) {
    // Clear textarea when "Custom prompt" selected in freeform
    if (currentMode === 'freeform') {
      freeformTextarea.value = '';
    }
    return;
  }
  const s = samples[key];

  if (currentMode === 'freeform' && s.freeform_text) {
    freeformTextarea.value = s.freeform_text;
  } else {
    // Structured mode — fill form fields
    document.getElementById('campaign_name').value = s.campaign_name || '';
    document.getElementById('audience').value = s.audience || '';
    document.getElementById('goal').value = s.goal || '';
    document.getElementById('key_message').value = s.key_message || '';
    document.getElementById('cta_text').value = s.cta_text || '';
    document.getElementById('cta_url').value = s.cta_url || '';
    document.getElementById('tone').value = s.tone || 'product_launch';
    document.getElementById('template_type').value = s.template_type || 'product_launch';
    document.getElementById('event_date').value = s.event_date || '';
    document.getElementById('additional_context').value = s.additional_context || '';
  }
});

// ── New Campaign button ──
document.getElementById('btn-new-campaign').addEventListener('click', () => {
  // Reset to input mode
  campaignDetails.classList.add('hidden');
  briefInput.classList.remove('hidden');
  generateBtn.classList.remove('hidden');
  document.getElementById('generate-area').classList.remove('hidden');
  panelHeader.textContent = 'Campaign Brief';
  emptyState.classList.remove('hidden');
  resultsContent.classList.add('hidden');

  // Clear results
  document.getElementById('result-subject').textContent = '';
  document.getElementById('result-preview').textContent = '';
  document.getElementById('email-iframe').srcdoc = '';
  document.getElementById('sync-status').classList.add('hidden');
});
generateBtn.addEventListener('click', (e) => {
  e.preventDefault();
  clearErrors();

  if (currentMode === 'freeform') {
    submitFreeform();
  } else {
    // Validate structured form fields exist and are accessible
    if (!formFields.classList.contains('hidden')) {
      submitStructured();
    }
  }
});

async function submitFreeform() {
  const text = freeformTextarea.value.trim();
  if (!text) {
    showErrors(['Please enter campaign details in the text area.']);
    return;
  }

  showLoading();
  const steps = getSteps();
  const isRealGeneration = text.length > 0;

  // Show parse step
  steps.parse.classList.remove('hidden');

  // Animate: Parse
  setTimeout(() => markStep(steps.parse, 'active'), 100);
  setTimeout(() => markStep(steps.parse, 'done'), 600);
  setTimeout(() => markStep(steps.validate, 'active'), 700);

  try {
    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ freeform_text: text }),
    });

    const result = await resp.json();

    if (result.status === 'failed') {
      markStep(steps.validate, 'done');
      markStep(steps.generate, 'done');
      markStep(steps.brand, 'done');
      markStep(steps.preview, 'done');
      steps.parse.classList.add('hidden');
      showErrors(result.errors);
      hideLoading();
      return;
    }

    // Complete remaining steps
    markStep(steps.validate, 'done');
    setTimeout(() => { markStep(steps.generate, 'active'); }, 200);
    setTimeout(() => { markStep(steps.generate, 'done'); }, 600);
    setTimeout(() => { markStep(steps.brand, 'active'); }, 700);
    setTimeout(() => { markStep(steps.brand, 'done'); }, 1100);
    setTimeout(() => { markStep(steps.preview, 'active'); }, 1200);
    setTimeout(() => { markStep(steps.preview, 'done'); }, 1600);
    setTimeout(() => {
      steps.parse.classList.add('hidden');
      showResults(result);
    }, 1800);

  } catch (err) {
    steps.parse.classList.add('hidden');
    showErrors([`Network error: ${err.message}`]);
    hideLoading();
  }
}

async function submitStructured() {
  const data = {
    campaign_name: document.getElementById('campaign_name').value.trim(),
    audience: document.getElementById('audience').value.trim(),
    goal: document.getElementById('goal').value.trim(),
    key_message: document.getElementById('key_message').value.trim(),
    cta_text: document.getElementById('cta_text').value.trim(),
    cta_url: document.getElementById('cta_url').value.trim(),
    tone: document.getElementById('tone').value,
    template_type: document.getElementById('template_type').value,
    additional_context: document.getElementById('additional_context').value.trim(),
    event_date: document.getElementById('event_date').value.trim() || null,
  };

  showLoading();
  const steps = getSteps();
  steps.parse.classList.add('hidden');

  // Animate step progress
  setTimeout(() => markStep(steps.validate, 'active'), 100);
  setTimeout(() => markStep(steps.validate, 'done'), 400);
  setTimeout(() => markStep(steps.generate, 'active'), 500);

  try {
    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result = await resp.json();

    if (result.status === 'failed') {
      markStep(steps.generate, 'done');
      markStep(steps.brand, 'done');
      markStep(steps.preview, 'done');
      showErrors(result.errors);
      hideLoading();
      return;
    }

    markStep(steps.generate, 'done');
    setTimeout(() => { markStep(steps.brand, 'active'); }, 200);
    setTimeout(() => { markStep(steps.brand, 'done'); }, 600);
    setTimeout(() => { markStep(steps.preview, 'active'); }, 700);
    setTimeout(() => { markStep(steps.preview, 'done'); }, 1000);
    setTimeout(() => showResults(result), 1200);

  } catch (err) {
    showErrors([`Network error: ${err.message}`]);
    hideLoading();
  }
}

function getSteps() {
  return {
    parse: document.getElementById('step-parse'),
    validate: document.getElementById('step-validate'),
    generate: document.getElementById('step-generate'),
    brand: document.getElementById('step-brand'),
    preview: document.getElementById('step-preview'),
  };
}

function markStep(el, state) {
  if (!el) return;
  el.className = state;
}

function showLoading() {
  emptyState.classList.add('hidden');
  resultsContent.classList.add('hidden');
  loadingState.classList.remove('hidden');
  generateBtn.disabled = true;
  generateBtn.innerHTML = 'Generating\u2026';
}

function hideLoading() {
  loadingState.classList.add('hidden');
  generateBtn.disabled = false;
  generateBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5"/><path d="M12 12v9"/></svg> Generate Email';
}

function showErrors(errors) {
  validationErrors.classList.remove('hidden');
  validationErrors.innerHTML = '<h4>Brief Validation Failed</h4><ul>' +
    errors.map(e => `<li>${escapeHtml(e)}</li>`).join('') +
    '</ul>';
}

function clearErrors() {
  validationErrors.classList.add('hidden');
  validationErrors.innerHTML = '';
}

function showResults(result) {
  hideLoading();
  emptyState.classList.add('hidden');
  resultsContent.classList.remove('hidden');

  // Metadata bar
  document.getElementById('result-subject').textContent = result.subject_line;
  document.getElementById('result-preview').textContent = result.preview_text;
  document.getElementById('result-template-tag').textContent = result.template_used || 'custom';

  // Brand chip
  const brandStatus = document.getElementById('brand-status');
  if (result.brand_passed) {
    brandStatus.textContent = '\u2713 Passed';
    brandStatus.className = 'meta-chip meta-brand passed';
  } else {
    brandStatus.textContent = '\u2717 Issues';
    brandStatus.className = 'meta-chip meta-brand failed';
  }

  // Confidence chip
  const confChip = document.getElementById('confidence-display');
  const score = result.confidence_score;
  confChip.textContent = score + '/5';
  confChip.className = 'meta-chip meta-confidence conf-' + score;

  // Violations
  const violationsDiv = document.getElementById('brand-violations');
  if (result.brand_violations && result.brand_violations.length > 0) {
    violationsDiv.innerHTML = '<div class="brand-violations-list">' +
      result.brand_violations.map(v => `
        <div class="violation-item">
          <span class="violation-severity severity-${v.severity}">${v.severity}</span>
          <div>
            <strong>[${v.location}]</strong> ${v.rule}
            <div style="color:#666;font-size:11px;">${v.detail}</div>
          </div>
        </div>
      `).join('') +
      '</div>';
    violationsDiv.classList.remove('hidden');
  } else {
    violationsDiv.classList.add('hidden');
  }

  // Email iframe
  document.getElementById('email-iframe').srcdoc = result.html_body;
  document.getElementById('email-html-code').textContent = result.html_body;
  document.getElementById('email-plain-code').textContent = result.plain_text;

  // Mode note
  const provider = result.provider || 'demo';
  if (provider === 'DeepSeek') {
    modeNote.textContent = 'Live mode \u2014 using DeepSeek API for real generation.';
  } else if (provider === 'Claude') {
    modeNote.textContent = 'Live mode \u2014 using Claude API for real generation.';
  } else {
    modeNote.textContent = 'Demo mode \u2014 no API key configured. Realistic simulated output.';
  }

  // Sync status
  if (result.sync) {
    const syncDiv = document.getElementById('sync-status');
    if (result.sync.success) {
      syncDiv.innerHTML = result.sync.preview_url
        ? `<span class="brand-passed">\u2713 Synced to Customer.io</span> <a href="${result.sync.preview_url}" target="_blank" style="font-size:13px;color:var(--brand-500);">Open in Design Studio \u2192</a>`
        : `<span class="brand-passed">\u2713 ${result.sync.detail}</span>`;
    } else {
      syncDiv.innerHTML = `<span class="brand-failed">\u2717 Sync failed: ${result.sync.detail}</span>`;
    }
    syncDiv.classList.remove('hidden');
  }
  if (window.innerWidth < 960) {
    document.getElementById('results-panel').scrollIntoView({ behavior: 'smooth' });
  }

  // Populate structured form with parsed fields when in freeform mode
  if (result.parsed_fields && currentMode === 'freeform') {
    const p = result.parsed_fields;
    document.getElementById('campaign_name').value = p.campaign_name || '';
    document.getElementById('audience').value = p.audience || '';
    document.getElementById('goal').value = p.goal || '';
    document.getElementById('key_message').value = p.key_message || '';
    document.getElementById('cta_text').value = p.cta_text || '';
    document.getElementById('cta_url').value = p.cta_url || '';
    document.getElementById('tone').value = p.tone || 'educational';
    document.getElementById('template_type').value = p.template_type || 'educational';
    document.getElementById('event_date').value = p.event_date || '';
    document.getElementById('additional_context').value = p.additional_context || '';
  }

  // Gather brief data from form fields (works in both modes since parsed fields backfill)
  const briefData = {
    campaign_name: document.getElementById('campaign_name').value || result.subject_line?.split('\u2014')[0]?.trim() || '',
    audience: document.getElementById('audience').value || '',
    goal: document.getElementById('goal').value || '',
    key_message: document.getElementById('key_message').value || '',
    cta_text: document.getElementById('cta_text').value || '',
    cta_url: document.getElementById('cta_url').value || '',
    tone: document.getElementById('tone').value || '',
    template_type: document.getElementById('template_type').value || '',
    event_date: document.getElementById('event_date').value || '',
    additional_context: document.getElementById('additional_context').value || '',
  };

  // Switch left panel to campaign details
  briefInput.classList.add('hidden');
  campaignDetails.classList.remove('hidden');
  panelHeader.textContent = 'Campaign Details';

  // Populate details
  document.getElementById('detail-name').textContent = briefData.campaign_name || '\u2014';
  document.getElementById('detail-audience').textContent = briefData.audience || '\u2014';
  document.getElementById('detail-goal').textContent = briefData.goal || '\u2014';
  document.getElementById('detail-message').textContent = briefData.key_message || '\u2014';
  document.getElementById('detail-cta').textContent = (briefData.cta_text || '\u2014') + ' \u2192';
  document.getElementById('detail-url').textContent = briefData.cta_url || '\u2014';

  const toneMap = {product_launch:'Product Launch',event:'Event',feature_update:'Feature Update',educational:'Educational',reengagement:'Re-engagement'};
  document.getElementById('detail-tone').textContent = toneMap[briefData.tone] || briefData.tone || '\u2014';
  const templateMap = {product_launch:'Product Launch',event_invite:'Event Invite',feature_update:'Feature Update',educational:'Educational',reengagement:'Re-engagement'};
  document.getElementById('detail-template').textContent = templateMap[briefData.template_type] || briefData.template_type || '\u2014';

  if (briefData.event_date) {
    document.getElementById('detail-event-row').classList.remove('hidden');
    document.getElementById('detail-event').textContent = briefData.event_date;
  } else {
    document.getElementById('detail-event-row').classList.add('hidden');
  }
  if (briefData.additional_context) {
    document.getElementById('detail-context-row').classList.remove('hidden');
    document.getElementById('detail-context').textContent = briefData.additional_context;
  } else {
    document.getElementById('detail-context-row').classList.add('hidden');
  }
}

// ── Device Toggle ──
let currentDevice = 'desktop';
const previewWrapper = document.getElementById('preview-wrapper');

document.querySelectorAll('.device-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.device-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentDevice = btn.dataset.device;
    if (currentDevice === 'mobile') {
      previewWrapper.classList.add('mobile');
    } else {
      previewWrapper.classList.remove('mobile');
    }
  });
});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const tabName = tab.dataset.tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    document.getElementById('tab-' + tabName).classList.remove('hidden');
  });
});

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

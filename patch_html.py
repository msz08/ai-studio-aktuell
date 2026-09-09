with open("legvan-tv-remote/scripts/static/index.html", "r") as f:
    html = f.read()

# 1. Replace the Input button with Tools button
old_input = '<button class="ibtn" title="Input / Source" onclick="key(178)">⊞</button>'
new_input = '<button class="ibtn" title="Tools" onclick="openToolsModal()">🛠</button>'
html = html.replace(old_input, new_input)

# 2. Remove Google Assistant button
old_assistant = """  <!-- Google Assistant / Search -->
  <button class="assistant" title="Google Assistant" onclick="assistant()">
    <span class="mic">🎙</span>
    <span>Google Assistant</span>
  </button>"""
html = html.replace(old_assistant, "")

# 3. Replace Recent Apps button with Apps Modal button
old_apps = '<button class="nav-btn" onclick="key(187)" title="Recent Apps">'
new_apps = '<button class="nav-btn" onclick="openAppsModal()" title="Apps">'
html = html.replace(old_apps, new_apps)

# 4. Insert new Modals HTML just before <!-- Text input modal -->
old_modal_start = "<!-- Text input modal -->"

new_modals = """
<!-- Tools Modal -->
<div class="text-modal" id="tools-modal" onclick="onToolsBgClick(event)">
  <div class="text-card" style="width: 320px;">
    <div class="text-card-title">🛠 TV Tools</div>
    <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
      <button class="text-send" onclick="document.getElementById('apk-upload').click()" style="background: #34c759;">Install APK</button>
      <input type="file" id="apk-upload" accept=".apk" style="display: none;" onchange="uploadFile(this, '/api/tools/install')">
      
      <button class="text-send" onclick="document.getElementById('file-upload').click()" style="background: #007aff;">Push File to Downloads</button>
      <input type="file" id="file-upload" style="display: none;" onchange="uploadFile(this, '/api/tools/push')">
      
      <button class="text-send" onclick="toolsAction('screenshot')" style="background: #ff9800;">Take Screenshot</button>
      <button class="text-send" onclick="toolsAction('storage')" style="background: #6c757d;">Check Storage</button>
      <button class="text-send" onclick="toolsAction('clearcache')" style="background: #dc3545;">Clear Background Apps</button>
      <button class="text-send" onclick="toolsAction('reboot')" style="background: #1c1c1e; border: 1px solid #333;">Reboot TV</button>
    </div>
    <div class="text-hint" style="margin-top: 15px;">Tap outside to close</div>
  </div>
</div>

<!-- Apps Modal -->
<div class="text-modal" id="apps-modal" onclick="onAppsBgClick(event)">
  <div class="text-card" style="width: 340px; max-height: 80vh; display: flex; flex-direction: column;">
    <div class="text-card-title">Launch App</div>
    <div id="apps-list" style="overflow-y: auto; display: flex; flex-direction: column; gap: 8px; margin-top: 10px; padding-right: 5px;">
        <div style="text-align: center; color: white;">Loading...</div>
    </div>
    <div class="text-hint" style="margin-top: 15px;">Tap outside to close</div>
  </div>
</div>

<!-- Screenshot Modal (Overlay) -->
<div class="text-modal" id="screenshot-modal" onclick="onScreenshotBgClick(event)" style="z-index: 1000;">
  <div style="max-width: 90vw; max-height: 90vh;">
    <img id="screenshot-img" src="" style="max-width: 100%; max-height: 90vh; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.8);">
  </div>
</div>

"""
html = html.replace(old_modal_start, new_modals + old_modal_start)

# 5. Insert Javascript
old_js_end = "// ─── Numpad modal ───"
new_js = """
// ─── Tools & Apps Modals ───
function openToolsModal() { document.getElementById('tools-modal').classList.add('open'); }
function closeToolsModal() { document.getElementById('tools-modal').classList.remove('open'); }
function onToolsBgClick(e) { if (e.target === document.getElementById('tools-modal')) closeToolsModal(); }

function openAppsModal() { 
  document.getElementById('apps-modal').classList.add('open'); 
  loadApps();
}
function closeAppsModal() { document.getElementById('apps-modal').classList.remove('open'); }
function onAppsBgClick(e) { if (e.target === document.getElementById('apps-modal')) closeAppsModal(); }

function onScreenshotBgClick(e) { document.getElementById('screenshot-modal').classList.remove('open'); }

async function toolsAction(action) {
  closeToolsModal();
  toast('Executing...');
  try {
    if (action === 'screenshot') {
      const img = document.getElementById('screenshot-img');
      img.src = '';
      const r = await fetch(`${BASE}/api/tools/screenshot`);
      if (r.ok) {
        const blob = await r.blob();
        img.src = URL.createObjectURL(blob);
        document.getElementById('screenshot-modal').classList.add('open');
      } else {
        toast('Failed to capture screen', true);
      }
      return;
    }
    
    let method = action === 'storage' ? 'GET' : 'POST';
    const r = await fetch(`${BASE}/api/tools/${action}`, { method });
    const d = await r.json();
    if (d.ok) toast(d.msg || 'Success');
    else toast(d.error || 'Action failed', true);
  } catch (e) {
    toast('Server unreachable', true);
  }
}

async function uploadFile(input, endpoint) {
  const file = input.files[0];
  if (!file) return;
  closeToolsModal();
  toast(`Uploading ${file.name}... (takes a while)`);
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const r = await fetch(`${BASE}${endpoint}`, {
      method: 'POST',
      body: formData
    });
    const d = await r.json();
    if (d.ok) toast(`Success! ${d.msg || ''}`);
    else toast(d.error || 'Upload failed', true);
  } catch (e) {
    toast('Server unreachable', true);
  }
  input.value = ''; // Reset input
}

async function loadApps() {
  const list = document.getElementById('apps-list');
  try {
    const r = await fetch(`${BASE}/api/apps`);
    const d = await r.json();
    if (d.ok) {
      list.innerHTML = '';
      d.apps.forEach(pkg => {
        const btn = document.createElement('button');
        btn.className = 'text-send';
        btn.style.background = 'rgba(255,255,255,0.1)';
        btn.style.justifyContent = 'flex-start';
        btn.style.padding = '12px 15px';
        btn.textContent = formatAppName(pkg);
        btn.onclick = () => { closeAppsModal(); launch(pkg); };
        list.appendChild(btn);
      });
    }
  } catch (e) {
    list.innerHTML = '<div style="color:red">Failed to load apps</div>';
  }
}

"""
html = html.replace(old_js_end, new_js + old_js_end)

with open("legvan-tv-remote/scripts/static/index.html", "w") as f:
    f.write(html)

print("HTML Patched.")

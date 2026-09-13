// In-App Auto Updater Client Module for HomeTheaterX
import { apiGet, apiPost, showToast } from './api.js';
import { addWsListener } from './ws.js';

let latestReleaseData = null;
let isDownloading = false;

export function initUpdater() {
  const btnCheckUpdates = document.getElementById('btn-check-updates');
  const btnOpenModal = document.getElementById('btn-open-update-modal');
  const btnCloseModal = document.getElementById('btn-close-update-modal');
  const btnCancelUpdate = document.getElementById('btn-cancel-update');
  const btnStartUpdate = document.getElementById('btn-start-update');

  if (btnCheckUpdates) {
    btnCheckUpdates.addEventListener('click', () => {
      checkForUpdates(false);
    });
  }

  if (btnOpenModal) {
    btnOpenModal.addEventListener('click', () => {
      if (latestReleaseData) {
        showUpdateModal(latestReleaseData);
      }
    });
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', hideUpdateModal);
  }

  if (btnCancelUpdate) {
    btnCancelUpdate.addEventListener('click', hideUpdateModal);
  }

  if (btnStartUpdate) {
    btnStartUpdate.addEventListener('click', () => {
      if (isDownloading) return;
      const statusText = document.getElementById('modal-download-status');
      if (statusText && statusText.dataset.state === 'downloaded') {
        applyUpdateAndRestart();
      } else {
        startUpdateDownload();
      }
    });
  }

  // Listen to WebSocket update_progress broadcasts
  addWsListener((payload) => {
    if (payload && payload.type === 'update_progress' && payload.data) {
      handleDownloadProgress(payload.data);
    }
  });

  // Perform a silent background update check after 3 seconds
  setTimeout(() => {
    checkForUpdates(true);
  }, 3000);
}

export async function checkForUpdates(silent = false) {
  const btnCheck = document.getElementById('btn-check-updates');
  const statusLabel = document.getElementById('update-status-label');
  const tabBadge = document.getElementById('tab-update-badge');
  const settingsBanner = document.getElementById('settings-update-banner');
  const settingsTitle = document.getElementById('settings-update-title');

  if (btnCheck && !silent) {
    btnCheck.disabled = true;
    btnCheck.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-[10px]"></i><span>Checking...</span>`;
  }

  try {
    const res = await apiGet('/api/updates/check');
    if (res && res.status === 'success' && res.data) {
      const data = res.data;
      latestReleaseData = data;

      if (data.has_update) {
        // Update available!
        if (tabBadge) tabBadge.classList.remove('hidden');
        if (settingsBanner) settingsBanner.classList.remove('hidden');
        if (settingsTitle) {
          settingsTitle.innerText = `New version ${data.tag_name || data.latest_version} available!`;
        }
        if (statusLabel) {
          statusLabel.innerText = `Update Available: ${data.tag_name} (Current: v${data.current_version})`;
          statusLabel.className = 'text-[9px] text-amber-400 font-bold tracking-widest mt-1 uppercase';
        }

        if (!silent) {
          showToast(`Update Available: ${data.tag_name}`, 'info');
          showUpdateModal(data);
        }
      } else {
        // Up to date
        if (tabBadge) tabBadge.classList.add('hidden');
        if (settingsBanner) settingsBanner.classList.add('hidden');
        if (statusLabel) {
          statusLabel.innerText = `Up to date (v${data.current_version}) • ChamathSadaru/HomeTheaterX-V2`;
          statusLabel.className = 'text-[9px] text-emerald-400 tracking-widest mt-1 uppercase';
        }

        if (!silent) {
          showToast('HomeTheaterX is up to date!', 'success');
        }
      }
    } else {
      if (!silent) {
        showToast('Unable to check for updates.', 'error');
      }
    }
  } catch (err) {
    console.error('[Updater] Check failed:', err);
    if (!silent) {
      showToast('Update check failed. Check your internet connection.', 'error');
    }
  } finally {
    if (btnCheck && !silent) {
      btnCheck.disabled = false;
      btnCheck.innerHTML = `<i class="fa-solid fa-arrows-rotate text-[10px]"></i><span>Check for Updates</span>`;
    }
  }
}

export function showUpdateModal(data) {
  const modal = document.getElementById('modal-update');
  const badge = document.getElementById('modal-update-badge');
  const tagline = document.getElementById('modal-update-tagline');
  const notes = document.getElementById('modal-release-notes');
  const progressBox = document.getElementById('modal-download-progress-box');
  const btnStart = document.getElementById('btn-start-update');
  const btnStartText = document.getElementById('btn-start-update-text');

  if (!modal) return;

  if (badge) badge.innerText = data.tag_name || `v${data.latest_version}`;
  if (tagline) tagline.innerText = data.release_name || 'A new version is available for download';
  
  if (notes) {
    const rawNotes = data.release_notes || 'No changelog notes provided for this release.';
    notes.innerText = rawNotes;
  }

  // Reset progress state if not already downloading
  if (!isDownloading) {
    if (progressBox) progressBox.classList.add('hidden');
    if (btnStart) btnStart.disabled = false;
    if (btnStartText) btnStartText.innerText = 'Download & Install';
  }

  modal.classList.remove('hidden');
}

export function hideUpdateModal() {
  const modal = document.getElementById('modal-update');
  if (modal) modal.classList.add('hidden');
}

export async function startUpdateDownload() {
  if (!latestReleaseData || !latestReleaseData.download_url) {
    showToast('No download asset found for this release.', 'error');
    return;
  }

  isDownloading = true;
  const progressBox = document.getElementById('modal-download-progress-box');
  const btnStart = document.getElementById('btn-start-update');
  const btnStartText = document.getElementById('btn-start-update-text');
  const btnCancel = document.getElementById('btn-cancel-update');

  if (progressBox) progressBox.classList.remove('hidden');
  if (btnStart) btnStart.disabled = true;
  if (btnStartText) btnStartText.innerText = 'Downloading...';
  if (btnCancel) btnCancel.classList.add('hidden');

  try {
    const res = await apiPost('/api/updates/download', {
      download_url: latestReleaseData.download_url
    });

    if (!res || res.status !== 'success') {
      showToast('Failed to start download.', 'error');
      isDownloading = false;
      if (btnStart) btnStart.disabled = false;
      if (btnCancel) btnCancel.classList.remove('hidden');
    }
  } catch (err) {
    console.error('[Updater] Download error:', err);
    showToast('Failed to trigger download.', 'error');
    isDownloading = false;
    if (btnStart) btnStart.disabled = false;
    if (btnCancel) btnCancel.classList.remove('hidden');
  }
}

function handleDownloadProgress(state) {
  const statusEl = document.getElementById('modal-download-status');
  const percentEl = document.getElementById('modal-download-percent');
  const barEl = document.getElementById('modal-download-bar');
  const speedEl = document.getElementById('modal-download-speed');
  const sizeEl = document.getElementById('modal-download-size');
  const btnStart = document.getElementById('btn-start-update');
  const btnStartText = document.getElementById('btn-start-update-text');

  if (percentEl) percentEl.innerText = `${state.progress}%`;
  if (barEl) barEl.style.width = `${state.progress}%`;
  if (speedEl) speedEl.innerText = `${state.speed_mbps || 0.0} MB/s`;

  const downloadedMB = (state.downloaded_bytes / (1024 * 1024)).toFixed(1);
  const totalMB = (state.total_bytes / (1024 * 1024)).toFixed(1);
  if (sizeEl) sizeEl.innerText = `${downloadedMB} MB / ${totalMB} MB`;

  if (state.status === 'downloading') {
    if (statusEl) statusEl.innerText = 'Downloading Update Package...';
  } else if (state.status === 'downloaded') {
    isDownloading = false;
    if (statusEl) {
      statusEl.innerText = 'Download Complete! Ready to Install.';
      statusEl.className = 'text-emerald-400 font-bold';
      statusEl.dataset.state = 'downloaded';
    }
    if (btnStart) {
      btnStart.disabled = false;
      btnStart.className = 'px-5 py-2 rounded-xl text-xs font-mono font-bold text-black bg-emerald-400 hover:bg-emerald-300 transition-all flex items-center gap-2 cursor-pointer';
    }
    if (btnStartText) btnStartText.innerText = 'Install & Restart Now';
    showToast('Update downloaded. Ready to install!', 'success');
  } else if (state.status === 'installing') {
    if (statusEl) {
      statusEl.innerText = 'Launching Installer & Restarting HomeTheaterX...';
      statusEl.className = 'text-amber-400 font-bold animate-pulse';
    }
    if (btnStart) btnStart.disabled = true;
  } else if (state.status === 'error') {
    isDownloading = false;
    if (statusEl) {
      statusEl.innerText = `Download Failed: ${state.error_msg || 'Unknown error'}`;
      statusEl.className = 'text-red-400 font-bold';
    }
    if (btnStart) {
      btnStart.disabled = false;
      if (btnStartText) btnStartText.innerText = 'Retry Download';
    }
    const btnCancel = document.getElementById('btn-cancel-update');
    if (btnCancel) btnCancel.classList.remove('hidden');
    showToast('Update download failed.', 'error');
  }
}

export async function applyUpdateAndRestart() {
  const statusEl = document.getElementById('modal-download-status');
  const btnStart = document.getElementById('btn-start-update');
  const btnStartText = document.getElementById('btn-start-update-text');

  if (statusEl) {
    statusEl.innerText = 'Installing update and relaunching HomeTheaterX...';
    statusEl.className = 'text-amber-400 font-bold animate-pulse';
  }
  if (btnStart) btnStart.disabled = true;
  if (btnStartText) btnStartText.innerText = 'Relaunching...';

  try {
    await apiPost('/api/updates/apply', { silent: true });
  } catch (err) {
    console.error('[Updater] Apply error:', err);
  }
}

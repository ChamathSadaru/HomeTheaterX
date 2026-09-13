// Bluetooth Receiver Client Module for HomeTheaterX
import { apiGet, apiPost, showToast } from './api.js';

export function initBluetooth() {
  const btnBt = document.getElementById('btn-bluetooth');
  const modal = document.getElementById('modal-bluetooth');
  const btnClose = document.getElementById('btn-close-bluetooth-modal');
  const btnOpenSettings = document.getElementById('btn-open-windows-bt');
  const btnSetName = document.getElementById('btn-set-bluetooth-name');
  const inputName = document.getElementById('input-bluetooth-name');

  if (btnBt) {
    btnBt.addEventListener('click', () => {
      openBluetoothModal();
    });
  }

  if (btnClose) {
    btnClose.addEventListener('click', () => {
      closeBluetoothModal();
    });
  }

  if (btnOpenSettings) {
    btnOpenSettings.addEventListener('click', async () => {
      try {
        await apiPost('/api/bluetooth/open_settings');
        showToast('Opening Windows Bluetooth Settings...', 'info');
      } catch (e) {
        showToast('Failed to open Bluetooth settings', 'error');
      }
    });
  }

  if (btnSetName && inputName) {
    btnSetName.addEventListener('click', async () => {
      const val = inputName.value.trim();
      if (!val) {
        showToast('Please enter a valid Bluetooth name', 'error');
        return;
      }
      btnSetName.disabled = true;
      try {
        const res = await apiPost('/api/bluetooth/set_name', { name: val });
        if (res && res.status === 'success') {
          showToast(res.message || `Bluetooth name updated to ${val}!`, 'success');
        } else {
          showToast(res.message || 'Failed to update Bluetooth name.', 'error');
        }
      } catch (err) {
        showToast('Administrator privileges required to change Bluetooth name.', 'error');
      } finally {
        btnSetName.disabled = false;
      }
    });
  }
}

export async function openBluetoothModal() {
  const modal = document.getElementById('modal-bluetooth');
  const inputName = document.getElementById('input-bluetooth-name');
  const devicesList = document.getElementById('bt-devices-list');

  if (modal) {
    modal.classList.remove('hidden');
  }

  try {
    const res = await apiGet('/api/bluetooth/status');
    if (res && res.status === 'success') {
      if (inputName && res.bluetooth_name) {
        inputName.value = res.bluetooth_name;
      }

      if (devicesList) {
        devicesList.innerHTML = '';
        const paired = res.paired_devices || [];
        if (paired.length === 0) {
          devicesList.innerHTML = '<span class="text-zinc-500 text-[11px] italic">No paired mobile/audio devices found. Click "Open Bluetooth" to pair a new device.</span>';
        } else {
          paired.forEach(dev => {
            const row = document.createElement('div');
            row.className = 'flex items-center justify-between py-1 px-2 rounded-lg bg-zinc-950/40 border border-zinc-850/50';
            row.innerHTML = `
              <div class="flex items-center gap-2">
                <i class="fa-solid fa-mobile-screen text-blue-400 text-xs"></i>
                <span class="text-xs text-white font-mono">${dev}</span>
              </div>
              <span class="text-[9px] text-emerald-400 font-mono tracking-wider font-bold">PAIRED</span>
            `;
            devicesList.appendChild(row);
          });
        }
      }
    }
  } catch (err) {
    console.error('[Bluetooth] Status fetch error:', err);
  }
}

export function closeBluetoothModal() {
  const modal = document.getElementById('modal-bluetooth');
  if (modal) {
    modal.classList.add('hidden');
  }
}

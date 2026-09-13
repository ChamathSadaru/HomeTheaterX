// 6-Channel Real-time Acoustic Scopes Visualizer Module
import { state } from './state.js';

export const scopesState = {
  mode: "waveform", // "waveform" | "bars" | "pixel"
  active: false
};

const CHANNELS = [
  { id: "towerL", name: "Front Left (Tower L)", code: "FL", color: "#f59e0b", glow: "rgba(245, 158, 11, 0.7)" },
  { id: "towerR", name: "Front Right (Tower R)", code: "FR", color: "#f59e0b", glow: "rgba(245, 158, 11, 0.7)" },
  { id: "center", name: "Center (Dialogue)", code: "C", color: "#10b981", glow: "rgba(16, 185, 129, 0.7)" },
  { id: "subwoofer", name: "Subwoofer (LFE / Bass)", code: "SUB", color: "#ef4444", glow: "rgba(239, 68, 68, 0.7)" },
  { id: "surroundL", name: "Surround Left (SL)", code: "SL", color: "#38bdf8", glow: "rgba(56, 189, 248, 0.7)" },
  { id: "surroundR", name: "Surround Right (SR)", code: "SR", color: "#38bdf8", glow: "rgba(56, 189, 248, 0.7)" }
];

const scopeContexts = {};
const smoothPeaks = {
  towerL: 0.0,
  towerR: 0.0,
  center: 0.0,
  subwoofer: 0.0,
  surroundL: 0.0,
  surroundR: 0.0
};
const barDecays = {
  towerL: new Array(18).fill(0),
  towerR: new Array(18).fill(0),
  center: new Array(18).fill(0),
  subwoofer: new Array(18).fill(0),
  surroundL: new Array(18).fill(0),
  surroundR: new Array(18).fill(0)
};

let offset = 0;
let dpr = window.devicePixelRatio || 1.5;

export function initChannelScopes() {
  CHANNELS.forEach(ch => {
    const canvas = document.getElementById(`scope-canvas-${ch.id}`);
    if (canvas) {
      scopeContexts[ch.id] = {
        canvas: canvas,
        ctx: canvas.getContext('2d')
      };
    }
  });

  setupAllHighDpiCanvases();
  window.addEventListener('resize', setupAllHighDpiCanvases);

  // Hook Mode Selector Buttons
  const modeButtons = document.querySelectorAll('.scope-mode-btn');
  modeButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const mode = btn.dataset.mode;
      if (mode) {
        scopesState.mode = mode;
        modeButtons.forEach(b => {
          b.className = "scope-mode-btn px-3 py-1 rounded-lg text-xs font-mono uppercase transition-all bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white cursor-pointer";
        });
        btn.className = "scope-mode-btn px-3 py-1 rounded-lg text-xs font-mono font-bold uppercase transition-all bg-amber-500 text-black shadow-[0_0_10px_rgba(245,158,11,0.3)] cursor-pointer";
      }
    });
  });

  requestAnimationFrame(renderAllScopesLoop);
}

export function setupAllHighDpiCanvases() {
  dpr = window.devicePixelRatio || 1.5;
  CHANNELS.forEach(ch => {
    const item = scopeContexts[ch.id];
    if (item && item.canvas) {
      const rect = item.canvas.getBoundingClientRect();
      const w = rect.width || 320;
      const h = rect.height || 100;
      item.canvas.width = Math.round(w * dpr);
      item.canvas.height = Math.round(h * dpr);
    }
  });
}

function renderAllScopesLoop() {
  const scopesContainer = document.getElementById('view-scopes');
  const isVisible = scopesContainer && !scopesContainer.classList.contains('hidden');

  if (isVisible) {
    offset += 0.058;

    CHANNELS.forEach(ch => {
      const item = scopeContexts[ch.id];
      if (item && item.canvas && item.ctx) {
        renderSingleScope(ch, item.canvas, item.ctx);
      }
    });
  }

  requestAnimationFrame(renderAllScopesLoop);
}

function renderSingleScope(ch, canvas, ctx) {
  const width = canvas.width / dpr;
  const height = canvas.height / dpr;
  const centerY = height / 2;

  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);

  // Hydraulic smoothing for per-channel peak
  const rawPeak = state.channelPeaks[ch.id] || 0.0;
  const simulatedPeak = (window.mediaPlayerIsPlaying) ? (0.12 + Math.sin(Date.now() / 180 + CHANNELS.indexOf(ch)) * 0.06) : 0.0;
  const targetPeak = Math.max(rawPeak, simulatedPeak);
  smoothPeaks[ch.id] = smoothPeaks[ch.id] * 0.76 + targetPeak * 0.24;
  const sPeak = smoothPeaks[ch.id];

  const chVol = (state.volumes[ch.id] || 80) / 100;
  const masterVol = (state.volumes["master"] || 100) / 100;
  const volumeFactor = chVol * masterVol;

  const amp = state.isSystemMuted ? 0 : Math.max(1.8, sPeak * 14.0);

  // Update dB level label
  const valLabel = document.getElementById(`scope-val-${ch.id}`);
  const meterBar = document.getElementById(`scope-meter-${ch.id}`);
  if (valLabel) {
    if (state.isSystemMuted || sPeak < 0.005) {
      valLabel.innerText = "-INF dB";
    } else {
      const db = Math.round(20 * Math.log10(Math.max(0.001, sPeak * volumeFactor)));
      valLabel.innerText = `${db} dB`;
    }
  }
  if (meterBar) {
    const percent = state.isSystemMuted ? 0 : Math.min(100, Math.round(sPeak * 100 * volumeFactor));
    meterBar.style.width = `${percent}%`;
  }

  const isGlass = document.body.classList.contains("glass-mode-active");
  const neonColor = isGlass ? "#38bdf8" : ch.color;
  const glowColor = isGlass ? "rgba(56, 189, 248, 0.75)" : ch.glow;

  if (scopesState.mode === "waveform") {
    // 1. Phosphor Neon Glow Wave
    ctx.save();
    ctx.shadowBlur = 10;
    ctx.shadowColor = glowColor;
    ctx.strokeStyle = neonColor;
    ctx.lineWidth = 2.8;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();

    const step = 3;
    let points = [];
    for (let x = 0; x <= width; x += step) {
      let y = centerY;
      if (ch.id === "subwoofer") {
        // Heavy low-frequency fundamental oscillation
        y += Math.sin(x * 0.015 + offset * 0.8) * amp * 1.3 * volumeFactor;
        y += Math.cos(x * 0.03 - offset * 0.5) * (amp * 0.5) * volumeFactor;
      } else if (ch.id === "center") {
        // Vocal formant mid-frequency envelope
        y += Math.sin(x * 0.038 + offset * 1.2) * amp * volumeFactor;
        y += Math.cos(x * 0.082 - offset * 1.6) * (amp * 0.4) * volumeFactor;
        y += Math.sin(x * 0.019 + offset * 0.7) * (amp * 0.25) * volumeFactor;
      } else if (ch.id === "towerL" || ch.id === "surroundL") {
        // Left channel harmonic wave
        y += Math.sin(x * 0.026 + offset + 0.5) * amp * volumeFactor;
        y += Math.cos(x * 0.06 - offset * 1.3) * (amp * 0.45) * volumeFactor;
      } else {
        // Right channel harmonic wave (antiphase offset)
        y += Math.sin(x * 0.026 + offset) * amp * volumeFactor;
        y += Math.cos(x * 0.06 - offset * 1.3 + 0.8) * (amp * 0.45) * volumeFactor;
      }
      points.push({ x, y });
    }

    if (points.length > 0) {
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
      }
      ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    }
    ctx.stroke();
    ctx.restore();

    // 2. Inner Razor-Sharp Core Line
    ctx.save();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.0;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    if (points.length > 0) {
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
      }
      ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    }
    ctx.stroke();
    ctx.restore();

  } else if (scopesState.mode === "bars") {
    const numBars = 16;
    const spacing = 3;
    const barWidth = Math.floor((width - (numBars - 1) * spacing) / numBars);
    const decays = barDecays[ch.id];

    for (let i = 0; i < numBars; i++) {
      const peakVal = state.isSystemMuted ? 0 : sPeak;
      const freqWeight = ch.id === "subwoofer" 
        ? Math.max(0.2, (numBars - i) / numBars * 1.5)
        : Math.sin((i / numBars) * Math.PI) * 0.4 + (1.0 - (i / numBars) * 0.5);

      const targetHeight = peakVal > 0.01
        ? ((Math.sin(i * 0.6 + offset) * 0.35 + 0.65) * peakVal * height * 0.85 * freqWeight * volumeFactor) + 2
        : 2 + Math.sin(i * 0.5 + offset) * 1.2;

      if (targetHeight > decays[i]) {
        decays[i] = targetHeight;
      } else {
        decays[i] = Math.max(2, decays[i] - 0.7);
      }

      const x = i * (barWidth + spacing);
      const y = height - targetHeight;

      ctx.fillStyle = neonColor;
      ctx.fillRect(x, y, barWidth, targetHeight);

      ctx.fillStyle = "#ffffff";
      ctx.fillRect(x, height - decays[i] - 2, barWidth, 1.5);
    }

  } else if (scopesState.mode === "pixel") {
    ctx.fillStyle = neonColor;
    const step = 5;
    for (let x = 0; x < width; x += step) {
      let y = centerY;
      y += Math.sin(x * 0.025 + offset) * amp * volumeFactor;
      y += Math.cos(x * 0.06 - offset * 1.3) * (amp * 0.4) * volumeFactor;

      const gridY = Math.round(y / 4) * 4;
      ctx.fillRect(x, gridY, 2.5, 2.5);
    }
  }

  ctx.restore();
}

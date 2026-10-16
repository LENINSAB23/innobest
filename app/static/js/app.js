/**
 * Controlador Principal de la Aplicación Web InnoBest
 * Gestiona navegación por pestañas, sincronización con MongoDB Atlas,
 * carga de estadísticas y alertas al usuario.
 */

class InnoBestApp {
  constructor() {
    this.initTabs();
    this.initHistory();
    this.initStats();
    this.initModelReload();
    this.initToasts();
  }

  initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-tab");

        tabBtns.forEach(b => b.classList.remove("active"));
        tabPanes.forEach(p => p.classList.remove("active"));

        btn.classList.add("active");
        const activePane = document.getElementById(targetId);
        if (activePane) activePane.classList.add("active");

        // Si se cambia a la pestaña de historial, refrescar datos de MongoDB
        if (targetId === "tab-history") {
          this.loadHistory();
        }
      });
    });
  }

  initStats() {
    this.loadStats();
    // Actualizar estadísticas cada 20 segundos
    setInterval(() => this.loadStats(), 20000);
  }

  async loadStats() {
    try {
      const res = await fetch("/api/stats");
      if (!res.ok) return;
      const data = await res.json();

      // Contadores en hero
      const statDetections = document.getElementById("stat-total-detections");
      if (statDetections) statDetections.textContent = data.total_detections || 0;

      // Chip de estado de MongoDB en Header
      const mongoChip = document.getElementById("header-mongo-chip");
      const mongoText = document.getElementById("header-mongo-text");
      if (mongoChip && mongoText) {
        if (data.connected_to_atlas) {
          mongoChip.className = "status-chip connected";
          mongoText.textContent = "MongoDB Atlas: Conectado (Cluster0)";
        } else {
          mongoChip.className = "status-chip warning";
          mongoText.textContent = `MongoDB: ${data.status_message}`;
        }
      }

      // Chip de Modelo YOLO en Header
      const modelChip = document.getElementById("header-model-chip");
      const modelText = document.getElementById("header-model-text");
      if (modelChip && modelText) {
        if (data.model_active) {
          modelChip.className = "status-chip connected";
          modelText.textContent = "YOLO: best.pt Activo";
        } else {
          modelChip.className = "status-chip warning";
          modelText.textContent = "YOLO: Modo Demostración (Standby)";
        }
      }
    } catch (e) {
      console.warn("No se pudieron cargar estadísticas:", e);
    }
  }

  initHistory() {
    const refreshBtn = document.getElementById("btn-refresh-history");
    const exportBtn = document.getElementById("btn-export-history");

    if (refreshBtn) refreshBtn.addEventListener("click", () => this.loadHistory(true));
    if (exportBtn) exportBtn.addEventListener("click", () => this.exportHistoryJson());

    // Cargar historial inicial
    this.loadHistory();
  }

  async loadHistory(showFeedback = false) {
    const tableBody = document.getElementById("history-table-body");
    const emptyNotice = document.getElementById("history-empty-notice");
    if (!tableBody) return;

    try {
      const res = await fetch("/api/history?limit=30");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      tableBody.innerHTML = "";

      if (!data.records || data.records.length === 0) {
        if (emptyNotice) emptyNotice.style.display = "block";
        return;
      }

      if (emptyNotice) emptyNotice.style.display = "none";

      data.records.forEach((rec, idx) => {
        const tr = document.createElement("tr");

        const sourceBadge = rec.source === "webcam"
          ? '<span style="background:#e0f2fe;color:#0369a1;padding:3px 8px;border-radius:12px;font-size:0.75rem;font-weight:700;">Webcam</span>'
          : '<span style="background:#fef3c7;color:#b45309;padding:3px 8px;border-radius:12px;font-size:0.75rem;font-weight:700;">Foto</span>';

        const confPct = rec.confidence_pct || (rec.confidence ? Math.round(rec.confidence * 100) : 0);
        const timeStr = rec.timestamp_str || (rec.timestamp ? rec.timestamp.substring(0, 19).replace("T", " ") : "-");

        tr.innerHTML = `
          <td><strong>#${idx + 1}</strong></td>
          <td><span style="font-weight:700;color:var(--green-950);">${rec.bird_name || "Desconocido"}</span></td>
          <td>${sourceBadge}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <div style="width:70px;height:8px;background:#e2e8f0;border-radius:6px;overflow:hidden;">
                <div style="width:${confPct}%;height:100%;background:#10b981;"></div>
              </div>
              <span style="font-size:0.8rem;font-weight:700;">${confPct}%</span>
            </div>
          </td>
          <td><span style="font-size:0.82rem;color:var(--slate-600);">${rec.region || "Huánuco"}</span></td>
          <td style="font-size:0.8rem;color:var(--slate-500);">${timeStr}</td>
          <td><code style="font-size:0.75rem;background:#f1f5f9;padding:2px 6px;border-radius:4px;">${String(rec._id).substring(0, 8)}...</code></td>
        `;

        tableBody.appendChild(tr);
      });

      if (showFeedback) {
        window.showToast("Historial de MongoDB Atlas actualizado.", "success");
      }
    } catch (e) {
      console.error("Error cargando historial de MongoDB:", e);
      if (showFeedback) {
        window.showToast("No se pudo obtener el historial de MongoDB.", "warning");
      }
    }
  }

  async exportHistoryJson() {
    try {
      const res = await fetch("/api/history?limit=200");
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data.records, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `detecciones_aves_huanuco_${new Date().toISOString().substring(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      window.showToast("Descargando exportación de detecciones en JSON...", "info");
    } catch (e) {
      window.showToast("Error al exportar datos.", "warning");
    }
  }

  initModelReload() {
    const btnReload = document.getElementById("btn-reload-model");
    if (btnReload) {
      btnReload.addEventListener("click", async () => {
        try {
          const res = await fetch("/api/model/reload", { method: "POST" });
          const data = await res.json();
          window.showToast(data.message, data.model_loaded ? "success" : "info");
          this.loadStats();
        } catch (e) {
          window.showToast("Error al solicitar recarga del modelo.", "warning");
        }
      });
    }
  }

  initToasts() {
    window.showToast = (message, type = "info") => {
      let container = document.getElementById("toast-container");
      if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
      }

      const toast = document.createElement("div");
      toast.className = "toast";

      let icon = "🌿";
      if (type === "success") icon = "✓";
      if (type === "warning") icon = "⚠";

      toast.innerHTML = `<span style="font-size:1.1rem;">${icon}</span> <span>${message}</span>`;
      container.appendChild(toast);

      setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
      }, 4000);
    };
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.innoBestApp = new InnoBestApp();
});

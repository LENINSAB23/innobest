/**
 * Controlador de Carga de Archivos (Fotos de Aves) para InnoBest
 * Gestiona el arrastrar y soltar (drag & drop), selección de archivo,
 * llamada a la API /api/detect/upload y dibujo de detecciones en la foto.
 */

class UploadController {
  constructor() {
    this.dropzone = document.getElementById("dropzone");
    this.fileInput = document.getElementById("file-input");
    this.btnSelect = document.getElementById("btn-select-file");
    this.previewStage = document.getElementById("preview-stage");
    this.previewImg = document.getElementById("preview-img");
    this.previewCanvas = document.getElementById("preview-canvas");
    this.previewCtx = this.previewCanvas ? this.previewCanvas.getContext("2d") : null;
    this.loadingSpinner = document.getElementById("upload-spinner");

    // Ficha de resultados de upload
    this.uploadResults = document.getElementById("upload-results-panel");
    this.uploadSpecies = document.getElementById("upload-species-title");
    this.uploadScientific = document.getElementById("upload-scientific-title");
    this.uploadBadge = document.getElementById("upload-badge-status");
    this.uploadMeterFill = document.getElementById("upload-meter-fill");
    this.uploadMeterVal = document.getElementById("upload-meter-val");
    this.uploadHabitat = document.getElementById("upload-bio-habitat");
    this.uploadThreats = document.getElementById("upload-bio-threats");
    this.uploadDbToast = document.getElementById("upload-db-toast");
    this.uploadDbRecordId = document.getElementById("upload-db-record-id");

    this.initEvents();
  }

  initEvents() {
    if (!this.dropzone || !this.fileInput) return;

    if (this.btnSelect) {
      this.btnSelect.addEventListener("click", () => this.fileInput.click());
    }

    this.dropzone.addEventListener("click", (e) => {
      if (e.target !== this.btnSelect) this.fileInput.click();
    });

    this.fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        this.processFile(e.target.files[0]);
      }
    });

    // Drag and Drop
    ["dragenter", "dragover"].forEach(name => {
      this.dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach(name => {
      this.dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.remove("dragover");
      });
    });

    this.dropzone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      if (dt.files && dt.files[0]) {
        this.processFile(dt.files[0]);
      }
    });
  }

  async processFile(file) {
    if (!file.type.startsWith("image/")) {
      window.showToast("El archivo seleccionado debe ser una imagen (JPG, PNG o WEBP).", "warning");
      return;
    }

    // Mostrar preview local inicial
    const reader = new FileReader();
    reader.onload = (e) => {
      this.previewImg.src = e.target.result;
      this.previewStage.style.display = "block";
      this.previewImg.onload = () => {
        this.previewCanvas.width = this.previewImg.naturalWidth;
        this.previewCanvas.height = this.previewImg.naturalHeight;
      };
    };
    reader.readAsDataURL(file);

    // Enviar al servidor para inferencia con YOLO
    const formData = new FormData();
    formData.append("file", file);
    formData.append("conf_threshold", "0.40");
    formData.append("save_to_db", "true");

    if (this.loadingSpinner) this.loadingSpinner.style.display = "flex";

    try {
      const res = await fetch("/api/detect/upload", {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // Dibujar cajas en la imagen
      this.renderBoxes(data.detections);

      // Mostrar ficha de la especie
      if (data.detections.length > 0) {
        this.displayResults(data.detections[0], data.saved_to_db, data.record_id);
        window.showToast(`¡Detección exitosa! Especie: ${data.detections[0].class_name}`, "success");
      } else {
        window.showToast("No se detectaron aves amenazadas en la fotografía con la confianza requerida.", "info");
      }
    } catch (err) {
      console.error("Error en upload:", err);
      window.showToast("Error al procesar la imagen en el servidor.", "warning");
    } finally {
      if (this.loadingSpinner) this.loadingSpinner.style.display = "none";
    }
  }

  renderBoxes(detections) {
    if (!this.previewCtx) return;
    this.previewCtx.clearRect(0, 0, this.previewCanvas.width, this.previewCanvas.height);

    if (!detections || detections.length === 0) return;

    detections.forEach(det => {
      const b = det.box;
      const x = b.x1;
      const y = b.y1;
      const w = b.x2 - b.x1;
      const h = b.y2 - b.y1;
      const color = det.bird_info && det.bird_info.status_color ? det.bird_info.status_color : "#10b981";

      this.previewCtx.save();
      this.previewCtx.strokeStyle = color;
      this.previewCtx.lineWidth = Math.max(4, Math.round(this.previewCanvas.width / 250));
      this.previewCtx.strokeRect(x, y, w, h);

      // Etiqueta
      const fontSize = Math.max(16, Math.round(this.previewCanvas.width / 45));
      this.previewCtx.font = `bold ${fontSize}px 'Outfit', sans-serif`;
      const label = `${det.class_name} · ${det.confidence_pct}%`;
      const textWidth = this.previewCtx.measureText(label).width;

      const tagHeight = fontSize + 12;
      this.previewCtx.fillStyle = color;
      this.previewCtx.fillRect(x, y > tagHeight ? y - tagHeight : y, textWidth + 16, tagHeight);

      this.previewCtx.fillStyle = "#ffffff";
      this.previewCtx.fillText(label, x + 8, (y > tagHeight ? y - tagHeight : y) + fontSize + 2);
      this.previewCtx.restore();
    });
  }

  displayResults(birdDetection, savedToDb, recordId) {
    const info = birdDetection.bird_info;
    if (!info) return;

    if (this.uploadResults) this.uploadResults.style.display = "flex";
    if (this.uploadSpecies) this.uploadSpecies.textContent = info.common_name;
    if (this.uploadScientific) this.uploadScientific.textContent = info.scientific_name;

    if (this.uploadBadge) {
      this.uploadBadge.textContent = info.conservation_status;
      this.uploadBadge.className = `conservation-badge badge-${(info.status_code || "vu").toLowerCase()}`;
    }

    if (this.uploadMeterFill) this.uploadMeterFill.style.width = `${birdDetection.confidence_pct}%`;
    if (this.uploadMeterVal) this.uploadMeterVal.textContent = `${birdDetection.confidence_pct}%`;

    if (this.uploadHabitat) this.uploadHabitat.textContent = info.huanuco_habitat;
    if (this.uploadThreats) this.uploadThreats.textContent = info.threats;

    if (this.uploadDbToast) {
      if (savedToDb && recordId) {
        this.uploadDbToast.style.display = "flex";
        if (this.uploadDbRecordId) this.uploadDbRecordId.textContent = `Guardado en MongoDB Atlas: ${recordId}`;
      } else {
        this.uploadDbToast.style.display = "none";
      }
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.uploadApp = new UploadController();
});

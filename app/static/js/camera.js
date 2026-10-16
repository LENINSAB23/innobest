/**
 * Controlador de Cámara Web en Tiempo Real para InnoBest
 * Gestiona el acceso al hardware de la cámara de la laptop, el streaming de video,
 * el envío de cuadros al backend de visión artificial y el dibujado de cajas sobre canvas.
 */

class CameraController {
  constructor() {
    this.video = document.getElementById("webcam");
    this.canvas = document.getElementById("canvas-overlay");
    this.ctx = this.canvas ? this.canvas.getContext("2d") : null;
    this.startBtn = document.getElementById("btn-start-camera");
    this.stopBtn = document.getElementById("btn-stop-camera");
    this.snapshotBtn = document.getElementById("btn-snapshot");
    this.placeholder = document.getElementById("camera-placeholder");
    this.saveMongoCheckbox = document.getElementById("chk-save-mongo");
    this.confSlider = document.getElementById("slider-conf");
    this.confValueSpan = document.getElementById("conf-val");
    this.cameraSelect = document.getElementById("camera-select");

    // Diagnóstico lateral
    this.resultBanner = document.getElementById("live-result-banner");
    this.speciesTitle = document.getElementById("live-species-title");
    this.scientificTitle = document.getElementById("live-scientific-title");
    this.badgeStatus = document.getElementById("live-badge-status");
    this.meterFill = document.getElementById("live-meter-fill");
    this.meterVal = document.getElementById("live-meter-val");
    this.bioHabitat = document.getElementById("live-bio-habitat");
    this.bioThreats = document.getElementById("live-bio-threats");
    this.dbToast = document.getElementById("live-db-toast");
    this.dbRecordId = document.getElementById("live-db-record-id");

    this.stream = null;
    this.isStreaming = false;
    this.isProcessingFrame = false;
    this.loopInterval = null;
    this.offscreenCanvas = document.createElement("canvas");
    this.offscreenCtx = this.offscreenCanvas.getContext("2d");

    this.initEvents();
  }

  initEvents() {
    if (this.startBtn) this.startBtn.addEventListener("click", () => this.startCamera());
    if (this.stopBtn) this.stopBtn.addEventListener("click", () => this.stopCamera());
    if (this.snapshotBtn) this.snapshotBtn.addEventListener("click", () => this.captureSingleFrame());
    if (this.confSlider && this.confValueSpan) {
      this.confSlider.addEventListener("input", (e) => {
        this.confValueSpan.textContent = `${Math.round(e.target.value * 100)}%`;
      });
    }

    // Listar cámaras disponibles en la laptop
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
      this.populateCameraDevices();
    }
  }

  async populateCameraDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(d => d.kind === "videoinput");
      if (this.cameraSelect && videoDevices.length > 0) {
        this.cameraSelect.innerHTML = "";
        videoDevices.forEach((dev, idx) => {
          const opt = document.createElement("option");
          opt.value = dev.deviceId;
          opt.textContent = dev.label || `Cámara ${idx + 1}`;
          this.cameraSelect.appendChild(opt);
        });
      }
    } catch (e) {
      console.warn("No se pudieron enumerar dispositivos de video:", e);
    }
  }

  async startCamera() {
    if (this.isStreaming) return;

    try {
      const deviceId = this.cameraSelect && this.cameraSelect.value ? { exact: this.cameraSelect.value } : undefined;
      const constraints = {
        video: {
          deviceId: deviceId,
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user"
        },
        audio: false
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.stream;
      await this.video.play();

      this.isStreaming = true;
      if (this.placeholder) this.placeholder.style.display = "none";
      if (this.startBtn) this.startBtn.style.display = "none";
      if (this.stopBtn) this.stopBtn.style.display = "inline-flex";
      if (this.snapshotBtn) this.snapshotBtn.style.display = "inline-flex";

      // Ajustar resolución del canvas al video real
      this.video.addEventListener("loadedmetadata", () => {
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        this.offscreenCanvas.width = this.video.videoWidth;
        this.offscreenCanvas.height = this.video.videoHeight;
      });

      // Bucle de inferencia continua (cada 1000 ms = 1 segundo para envío continuo a MongoDB Atlas)
      this.loopInterval = setInterval(() => this.processLiveFrame(), 1000);

      window.showToast("Cámara activada: Transmitiendo cada 1s a MongoDB Atlas...", "success");
    } catch (err) {
      console.error("Error al encender cámara:", err);
      let msg = "No se pudo acceder a la cámara de la laptop. Verifica los permisos del navegador.";
      if (err.name === "NotAllowedError") {
        msg = "Permiso de cámara denegado. Permite el acceso a la cámara en el navegador.";
      } else if (err.name === "NotFoundError") {
        msg = "No se encontró ninguna cámara conectada en tu equipo.";
      }
      window.showToast(msg, "warning");
    }
  }

  stopCamera() {
    if (!this.isStreaming) return;

    if (this.loopInterval) {
      clearInterval(this.loopInterval);
      this.loopInterval = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    this.video.srcObject = null;
    this.isStreaming = false;

    // Limpiar canvas
    if (this.ctx) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    if (this.placeholder) this.placeholder.style.display = "flex";
    if (this.startBtn) this.startBtn.style.display = "inline-flex";
    if (this.stopBtn) this.stopBtn.style.display = "none";
    if (this.snapshotBtn) this.snapshotBtn.style.display = "none";

    this.resetDetectionCard();
    window.showToast("Cámara detenida.", "info");
  }

  async processLiveFrame() {
    if (!this.isStreaming || this.isProcessingFrame) return;
    if (this.video.videoWidth === 0 || this.video.videoHeight === 0) return;

    this.isProcessingFrame = true;

    try {
      // Capturar cuadro actual en offscreen canvas
      this.offscreenCtx.drawImage(this.video, 0, 0, this.offscreenCanvas.width, this.offscreenCanvas.height);
      const frameBase64 = this.offscreenCanvas.toDataURL("image/jpeg", 0.75);

      const conf = this.confSlider ? parseFloat(this.confSlider.value) : 0.45;
      const saveDb = this.saveMongoCheckbox ? this.saveMongoCheckbox.checked : true;

      const response = await fetch("/api/detect/webcam", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_base64: frameBase64,
          conf_threshold: conf,
          save_to_db: saveDb
        })
      });

      if (response.ok) {
        const data = await response.json();
        this.renderDetections(data.detections);
        if (data.detections && data.detections.length > 0) {
          this.updateDetectionCard(data.detections[0], data.saved_to_db, data.record_id);
        } else {
          this.resetDetectionCard();
        }
      }
    } catch (e) {
      console.error("Error procesando cuadro de video:", e);
    } finally {
      this.isProcessingFrame = false;
    }
  }

  async captureSingleFrame() {
    if (!this.isStreaming) return;
    await this.processLiveFrame();
    window.showToast("Foto de cámara analizada y registrada en MongoDB", "success");
  }

  renderDetections(detections) {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    if (!detections || detections.length === 0) return;

    detections.forEach(det => {
      const b = det.box;
      const x = b.x1;
      const y = b.y1;
      const w = b.x2 - b.x1;
      const h = b.y2 - b.y1;

      // Asignar colores vibrantes idénticos al estilo YOLO de la imagen de referencia (Imagen 2)
      let color = "#eab308"; // Amarillo oro (estilo 'PERSON' de la imagen de referencia)
      let textColor = "#000000";

      const nameLower = (det.raw_class || det.class_name || "").toLowerCase();
      if (nameLower.includes("paujil")) {
        color = "#e11d48"; // Rojo intenso (estilo 'OBJECT' de la imagen de referencia)
        textColor = "#ffffff";
      } else if (nameLower.includes("matorralero") || nameLower.includes("matorrelero")) {
        color = "#eab308"; // Amarillo vivo
        textColor = "#000000";
      } else if (nameLower.includes("trompetero")) {
        color = "#0284c7"; // Azul cielo / cian
        textColor = "#ffffff";
      }

      this.ctx.save();

      // 1. Dibujar Bounding Box rectangular nítido con línea sólida gruesa de 4px (sin sombras difusas)
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 4;
      this.ctx.lineJoin = "miter";
      this.ctx.strokeRect(x, y, w, h);

      // 2. Etiqueta superior tipo banner rectangular sólido (como en la Imagen de referencia 2)
      const label = `${(det.class_name || "AVE").toUpperCase()}  ${det.confidence_pct}%`;
      this.ctx.font = "bold 15px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
      const textMetrics = this.ctx.measureText(label);
      const tagWidth = textMetrics.width + 16;
      const tagHeight = 26;

      // Colocar el banner arriba del marco o en el borde superior interior si se sale de la pantalla
      const tagY = y >= tagHeight ? y - tagHeight : y;

      // Banner de color sólido
      this.ctx.fillStyle = color;
      this.ctx.fillRect(x, tagY, tagWidth, tagHeight);

      // Texto en contraste alto
      this.ctx.fillStyle = textColor;
      this.ctx.fillText(label, x + 8, tagY + 18);

      this.ctx.restore();
    });
  }

  updateDetectionCard(birdDetection, savedToDb, recordId) {
    const info = birdDetection.bird_info;
    if (!info) return;

    if (this.resultBanner) this.resultBanner.classList.add("detected");
    if (this.speciesTitle) this.speciesTitle.textContent = info.common_name;
    if (this.scientificTitle) this.scientificTitle.textContent = info.scientific_name;

    if (this.badgeStatus) {
      this.badgeStatus.textContent = info.conservation_status;
      this.badgeStatus.className = `conservation-badge badge-${(info.status_code || "vu").toLowerCase()}`;
    }

    if (this.meterFill) this.meterFill.style.width = `${birdDetection.confidence_pct}%`;
    if (this.meterVal) this.meterVal.textContent = `${birdDetection.confidence_pct}%`;

    if (this.bioHabitat) this.bioHabitat.textContent = info.huanuco_habitat;
    if (this.bioThreats) this.bioThreats.textContent = info.threats;

    if (this.dbToast) {
      if (savedToDb && recordId) {
        this.dbToast.style.display = "flex";
        if (this.dbRecordId) this.dbRecordId.textContent = `ID MongoDB: ${recordId.substring(0, 10)}...`;
      } else {
        this.dbToast.style.display = "none";
      }
    }
  }

  resetDetectionCard() {
    if (this.resultBanner) this.resultBanner.classList.remove("detected");
    if (this.speciesTitle) this.speciesTitle.textContent = "Buscando Aves en Huánuco...";
    if (this.scientificTitle) this.scientificTitle.textContent = "Apunta la cámara hacia el espécimen";
    if (this.badgeStatus) {
      this.badgeStatus.textContent = "Escaneando...";
      this.badgeStatus.className = "conservation-badge badge-none";
    }
    if (this.meterFill) this.meterFill.style.width = "0%";
    if (this.meterVal) this.meterVal.textContent = "0%";
    if (this.bioHabitat) this.bioHabitat.textContent = "Las áreas de observación incluyen Carpish, Tingo María y cuenca del Huallaga.";
    if (this.bioThreats) this.bioThreats.textContent = "En espera de detección para desplegar informe biológico...";
    if (this.dbToast) this.dbToast.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.cameraApp = new CameraController();
});

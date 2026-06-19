(function () {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function initParticles() {
    const canvas = document.getElementById("particleCanvas");
    if (!canvas || prefersReducedMotion) {
      return;
    }

    const context = canvas.getContext("2d");
    const particles = Array.from({ length: 46 }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.00055,
      vy: (Math.random() - 0.5) * 0.00055,
    }));

    function resize() {
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.floor(rect.width * window.devicePixelRatio);
      canvas.height = Math.floor(rect.height * window.devicePixelRatio);
      context.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    }

    function draw() {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      context.clearRect(0, 0, width, height);

      particles.forEach((particle) => {
        particle.x += particle.vx;
        particle.y += particle.vy;

        if (particle.x < 0 || particle.x > 1) {
          particle.vx *= -1;
        }

        if (particle.y < 0 || particle.y > 1) {
          particle.vy *= -1;
        }
      });

      particles.forEach((particle, index) => {
        const x = particle.x * width;
        const y = particle.y * height;

        context.beginPath();
        context.arc(x, y, 1.8, 0, Math.PI * 2);
        context.fillStyle = "rgba(147, 197, 253, 0.72)";
        context.fill();

        for (let nextIndex = index + 1; nextIndex < particles.length; nextIndex += 1) {
          const next = particles[nextIndex];
          const dx = x - next.x * width;
          const dy = y - next.y * height;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 130) {
            context.strokeStyle = `rgba(59, 130, 246, ${0.22 * (1 - distance / 130)})`;
            context.lineWidth = 1;
            context.beginPath();
            context.moveTo(x, y);
            context.lineTo(next.x * width, next.y * height);
            context.stroke();
          }
        }
      });

      requestAnimationFrame(draw);
    }

    resize();
    window.addEventListener("resize", resize);
    draw();
  }

  function initUploadExperience() {
    const form = document.getElementById("uploadForm");
    const input = document.getElementById("videoInput");
    const label = document.getElementById("fileLabel");
    const dropZone = document.getElementById("dropZone");
    const stateLabel = document.getElementById("uploadStateLabel");
    const percentLabel = document.getElementById("uploadPercent");
    const progressBar = document.getElementById("uploadProgressBar");
    const processingPill = document.getElementById("processingPill");
    const processingFile = document.getElementById("processingFile");
    const processingProgress = document.getElementById("processingProgress");
    const framesProcessed = document.getElementById("framesProcessed");
    const currentFps = document.getElementById("currentFps");
    const etaValue = document.getElementById("etaValue");
    const runButton = document.getElementById("runButton");

    const MAX_FILE_SIZE = 100 * 1024 * 1024; /* 100 MB */

    if (!form || !input || !dropZone) {
      return;
    }

    function showAlert(message) {
      let alertEl = form.querySelector(".alert");
      if (!alertEl) {
        alertEl = document.createElement("div");
        alertEl.className = "alert alert-danger";
        alertEl.setAttribute("role", "alert");
        form.insertAdjacentElement("afterbegin", alertEl);
      }
      alertEl.innerHTML = '<i class="bi bi-exclamation-triangle"></i> ' + message;
    }

    function clearAlert() {
      const alertEl = form.querySelector(".alert");
      if (alertEl) {
        alertEl.remove();
      }
    }

    function validateFileSize(file) {
      if (!file) return true;
      if (file.size > MAX_FILE_SIZE) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
        showAlert("File is too large (" + sizeMB + " MB). Maximum upload size is 100 MB.");
        input.value = "";
        label.textContent = "Drop surveillance, traffic, crowd, or sports footage";
        processingFile.textContent = "No video selected";
        if (runButton) runButton.disabled = true;
        return false;
      }
      clearAlert();
      if (runButton) runButton.disabled = false;
      return true;
    }

    function setProgress(value, state) {
      const safeValue = Math.max(0, Math.min(100, value));
      progressBar.style.width = `${safeValue}%`;
      percentLabel.textContent = `${Math.round(safeValue)}%`;
      stateLabel.textContent = state;
      dropZone.dataset.state = state.toLowerCase();
    }

    function setFile(file) {
      if (!file) {
        label.textContent = "Drop surveillance, traffic, crowd, or sports footage";
        processingFile.textContent = "No video selected";
        return;
      }

      label.textContent = file.name;
      processingFile.textContent = file.name;
      processingProgress.textContent = "Ready for tracking";
      processingPill.textContent = "Ready";
    }

    input.addEventListener("change", () => {
      if (validateFileSize(input.files[0])) {
        setFile(input.files[0]);
      }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("is-dragging");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("is-dragging");
      });
    });

    dropZone.addEventListener("drop", (event) => {
      input.files = event.dataTransfer.files;
      if (validateFileSize(input.files[0])) {
        setFile(input.files[0]);
      }
    });

    form.addEventListener("submit", (event) => {
      event.preventDefault();

      if (!input.files || !input.files[0]) {
        return;
      }

      if (!validateFileSize(input.files[0])) {
        return;
      }

      const filename = input.files[0].name;
      const formData = new FormData(form);
      const xhr = new XMLHttpRequest();

      if (runButton) {
        runButton.disabled = true;
        runButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing…';
      }

      processingFile.textContent = filename;
      processingPill.textContent = "Uploading";
      processingPill.classList.remove("success");
      processingProgress.textContent = "Uploading video to server";
      setProgress(0, "Uploading");

      /* ── Phase 1: real upload progress ── */
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const pct = (e.loaded / e.total) * 100;
          setProgress(pct, "Uploading");
          processingProgress.textContent = "Uploading video to server";

          const uploadedMB = (e.loaded / (1024 * 1024)).toFixed(1);
          const totalMB = (e.total / (1024 * 1024)).toFixed(1);
          framesProcessed.textContent = `${uploadedMB} / ${totalMB} MB`;
          currentFps.textContent = "--";
          etaValue.textContent = pct < 95 ? "Uploading…" : "Almost done";
        }
      });

      /* ── Phase 2: processing animation while server works ── */
      xhr.upload.addEventListener("load", () => {
        setProgress(100, "Uploaded");
        processingPill.textContent = "Processing";
        processingProgress.textContent = "Running YOLOv8 + ByteTrack inference — this may take a few minutes";
        framesProcessed.textContent = "—";
        currentFps.textContent = "--";
        etaValue.textContent = "Estimating…";

        let processingPct = 0;
        const startTime = Date.now();

        const processingTimer = window.setInterval(() => {
          /* slowly creep toward 95% — use /180 to slow down the curve */
          const elapsed = (Date.now() - startTime) / 1000;
          processingPct = 95 * (1 - Math.exp(-elapsed / 180));

          setProgress(processingPct, "Processing");

          /* show elapsed time */
          const minutes = Math.floor(elapsed / 60);
          const seconds = Math.floor(elapsed % 60);
          etaValue.textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")} elapsed`;

          /* show helpful status messages based on elapsed time */
          if (elapsed < 30) {
            processingProgress.textContent = "Running YOLOv8 + ByteTrack inference…";
          } else if (elapsed < 120) {
            processingProgress.textContent = "Still processing — free tier CPU is slow, please wait…";
          } else if (elapsed < 300) {
            processingProgress.textContent = "Processing large video — hang tight, almost there…";
          } else {
            processingProgress.textContent = "Still working… this video is taking a while on free tier";
          }

          framesProcessed.textContent = "—";
          currentFps.textContent = "--";
        }, 1000);

        /* store timer ID so we can clear it on response */
        xhr._processingTimer = processingTimer;
      });

      /* ── Phase 3: server responded ── */
      xhr.addEventListener("load", () => {
        if (xhr._processingTimer) {
          window.clearInterval(xhr._processingTimer);
        }

        /* server returns a 302 redirect → follow it */
        if (xhr.status >= 200 && xhr.status < 400) {
          setProgress(100, "Complete");
          processingPill.textContent = "Complete";
          processingPill.classList.add("success");
          processingProgress.textContent = "Tracking complete — loading results";
          etaValue.textContent = "Done";

          /* the /upload route returns a redirect; responseURL follows it */
          const redirectUrl = xhr.responseURL;
          if (redirectUrl && redirectUrl !== window.location.href) {
            window.location.href = redirectUrl;
          } else {
            /* fallback: reload to pick up any rendered error */
            window.location.reload();
          }
        } else {
          /* server returned an error page */
          setProgress(0, "Error");
          processingPill.textContent = "Error";
          etaValue.textContent = "--";
          if (runButton) {
            runButton.disabled = false;
            runButton.innerHTML = '<i class="bi bi-cpu"></i> Run Occlusion-Aware Tracking';
          }

          /* extract actual error — try JSON first, then HTML */
          let errorMsg = "Processing failed (HTTP " + xhr.status + ")";
          try {
            const json = JSON.parse(xhr.responseText);
            if (json.error) errorMsg = json.error;
          } catch (_) {
            /* not JSON — try parsing HTML */
            const parser = new DOMParser();
            const doc = parser.parseFromString(xhr.responseText, "text/html");
            const alertEl = doc.querySelector(".alert");
            if (alertEl) {
              errorMsg = alertEl.textContent.trim();
              const existingAlert = form.querySelector(".alert");
              if (existingAlert) {
                existingAlert.innerHTML = alertEl.innerHTML;
              } else {
                form.insertAdjacentHTML("afterbegin", alertEl.outerHTML);
              }
            }
          }
          /* show error in processing card so user always sees it */
          processingProgress.textContent = errorMsg;
          showAlert(errorMsg);
        }
      });

      xhr.addEventListener("error", () => {
        if (xhr._processingTimer) {
          window.clearInterval(xhr._processingTimer);
        }
        setProgress(0, "Error");
        processingPill.textContent = "Error";
        processingProgress.textContent = "Server crashed or timed out — try a shorter video";
        etaValue.textContent = "--";
        if (runButton) {
          runButton.disabled = false;
          runButton.innerHTML = '<i class="bi bi-cpu"></i> Run Occlusion-Aware Tracking';
        }
        showAlert("Server crashed or timed out. On Render free tier, try a video under 10 seconds.");
      });

      xhr.addEventListener("abort", () => {
        if (xhr._processingTimer) {
          window.clearInterval(xhr._processingTimer);
        }
        setProgress(0, "Aborted");
        processingPill.textContent = "Idle";
        processingProgress.textContent = "Upload cancelled";
        etaValue.textContent = "--";
        if (runButton) {
          runButton.disabled = false;
          runButton.innerHTML = '<i class="bi bi-cpu"></i> Run Occlusion-Aware Tracking';
        }
      });

      xhr.open("POST", form.action);
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
      xhr.send(formData);
    });
  }

  function chartDefaults() {
    if (!window.Chart) {
      return;
    }

    Chart.defaults.color = "#9ca3af";
    Chart.defaults.borderColor = "rgba(148, 163, 184, 0.14)";
    Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  }

  function initCharts() {
    if (!window.Chart || document.body.dataset.page !== "result") {
      return;
    }

    chartDefaults();

    const lineOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#111827",
          borderColor: "rgba(148, 163, 184, 0.22)",
          borderWidth: 1,
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true },
      },
    };

    const objectCount = document.getElementById("objectCountChart");
    const trackStability = document.getElementById("trackStabilityChart");
    const motion = document.getElementById("motionChart");
    const density = document.getElementById("densityChart");

    if (objectCount) {
      new Chart(objectCount, {
        type: "line",
        data: {
          labels: ["00:00", "00:15", "00:30", "00:45", "01:00", "01:15", "01:30"],
          datasets: [{
            data: [18, 24, 31, 29, 38, 42, 36],
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59, 130, 246, 0.14)",
            fill: true,
            tension: 0.38,
          }],
        },
        options: lineOptions,
      });
    }

    if (trackStability) {
      new Chart(trackStability, {
        type: "bar",
        data: {
          labels: ["People", "Vehicles", "Objects", "Recovered"],
          datasets: [{
            data: [93, 97, 88, 96],
            backgroundColor: ["#3b82f6", "#8b5cf6", "#10b981", "#60a5fa"],
            borderRadius: 6,
          }],
        },
        options: lineOptions,
      });
    }

    if (motion) {
      new Chart(motion, {
        type: "doughnut",
        data: {
          labels: ["Slow", "Moderate", "Fast", "Stationary"],
          datasets: [{
            data: [32, 44, 18, 6],
            backgroundColor: ["#10b981", "#3b82f6", "#8b5cf6", "#475569"],
            borderWidth: 0,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom", labels: { boxWidth: 10, boxHeight: 10 } },
          },
        },
      });
    }

    if (density) {
      new Chart(density, {
        type: "radar",
        data: {
          labels: ["North", "East", "South", "West", "Center"],
          datasets: [{
            data: [41, 28, 36, 22, 54],
            borderColor: "#8b5cf6",
            backgroundColor: "rgba(139, 92, 246, 0.18)",
            pointBackgroundColor: "#f9fafb",
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            r: {
              angleLines: { color: "rgba(148, 163, 184, 0.14)" },
              grid: { color: "rgba(148, 163, 184, 0.14)" },
              pointLabels: { color: "#9ca3af" },
              ticks: { display: false },
            },
          },
        },
      });
    }
  }

  function initAnalyticsDownload() {
    const button = document.getElementById("downloadAnalytics");
    if (!button) {
      return;
    }

    button.addEventListener("click", () => {
      const analytics = window.trackVisionAnalytics || {};
      const blob = new Blob([JSON.stringify(analytics, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "trackvision-analytics.json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    });
  }

  initParticles();
  initUploadExperience();
  initCharts();
  initAnalyticsDownload();
})();

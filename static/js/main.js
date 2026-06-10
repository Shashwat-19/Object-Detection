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

    if (!form || !input || !dropZone) {
      return;
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

    input.addEventListener("change", () => setFile(input.files[0]));

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
      setFile(input.files[0]);
    });

    form.addEventListener("submit", () => {
      const filename = input.files[0] ? input.files[0].name : "Selected video";
      let progress = 0;
      let frames = 0;

      processingFile.textContent = filename;
      processingPill.textContent = "Processing";
      processingProgress.textContent = "Uploading video";
      setProgress(8, "Uploading");

      const timer = window.setInterval(() => {
        progress = progress < 72 ? progress + Math.random() * 8 : Math.min(94, progress + Math.random() * 1.2);
        frames += Math.floor(24 + Math.random() * 38);

        const state = progress < 35 ? "Uploading" : "Processing";
        setProgress(progress, state);
        processingProgress.textContent = progress < 35 ? "Securing upload" : "Running YOLOv8 + ByteTrack";
        framesProcessed.textContent = frames.toLocaleString();
        currentFps.textContent = `${(27 + Math.random() * 8).toFixed(1)}`;
        etaValue.textContent = progress < 80 ? "Under 1 min" : "Finalizing";
      }, 700);

      window.setTimeout(() => {
        window.clearInterval(timer);
        setProgress(96, "Processing");
        processingProgress.textContent = "Rendering tracked output";
      }, 9000);
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

/* Voice ordering flow: record -> transcribe (Gemini via server) -> extract -> confirm -> submit. */
(function () {
  "use strict";

  const root = document.getElementById("voice-app");
  if (!root) return;
  const App = window.App;

  const aiConfigured = root.dataset.geminiConfigured === "true";
  const maxAudioBytes = parseInt(root.dataset.maxAudioBytes || "8388608", 10);
  const requiredFields = (root.dataset.requiredFields || "").split(",").filter(Boolean);

  const ui = {
    micButton: document.getElementById("mic-button"),
    micLabel: document.getElementById("mic-label"),
    statusText: document.getElementById("mic-status-text"),
    timer: document.getElementById("recording-timer"),
    waveform: document.getElementById("waveform"),
    language: document.getElementById("language-select"),
    transcript: document.getElementById("transcript-input"),
    transcriptSource: document.getElementById("transcript-source"),
    extractBtn: document.getElementById("btn-extract"),
    clearBtn: document.getElementById("btn-clear"),
    extractFeedback: document.getElementById("extract-feedback"),
    reviewState: document.getElementById("review-state"),
    flagRegion: document.getElementById("flag-region"),
    form: document.getElementById("order-form"),
    submitFeedback: document.getElementById("submit-feedback"),
    submitBtn: document.getElementById("btn-submit"),
    resultCard: document.getElementById("result-card"),
    resultCode: document.getElementById("result-code"),
    resultMessage: document.getElementById("result-message"),
    resultTrackLink: document.getElementById("result-track-link"),
    newRequestBtn: document.getElementById("btn-new-request"),
    playback: document.getElementById("audio-playback"),
    reviewSection: document.getElementById("review-section"),
    dateTextField: document.getElementById("date-text-field"),
    quickTypeButtons: document.querySelectorAll("[data-quick-user-type]"),
  };

  let mediaRecorder = null;
  let stream = null;
  let chunks = [];
  let recorderMime = "audio/webm";
  let audioContext = null;
  let analyser = null;
  let animationFrame = null;
  let timerHandle = null;
  let startedAt = 0;
  let recognition = null;
  let recognitionActive = false;
  let busy = false;
  let submitAttemptId = null;
  let lastExtraction = null;

  const LANGUAGE_TAGS = { ne: "ne-NP", en: "en-US", "ne-roman": "ne-NP", mixed: "ne-NP", unknown: "" };

  /* ------------------------------ helpers ------------------------------ */
  function setStatus(text, tone) {
    ui.statusText.textContent = text;
    ui.statusText.className = tone === "error" ? "flash flash-error small" : "muted";
  }

  function setBusy(state, label) {
    busy = state;
    ui.micButton.classList.toggle("busy", state && !mediaRecorder);
    ui.micButton.disabled = state;
    if (label) ui.micLabel.innerHTML = label;
  }

  function resetMicUi() {
    ui.micButton.classList.remove("recording", "busy");
    ui.micButton.disabled = false;
    ui.micButton.setAttribute("aria-pressed", "false");
    ui.micLabel.innerHTML = 'थिच्नुहोस् र बोल्नुहोस्<small>Tap to speak</small>';
    ui.timer.hidden = true;
  }

  function fieldWrap(name) {
    const input = ui.form ? ui.form.querySelector('[name="' + name + '"]') : null;
    return input ? input.closest(".field") : null;
  }

  function fieldLabel(name) {
    const wrap = fieldWrap(name);
    if (!wrap) return name.replace(/_/g, " ");
    const label = wrap.querySelector(".field-label");
    return label ? label.textContent.replace("*", "").trim() : name;
  }

  function markField(name, state) {
    const wrap = fieldWrap(name);
    if (!wrap) return;
    wrap.classList.toggle("ai-filled", state === "ai");
    wrap.classList.toggle("needs-attention", state === "attention");
    let tag = wrap.querySelector(".ai-tag");
    if (state && !tag) {
      tag = document.createElement("span");
      tag.className = "ai-tag";
      wrap.querySelector(".field-label").appendChild(tag);
    }
    if (tag) {
      tag.textContent = state === "ai" ? "AI" : state === "attention" ? "check" : "";
      if (!state) tag.remove();
    }
  }

  function clearMarks() {
    if (!ui.form) return;
    ui.form.querySelectorAll(".field").forEach(function (wrap) {
      wrap.classList.remove("ai-filled", "needs-attention");
      const tag = wrap.querySelector(".ai-tag");
      if (tag) tag.remove();
    });
  }

  function showFeedback(container, message, type, details) {
    if (!container) return;
    container.hidden = false;
    container.innerHTML = "";
    const box = document.createElement("div");
    box.className = "flash flash-" + (type || "error");
    const p = document.createElement("p");
    p.textContent = message;
    box.appendChild(p);
    if (details && details.length) {
      const ul = document.createElement("ul");
      details.forEach(function (item) {
        const li = document.createElement("li");
        li.textContent = (item.field ? fieldLabel(item.field) + ": " : "") + (item.message || item.code || "invalid");
        ul.appendChild(li);
      });
      box.appendChild(ul);
    }
    container.appendChild(box);
  }

  function hideFeedback(container) {
    if (container) {
      container.hidden = true;
      container.innerHTML = "";
    }
  }

  function setReviewState(text, tone) {
    ui.reviewState.textContent = text;
    ui.reviewState.className = "badge badge-" + (tone || "muted");
  }

  /* --------------------------- audio recording -------------------------- */
  function pickMimeType() {
    const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
    if (!window.MediaRecorder || !window.MediaRecorder.isTypeSupported) return "";
    for (let i = 0; i < candidates.length; i += 1) {
      if (window.MediaRecorder.isTypeSupported(candidates[i])) return candidates[i];
    }
    return "";
  }

  function startTimer() {
    startedAt = Date.now();
    ui.timer.hidden = false;
    ui.timer.textContent = "00:00";
    timerHandle = window.setInterval(function () {
      const seconds = Math.floor((Date.now() - startedAt) / 1000);
      const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
      const ss = String(seconds % 60).padStart(2, "0");
      ui.timer.textContent = mm + ":" + ss;
      if (seconds >= 60) stopRecording(); // keep recordings short and cheap
    }, 250);
  }

  function stopTimer() {
    if (timerHandle) window.clearInterval(timerHandle);
    timerHandle = null;
  }

  function startWaveform(micStream) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx || !ui.waveform) return;
    audioContext = new Ctx();
    const source = audioContext.createMediaStreamSource(micStream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);
    const ctx = ui.waveform.getContext("2d");
    const data = new Uint8Array(analyser.frequencyBinCount);

    function draw() {
      animationFrame = window.requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(data);
      ctx.clearRect(0, 0, ui.waveform.width, ui.waveform.height);
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = "#15803d";
      ctx.beginPath();
      const step = ui.waveform.width / data.length;
      for (let i = 0; i < data.length; i += 1) {
        const y = (data[i] / 128.0) * (ui.waveform.height / 2);
        if (i === 0) ctx.moveTo(0, y);
        else ctx.lineTo(i * step, y);
      }
      ctx.stroke();
    }
    draw();
  }

  function stopWaveform() {
    if (animationFrame) window.cancelAnimationFrame(animationFrame);
    animationFrame = null;
    if (audioContext) audioContext.close().catch(function () {});
    audioContext = null;
    analyser = null;
    if (ui.waveform) {
      const ctx = ui.waveform.getContext("2d");
      ctx.clearRect(0, 0, ui.waveform.width, ui.waveform.height);
    }
  }

  function startSpeechPreview() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      ui.transcriptSource.textContent = "server transcription only";
      return;
    }
    try {
      recognition = new Recognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      const tag = LANGUAGE_TAGS[ui.language.value] || navigator.language || "en-US";
      if (tag) recognition.lang = tag;
      let previewText = "";
      recognition.onresult = function (event) {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const result = event.results[i];
          if (result.isFinal) previewText += result[0].transcript;
          else interim += result[0].transcript;
        }
        if (!ui.transcript.value.trim() || ui.transcriptSource.textContent.indexOf("browser") === 0) {
          ui.transcript.value = (previewText + " " + interim).trim();
          ui.transcriptSource.textContent = "browser live preview (will be replaced by Gemini)";
          ui.extractBtn.disabled = !ui.transcript.value.trim();
        }
      };
      recognition.onerror = function () { recognitionActive = false; };
      recognition.onend = function () { recognitionActive = false; };
      recognition.start();
      recognitionActive = true;
    } catch (error) {
      recognition = null;
    }
  }

  function stopSpeechPreview() {
    if (recognition && recognitionActive) {
      try {
        recognition.stop();
      } catch (error) {
        /* already stopped */
      }
    }
    recognitionActive = false;
  }

  async function startRecording() {
    if (busy) return;
    if (!aiConfigured) {
      App.toast(
        "AI सहायक निष्क्रिय छ — कृपया टाइप गर्नुहोस्। AI assistant is offline; please type the order below.",
        "warning",
        8000
      );
      ui.transcript.focus();
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
      App.toast("This browser cannot record audio. Please use Chrome, Edge, Firefox or Safari.", "error", 8000);
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      const name = error && error.name;
      if (name === "NotAllowedError" || name === "SecurityError") {
        App.toast("Microphone permission was blocked. Allow it in the address bar and try again.", "error", 9000);
        setStatus("Microphone permission denied — you can still type your order below.", "error");
      } else if (name === "NotFoundError") {
        App.toast("No microphone was found on this device.", "error");
      } else {
        App.toast("Could not start the microphone: " + (error.message || name), "error");
      }
      return;
    }

    recorderMime = pickMimeType();
    chunks = [];
    try {
      mediaRecorder = recorderMime
        ? new window.MediaRecorder(stream, { mimeType: recorderMime })
        : new window.MediaRecorder(stream);
    } catch (error) {
      App.toast("This browser cannot record in a supported audio format.", "error");
      stopStream();
      return;
    }

    mediaRecorder.ondataavailable = function (event) {
      if (event.data && event.data.size > 0) chunks.push(event.data);
    };
    mediaRecorder.onstop = handleRecordingStopped;
    mediaRecorder.start();

    ui.micButton.classList.add("recording");
    ui.micButton.setAttribute("aria-pressed", "true");
    ui.micLabel.innerHTML = 'रोक्न थिच्नुहोस्<small>Tap to stop</small>';
    setStatus("सुन्दैछ… Listening. Speak naturally in Nepali or English.");
    startTimer();
    startWaveform(stream);
    startSpeechPreview();
  }

  function stopStream() {
    if (stream) {
      stream.getTracks().forEach(function (track) { track.stop(); });
      stream = null;
    }
  }

  function stopRecording() {
    stopTimer();
    stopSpeechPreview();
    stopWaveform();
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
      return;
    }
    resetMicUi();
  }

  async function handleRecordingStopped() {
    stopStream();
    resetMicUi();
    const mime = recorderMime || "audio/webm";
    const blob = new Blob(chunks, { type: mime });
    chunks = [];
    mediaRecorder = null;

    if (!blob.size) {
      setStatus("No audio was captured. Please try again.", "error");
      return;
    }
    if (blob.size > maxAudioBytes) {
      setStatus("That recording is too long. Please keep it under a minute.", "error");
      return;
    }
    if (ui.playback) {
      ui.playback.hidden = false;
      ui.playback.src = URL.createObjectURL(blob);
    }

    const seconds = ((Date.now() - startedAt) / 1000).toFixed(1);
    await transcribe(blob, mime, seconds);
  }

  async function transcribe(blob, mime, seconds) {
    setBusy(true, 'ट्रान्सक्राइब हुँदैछ…<small>Transcribing</small>');
    setStatus("Sending " + seconds + "s of audio to the server for transcription…");
    const formData = new FormData();
    formData.append("audio", blob, "order-audio.webm");
    formData.append("mime_type", mime);
    formData.append("language", ui.language.value);
    try {
      const response = await App.request("/api/voice/transcribe", { method: "POST", body: formData });
      ui.transcript.value = response.transcript || "";
      ui.transcriptSource.textContent = "Gemini " + (response.model || "") + (response.language ? " · " + response.language : "");
      ui.extractBtn.disabled = !ui.transcript.value.trim();
      setStatus("Transcribed. Extracting the order details…");
      if (response.notes) App.toast(response.notes, "info", 6000);
      await extractDetails();
      setStatus("Review the details below and submit when correct.");
    } catch (error) {
      if (error.code === "gemini_not_configured") {
        setStatus("AI is not configured on the server — type the order below.", "error");
        App.toast(error.message, "warning", 10000);
      } else {
        setStatus("Transcription failed: " + error.message, "error");
        App.toast(error.message, "error", 8000);
        showFeedback(ui.extractFeedback, "Transcription failed: " + error.message, "error", error.details);
      }
    } finally {
      setBusy(false);
      resetMicUi();
    }
  }

  /* ------------------------------ extraction ---------------------------- */
  async function extractDetails() {
    const text = ui.transcript.value.trim();
    if (!text) {
      App.toast("रेकर्ड गर्नुहोस् वा टाइप गर्नुहोस्। Record or type your order first.", "warning");
      return;
    }
    hideFeedback(ui.extractFeedback);
    ui.extractBtn.disabled = true;
    const originalLabel = ui.extractBtn.textContent;
    ui.extractBtn.textContent = "✨ Extracting…";
    try {
      const response = await App.request("/api/orders/parse", {
        method: "POST",
        body: { text: text, language: ui.language.value },
      });
      lastExtraction = response.extracted;
      fillForm(response.extracted);
      renderFlags(response.missing_fields || [], response.ambiguities || []);
      const confidence = response.extracted.confidence;
      setReviewState(
        "AI extraction" + (confidence != null ? " · " + Math.round(confidence * 100) + "%" : ""),
        "info"
      );
      setStatus("सबै विवरण जाँच्नुहोस्। Review the highlighted details before submitting.");
    } catch (error) {
      if (error.code === "gemini_not_configured") {
        setReviewState("manual entry", "muted");
        showFeedback(
          ui.extractFeedback,
          "AI parsing is switched off because GEMINI_API_KEY is not set on the server. Your transcript is kept — please fill the details by hand and submit.",
          "warning"
        );
      } else {
        showFeedback(ui.extractFeedback, "Could not extract details: " + error.message, "error", error.details);
      }
    } finally {
      ui.extractBtn.disabled = !ui.transcript.value.trim();
      ui.extractBtn.textContent = originalLabel;
    }
  }

  function setFieldValue(name, value) {
    const input = ui.form.querySelector('[name="' + name + '"]');
    if (!input || value === null || value === undefined || value === "") return false;
    if (input.tagName === "SELECT" && !Array.from(input.options).some(function (o) { return o.value === String(value); })) {
      return false;
    }
    input.value = value;
    markField(name, "ai");
    return true;
  }

  function fillForm(values) {
    clearMarks();
    if (!values) return;
    [
      "requester_name", "phone", "user_type", "request_type", "product_name",
      "quantity", "unit", "price_per_unit", "expected_total", "location", "fulfillment_type",
    ].forEach(function (name) {
      setFieldValue(name, values[name]);
    });

    if (values.requested_date) {
      setFieldValue("requested_date", values.requested_date);
    } else if (values.requested_date_text) {
      setFieldValue("requested_date_text", values.requested_date_text);
      ui.dateTextField.hidden = false;
      markField("requested_date", "attention");
    }
    setReviewState("AI extraction", "info");
  }

  function renderFlags(missing, ambiguities) {
    ui.flagRegion.innerHTML = "";
    if (!missing.length && !ambiguities.length) {
      ui.flagRegion.hidden = true;
      return;
    }
    ui.flagRegion.hidden = false;

    if (missing.length) {
      const block = document.createElement("div");
      block.className = "flag-block warn";
      const title = document.createElement("strong");
      title.textContent = "कृपया यी जानकारी थप्नुहोस् · Please add these required details";
      const ul = document.createElement("ul");
      missing.forEach(function (field) {
        const li = document.createElement("li");
        li.textContent = fieldLabel(field);
        ul.appendChild(li);
        markField(field, "attention");
      });
      block.appendChild(title);
      block.appendChild(ul);
      ui.flagRegion.appendChild(block);
    }

    if (ambiguities.length) {
      const block = document.createElement("div");
      block.className = "flag-block info";
      const title = document.createElement("strong");
      title.textContent = "पुष्टि गर्नुपर्ने · Please confirm these";
      const ul = document.createElement("ul");
      ambiguities.forEach(function (item) {
        const li = document.createElement("li");
        li.textContent = (item.question || fieldLabel(item.field)) + " (" + (item.reason || "uncertain") + ")";
        ul.appendChild(li);
        markField(item.field, "attention");
      });
      block.appendChild(title);
      block.appendChild(ul);
      ui.flagRegion.appendChild(block);
    }
  }

  /* ------------------------------ submission ---------------------------- */
  function newAttemptId() {
    if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
    return "attempt-" + Date.now() + "-" + Math.random().toString(16).slice(2);
  }

  function collectForm() {
    const data = new FormData(ui.form);
    const payload = {};
    data.forEach(function (value, key) {
      const text = String(value).trim();
      if (key === "quantity" || key === "price_per_unit" || key === "expected_total") {
        payload[key] = text === "" ? null : Number(text);
      } else {
        payload[key] = text === "" ? null : text;
      }
    });
    return payload;
  }

  async function submitOrder(event) {
    event.preventDefault();
    hideFeedback(ui.submitFeedback);
    const payload = collectForm();

    const missing = requiredFields.filter(function (field) {
      const value = payload[field];
      return value === null || value === undefined || value === "";
    });
    if (missing.length) {
      renderFlags(missing, (lastExtraction && lastExtraction.ambiguities) || []);
      showFeedback(
        ui.submitFeedback,
        "यी विवरणहरू आवश्यक छन् · These required details are still missing.",
        "warning",
        missing.map(function (field) { return { field: field, message: "required" }; })
      );
      App.toast("Please complete the highlighted fields.", "warning");
      return;
    }

    if (!submitAttemptId) submitAttemptId = newAttemptId();
    ui.submitBtn.disabled = true;
    const originalLabel = ui.submitBtn.textContent;
    ui.submitBtn.textContent = "पठाउँदै… Sending…";

    try {
      const response = await App.request("/api/orders", {
        method: "POST",
        body: {
          order: payload,
          transcript: ui.transcript.value.trim() || null,
          language: ui.language.value,
          client_request_id: submitAttemptId,
          source: "voice-ui",
        },
      });
      App.tracking.add({
        code: response.request_code,
        token: response.tracking_token || null,
        product: response.request.product_name,
        created_at: response.request.created_at,
      });
      ui.resultCard.hidden = false;
      ui.resultCode.textContent = response.request_code;
      ui.resultMessage.textContent = response.message + (response.duplicate ? " (already submitted earlier — no duplicate was created)" : "");
      ui.reviewSection.querySelectorAll("#order-form").forEach(function (node) { node.hidden = true; });
      ui.resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
      App.toast(response.message, "success", 8000);
    } catch (error) {
      if (error.status === 422) {
        renderFlags(
          (error.details || []).filter(function (d) { return d.code === "required"; }).map(function (d) { return d.field; }),
          []
        );
      }
      showFeedback(ui.submitFeedback, error.message, "error", error.details);
      App.toast(error.message, "error", 8000);
    } finally {
      ui.submitBtn.disabled = false;
      ui.submitBtn.textContent = originalLabel;
    }
  }

  function resetForNewRequest() {
    ui.form.reset();
    ui.transcript.value = "";
    ui.transcriptSource.textContent = "not recorded yet";
    ui.extractBtn.disabled = true;
    ui.flagRegion.hidden = true;
    ui.flagRegion.innerHTML = "";
    ui.dateTextField.hidden = true;
    hideFeedback(ui.submitFeedback);
    hideFeedback(ui.extractFeedback);
    clearMarks();
    setReviewState("manual entry", "muted");
    lastExtraction = null;
    submitAttemptId = null;
    ui.resultCard.hidden = true;
    ui.form.hidden = false;
    ui.reviewSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ------------------------------ wiring -------------------------------- */
  if (ui.micButton) {
    ui.micButton.addEventListener("click", function () {
      if (mediaRecorder && mediaRecorder.state === "recording") stopRecording();
      else startRecording();
    });
  }
  if (ui.extractBtn) ui.extractBtn.addEventListener("click", extractDetails);
  if (ui.transcript) {
    ui.transcript.addEventListener("input", function () {
      ui.extractBtn.disabled = !ui.transcript.value.trim() || busy;
    });
  }
  if (ui.clearBtn) {
    ui.clearBtn.addEventListener("click", function () {
      ui.transcript.value = "";
      ui.transcriptSource.textContent = "not recorded yet";
      ui.extractBtn.disabled = true;
      ui.flagRegion.hidden = true;
      clearMarks();
      setReviewState("manual entry", "muted");
      lastExtraction = null;
    });
  }
  if (ui.form) ui.form.addEventListener("submit", submitOrder);
  if (ui.newRequestBtn) ui.newRequestBtn.addEventListener("click", resetForNewRequest);
  ui.quickTypeButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const field = ui.form.querySelector('[name="user_type"]');
      field.value = button.dataset.quickUserType;
      ui.quickTypeButtons.forEach(function (other) { other.classList.remove("selected"); });
      button.classList.add("selected");
      App.toast("Marked as " + button.dataset.quickUserType + ".", "info", 3000);
    });
  });
  window.addEventListener("pagehide", function () {
    stopTimer();
    stopSpeechPreview();
    stopStream();
  });

  setReviewState(aiConfigured ? "manual entry" : "manual entry (AI off)", "muted");
  if (!aiConfigured) {
    setStatus("AI सहायक निष्क्रिय छ — कृपया टाइप गर्नुहोस्। Type your order below; an administrator will review it.", "error");
  }
})();

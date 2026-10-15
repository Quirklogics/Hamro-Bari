/* Shared helpers: CSRF-aware fetch, toasts, confirmation modal, local tracking. */
(function () {
  "use strict";

  const TRACKING_KEY = "hamro_baari_voice_requests_v1";

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : "";
  }

  async function request(url, options) {
    const opts = options || {};
    const method = (opts.method || "GET").toUpperCase();
    const headers = Object.assign({}, opts.headers || {});
    if (method !== "GET" && method !== "HEAD") headers["X-CSRFToken"] = csrfToken();

    let body = opts.body;
    if (body !== undefined && body !== null && !(body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(body);
    }

    let response;
    try {
      response = await fetch(url, {
        method: method,
        headers: headers,
        body: body === undefined ? null : body,
        credentials: "same-origin",
      });
    } catch (networkError) {
      const error = new Error("Network error - is the server still running?");
      error.status = 0;
      error.code = "network_error";
      throw error;
    }

    let data = null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.indexOf("application/json") !== -1) {
      try {
        data = await response.json();
      } catch (parseError) {
        data = null;
      }
    }

    if (!response.ok) {
      const payload = (data && data.error) || {};
      const error = new Error(payload.message || "Request failed (" + response.status + ").");
      error.status = response.status;
      error.code = payload.code || "http_" + response.status;
      error.details = payload.details || [];
      error.fallback = payload.fallback || null;
      throw error;
    }
    return data;
  }

  function toast(message, type, timeout) {
    const region = document.getElementById("toast-region");
    if (!region) return;
    const el = document.createElement("div");
    el.className = "toast " + (type || "success");
    el.textContent = message;
    region.appendChild(el);
    window.setTimeout(function () {
      el.style.opacity = "0";
      window.setTimeout(function () {
        el.remove();
      }, 250);
    }, timeout || 5000);
  }

  function confirmDialog(config) {
    const options = config || {};
    const backdrop = document.getElementById("confirm-modal");
    if (!backdrop) return Promise.resolve(window.confirm(options.message || "Are you sure?"));
    const title = backdrop.querySelector("#confirm-title");
    const message = backdrop.querySelector("#confirm-message");
    const confirmBtn = backdrop.querySelector("[data-modal-confirm]");
    const cancelBtn = backdrop.querySelector("[data-modal-cancel]");

    title.textContent = options.title || "Please confirm";
    message.textContent = options.message || "";
    confirmBtn.textContent = options.confirmText || "Confirm";
    confirmBtn.className = "btn " + (options.danger ? "btn-danger" : "btn-primary");
    backdrop.hidden = false;
    confirmBtn.focus();

    return new Promise(function (resolve) {
      function close(result) {
        backdrop.hidden = true;
        confirmBtn.removeEventListener("click", onConfirm);
        cancelBtn.removeEventListener("click", onCancel);
        backdrop.removeEventListener("click", onBackdrop);
        document.removeEventListener("keydown", onKey);
        resolve(result);
      }
      function onConfirm() { close(true); }
      function onCancel() { close(false); }
      function onBackdrop(event) { if (event.target === backdrop) close(false); }
      function onKey(event) { if (event.key === "Escape") close(false); }
      confirmBtn.addEventListener("click", onConfirm);
      cancelBtn.addEventListener("click", onCancel);
      backdrop.addEventListener("click", onBackdrop);
      document.addEventListener("keydown", onKey);
    });
  }

  function readEntries() {
    try {
      const raw = window.localStorage.getItem(TRACKING_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      return [];
    }
  }

  function writeEntries(entries) {
    try {
      window.localStorage.setItem(TRACKING_KEY, JSON.stringify(entries));
    } catch (error) {
      /* storage disabled (private mode): tracking page simply stays empty */
    }
  }

  const tracking = {
    key: TRACKING_KEY,
    list: readEntries,
    add: function (entry) {
      const entries = readEntries().filter(function (item) {
        return item.code !== entry.code;
      });
      entries.unshift(entry);
      writeEntries(entries.slice(0, 100));
    },
    forget: function (code) {
      writeEntries(readEntries().filter(function (item) { return item.code !== code; }));
    },
    clear: function () { writeEntries([]); },
  };

  function renderDetails(details, container) {
    if (!container) return;
    container.innerHTML = "";
    if (!details || !details.length) return;
    const list = document.createElement("ul");
    details.forEach(function (item) {
      const li = document.createElement("li");
      li.textContent = (item.field ? item.field + ": " : "") + (item.message || item.code || "invalid");
      list.appendChild(li);
    });
    container.appendChild(list);
  }

  window.App = {
    request: request,
    toast: toast,
    confirm: confirmDialog,
    tracking: tracking,
    renderDetails: renderDetails,
    csrfToken: csrfToken,
  };
})();

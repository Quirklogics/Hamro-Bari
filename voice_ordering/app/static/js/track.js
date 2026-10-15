/* "My requests": status of requests submitted from this browser. */
(function () {
  "use strict";

  const App = window.App;
  const listEl = document.getElementById("track-list");
  const emptyEl = document.getElementById("track-empty");
  const loadingEl = document.getElementById("track-loading");
  const feedbackEl = document.getElementById("track-feedback");
  const refreshBtn = document.getElementById("btn-refresh");
  const forgetBtn = document.getElementById("btn-forget");
  if (!listEl) return;

  function statusBadge(status, label) {
    const tone = (label && label.tone) || "muted";
    const text = (label && label.en) || status;
    return '<span class="badge badge-' + tone + '">' + text + "</span>";
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatTimestamp(value) {
    if (!value) return "—";
    const parsed = new Date(value.endsWith("Z") ? value : value + "Z");
    if (isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) + " (local)";
  }

  function renderCard(entry, request) {
    const card = document.createElement("article");
    card.className = "track-card";

    if (!request) {
      card.innerHTML =
        "<h3><span class='mono'>" + escapeHtml(entry.code) + "</span><span class='badge badge-muted'>unknown</span></h3>" +
        "<p class='muted small'>This entry could not be verified on the server. It may have been created in a " +
        "different environment or the link is no longer valid.</p>";
    } else {
      const history = (request.history || [])
        .slice(-4)
        .map(function (item) {
          return "<li>" + escapeHtml(item.action.replace(/_/g, " ")) + " · " + escapeHtml(formatTimestamp(item.created_at)) +
            (item.reason ? " — " + escapeHtml(item.reason) : "") + "</li>";
        })
        .join("");

      card.innerHTML =
        "<h3><span class='mono'>" + escapeHtml(request.request_code) + "</span>" +
        statusBadge(request.status, request.status_label) + "</h3>" +
        "<div class='track-meta'>" +
        "<span><strong>" + escapeHtml(request.product_name || "—") + "</strong> · " + escapeHtml(request.quantity_display) + "</span>" +
        "<span class='muted'>" + escapeHtml(request.request_type || "") +
        (request.location ? " · " + escapeHtml(request.location) : "") + "</span>" +
        "<span class='muted small'>Submitted " + escapeHtml(formatTimestamp(request.created_at)) + "</span>" +
        "</div>" +
        (request.clarification_question
          ? "<div class='clarify-box'><strong>प्रशासकको प्रश्न · Administrator question</strong><p>" +
            escapeHtml(request.clarification_question) + "</p></div>"
          : "") +
        (request.missing_fields && request.missing_fields.length
          ? "<p class='muted small'>Missing details: " + escapeHtml(request.missing_fields.join(", ")) + "</p>"
          : "") +
        (history ? "<ul class='track-history'>" + history + "</ul>" : "");
    }

    const actions = document.createElement("div");
    actions.className = "block-actions";
    const forget = document.createElement("button");
    forget.type = "button";
    forget.className = "btn btn-ghost btn-sm";
    forget.textContent = "Forget this entry";
    forget.addEventListener("click", function () {
      App.tracking.forget(entry.code);
      render();
    });
    actions.appendChild(forget);
    card.appendChild(actions);
    return card;
  }

  function setFeedback(message, type) {
    if (!feedbackEl) return;
    feedbackEl.hidden = !message;
    feedbackEl.innerHTML = "";
    if (message) {
      const box = document.createElement("div");
      box.className = "flash flash-" + (type || "info");
      box.textContent = message;
      feedbackEl.appendChild(box);
    }
  }

  async function render() {
    const entries = App.tracking.list();
    listEl.innerHTML = "";
    if (!entries.length) {
      emptyEl.hidden = false;
      setFeedback("", "info");
      return;
    }
    emptyEl.hidden = true;
    if (loadingEl) loadingEl.hidden = false;

    let failures = 0;
    for (const entry of entries) {
      let request = null;
      if (entry.token) {
        try {
          const response = await App.request("/api/orders/track", {
            method: "POST",
            body: { tracking_token: entry.token },
          });
          request = response.request;
        } catch (error) {
          failures += 1;
          if (error.status === 0) {
            setFeedback(error.message, "error");
          }
        }
      }
      listEl.appendChild(renderCard(entry, request));
    }
    if (loadingEl) loadingEl.hidden = true;
    if (failures && failures === entries.length) {
      setFeedback("Could not reach the server for " + failures + " request(s). Try refreshing.", "error");
    } else {
      setFeedback("", "info");
    }
  }

  if (refreshBtn) refreshBtn.addEventListener("click", function () { render(); });
  if (forgetBtn) {
    forgetBtn.addEventListener("click", async function () {
      const ok = await App.confirm({
        title: "Forget local entries?",
        message: "This removes the tracking links stored in this browser. The requests stay in the database and remain visible to administrators.",
        confirmText: "Forget all",
        danger: true,
      });
      if (ok) {
        App.tracking.clear();
        render();
        App.toast("Local tracking entries cleared.", "info");
      }
    });
  }

  render();
})();

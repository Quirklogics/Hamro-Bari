/* Administrator dashboard behaviour: notifications, approve/reject/clarify, edits. */
(function () {
  "use strict";

  const App = window.App;
  if (!App) return;

  /* --------------------------- sidebar (mobile) -------------------------- */
  const toggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  /* ----------------------------- notifications --------------------------- */
  function updateBell(count) {
    const bell = document.querySelector(".notif-bell");
    if (!bell) return;
    let dot = bell.querySelector(".dot");
    if (count > 0) {
      if (!dot) {
        dot = document.createElement("span");
        dot.className = "dot";
        bell.appendChild(dot);
      }
      dot.textContent = count;
    } else if (dot) {
      dot.remove();
    }
  }

  async function markRead(button) {
    const id = button.dataset.markRead;
    button.disabled = true;
    try {
      const response = await App.request("/api/notifications/" + id + "/read", { method: "PATCH" });
      const item = document.querySelector('.notification[data-id="' + id + '"]');
      if (item) {
        item.classList.remove("unread");
        const target = item.querySelector("[data-mark-read]");
        if (target) {
          const note = document.createElement("span");
          note.className = "muted small";
          note.textContent = "read";
          target.replaceWith(note);
        }
      }
      updateBell(response.unread_count);
      App.toast("Notification marked as read.", "success", 2500);
    } catch (error) {
      button.disabled = false;
      App.toast(error.message, "error");
    }
  }

  document.querySelectorAll("[data-mark-read]").forEach(function (button) {
    button.addEventListener("click", function () { markRead(button); });
  });

  const markAll = document.getElementById("mark-all-read");
  if (markAll) {
    markAll.addEventListener("click", async function () {
      const ok = await App.confirm({
        title: "Mark all notifications read?",
        message: "The unread badge will be cleared for your account.",
        confirmText: "Mark all read",
      });
      if (!ok) return;
      try {
        const response = await App.request("/api/notifications/read-all", { method: "POST" });
        updateBell(0);
        window.location.reload();
        App.toast(response.updated + " notification(s) marked as read.", "success");
      } catch (error) {
        App.toast(error.message, "error");
      }
    });
  }

  /* --------------------------- quick approve (list) ---------------------- */
  document.querySelectorAll("[data-quick-approve]").forEach(function (button) {
    button.addEventListener("click", async function () {
      const id = button.dataset.quickApprove;
      const code = button.dataset.code;
      const ok = await App.confirm({
        title: "Approve " + code + "?",
        message: "The requester will see the approved status and a notification. This is recorded with your name and cannot be undone.",
        confirmText: "Approve request",
      });
      if (!ok) return;
      button.disabled = true;
      try {
        await App.request("/api/orders/" + id + "/approve", {
          method: "PATCH",
          body: { confirm: true },
        });
        App.toast(code + " approved.", "success");
        window.location.reload();
      } catch (error) {
        button.disabled = false;
        App.toast(error.message, "error", 8000);
      }
    });
  });

  /* ------------------------------ detail page ---------------------------- */
  const detailFeedback = document.getElementById("decision-feedback");

  function detailMessage(message, type) {
    if (!detailFeedback) {
      App.toast(message, type || "info");
      return;
    }
    detailFeedback.hidden = false;
    detailFeedback.innerHTML = "";
    const box = document.createElement("div");
    box.className = "flash flash-" + (type || "info");
    box.textContent = message;
    detailFeedback.appendChild(box);
  }

  const approveBtn = document.getElementById("btn-approve");
  if (approveBtn) {
    approveBtn.addEventListener("click", async function () {
      const ok = await App.confirm({
        title: "Approve " + approveBtn.dataset.code + "?",
        message: "This records your decision, notifies the requester in-app and locks the request from further status changes.",
        confirmText: "Approve request",
      });
      if (!ok) return;
      approveBtn.disabled = true;
      try {
        await App.request("/api/orders/" + approveBtn.dataset.requestId + "/approve", {
          method: "PATCH",
          body: { confirm: true },
        });
        App.toast("Request approved.", "success");
        window.location.reload();
      } catch (error) {
        approveBtn.disabled = false;
        detailMessage(error.message, "error");
      }
    });
  }

  const rejectOpen = document.getElementById("btn-reject-open");
  const rejectForm = document.getElementById("reject-form");
  if (rejectOpen && rejectForm) {
    rejectOpen.addEventListener("click", function () {
      rejectForm.hidden = !rejectForm.hidden;
    });
    const cancel = rejectForm.querySelector("[data-cancel-reject]");
    if (cancel) cancel.addEventListener("click", function () { rejectForm.hidden = true; });
  }

  const rejectSubmit = document.getElementById("btn-reject-submit");
  if (rejectSubmit) {
    rejectSubmit.addEventListener("click", async function () {
      const reasonInput = document.getElementById("reject-reason");
      const reason = reasonInput.value.trim();
      if (!reason) {
        App.toast("A rejection reason is required.", "warning");
        reasonInput.focus();
        return;
      }
      const ok = await App.confirm({
        title: "Reject this request?",
        message: "The reason is stored in the database and shown to the requester. This cannot be undone.",
        confirmText: "Reject request",
        danger: true,
      });
      if (!ok) return;
      rejectSubmit.disabled = true;
      try {
        await App.request("/api/orders/" + rejectSubmit.closest("aside").querySelector("[data-request-id]").dataset.requestId + "/reject", {
          method: "PATCH",
          body: { reason: reason, confirm: true },
        });
        App.toast("Request rejected.", "success");
        window.location.reload();
      } catch (error) {
        rejectSubmit.disabled = false;
        detailMessage(error.message, "error");
      }
    });
  }

  const clarifyOpen = document.getElementById("btn-clarify-open");
  const clarifyForm = document.getElementById("clarify-form");
  if (clarifyOpen && clarifyForm) {
    clarifyOpen.addEventListener("click", function () {
      clarifyForm.hidden = !clarifyForm.hidden;
    });
    const cancel = clarifyForm.querySelector("[data-cancel-clarify]");
    if (cancel) cancel.addEventListener("click", function () { clarifyForm.hidden = true; });
  }

  const clarifySubmit = document.getElementById("btn-clarify-submit");
  if (clarifySubmit) {
    clarifySubmit.addEventListener("click", async function () {
      const input = document.getElementById("clarify-question");
      const question = input.value.trim();
      if (!question) {
        App.toast("Please write the question for the requester.", "warning");
        input.focus();
        return;
      }
      const requestId = clarifySubmit.closest("aside").querySelector("[data-request-id]").dataset.requestId;
      clarifySubmit.disabled = true;
      try {
        await App.request("/api/orders/" + requestId + "/clarification", {
          method: "PATCH",
          body: { question: question },
        });
        App.toast("Clarification requested — the requester sees it on their tracking page.", "success", 7000);
        window.location.reload();
      } catch (error) {
        clarifySubmit.disabled = false;
        detailMessage(error.message, "error");
      }
    });
  }

  const editForm = document.getElementById("edit-form");
  if (editForm) {
    editForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const changes = {};
      new FormData(editForm).forEach(function (value, key) {
        const text = String(value).trim();
        if (key === "quantity" || key === "price_per_unit" || key === "expected_total") {
          changes[key] = text === "" ? null : Number(text);
        } else {
          changes[key] = text === "" ? null : text;
        }
      });
      const ok = await App.confirm({
        title: "Save corrections?",
        message: "Every changed field is written to the audit trail with your account name.",
        confirmText: "Save changes",
      });
      if (!ok) return;
      const submitButton = editForm.querySelector('button[type="submit"]');
      submitButton.disabled = true;
      try {
        const response = await App.request(
          "/api/orders/" + editForm.dataset.requestId,
          { method: "PATCH", body: { changes: changes, note: "Corrected in the admin dashboard" } }
        );
        App.toast(response.message, "success");
        window.location.reload();
      } catch (error) {
        submitButton.disabled = false;
        if (error.code === "no_changes") {
          detailMessage("Nothing changed — edit a value before saving.", "warning");
        } else {
          detailMessage(error.message, "error");
          App.renderDetails(error.details, detailFeedback);
        }
      }
    });
  }
})();

/**
 * Shared API helper with JWT auth
 */
const API = {
  getToken() {
    return localStorage.getItem("access_token");
  },

  async request(method, path, body = null) {
    const headers = { "Content-Type": "application/json" };
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const opts = { method, headers, credentials: "same-origin" };
    if (body && method !== "GET") opts.body = JSON.stringify(body);

    const res = await fetch(path, opts);

    if (res.status === 401) {
      localStorage.clear();
      window.location.href = "/login";
      throw new Error("انتهت الجلسة");
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data.detail || (typeof data.detail === "string" ? data.detail : "حدث خطأ");
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    return data;
  },

  get(path) { return this.request("GET", path); },
  post(path, body) { return this.request("POST", path, body); },
  put(path, body) { return this.request("PUT", path, body); },
  del(path) { return this.request("DELETE", path); },
};

function logout() {
  localStorage.clear();
  fetch("/api/auth/logout", { method: "POST" }).finally(() => {
    window.location.href = "/login";
  });
}

function toggleSidebar() {
  document.getElementById("sidebar")?.classList.toggle("open");
}

function closeModal() {
  document.getElementById("modal").hidden = true;
}

function openModal(title, html) {
  document.getElementById("modalTitle").textContent = title;
  document.getElementById("modalBody").innerHTML = html;
  document.getElementById("modal").hidden = false;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatDate(d) {
  if (!d) return "—";
  try {
    return new Date(d).toLocaleDateString("ar-SA");
  } catch {
    return d;
  }
}

// Auth guard
(function () {
  const token = localStorage.getItem("access_token");
  const role = localStorage.getItem("user_role");
  const path = window.location.pathname;

  if (!token) {
    if (!path.includes("/login")) window.location.href = "/login";
    return;
  }
  if (path.startsWith("/admin") && role !== "ADMIN") {
    window.location.href = "/student";
  }
  if (path.startsWith("/student") && role !== "STUDENT") {
    window.location.href = "/admin";
  }
})();

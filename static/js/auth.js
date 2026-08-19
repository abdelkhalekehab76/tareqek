/**
 * Login form handler – JWT authentication
 */
(function () {
  const form = document.getElementById("loginForm");
  const errorMsg = document.getElementById("errorMsg");
  const loginBtn = document.getElementById("loginBtn");

  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    errorMsg.hidden = true;
    loginBtn.disabled = true;
    loginBtn.textContent = "جاري التحقق...";

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
      // Prefer JSON endpoint for cleaner error handling
      const res = await fetch("/api/auth/login-json", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        credentials: "same-origin",
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "فشل تسجيل الدخول");
      }

      // Store token in localStorage for API calls
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_role", data.role);
      localStorage.setItem("user_name", data.full_name);
      localStorage.setItem("user_id", data.user_id);

      // Redirect based on role
      if (data.role === "ADMIN") {
        window.location.href = "/admin";
      } else {
        window.location.href = "/student";
      }
    } catch (err) {
      errorMsg.textContent = err.message || "حدث خطأ. حاول مرة أخرى.";
      errorMsg.hidden = false;
      loginBtn.disabled = false;
      loginBtn.textContent = "تسجيل الدخول";
    }
  });
})();

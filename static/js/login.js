const ROLE_ROUTES = {
  student: "/student/dashboard",
  cdpc: "/cdpc/dashboard",
  company: "/company/dashboard",
};

const ROLE_LABELS = { student: "Student", cdpc: "CDPC / Admin", company: "Company" };

const DEMO_CREDS = {
  student: { email: "n200001@rguktong.ac.in", password: "student123" },
  cdpc: { email: "cdpc@rguktong.ac.in", password: "cdpc12345" },
  company: { email: "technovasolutions@company.example.com", password: "company123" },
};

const GOOGLE_ERROR_MESSAGES = {
  missing_role: "Please choose a role (Student / CDPC / Company) before continuing with Google.",
  google_not_configured: "Google Sign-In isn't set up on this server yet. Ask the administrator to add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET, or sign in with email instead.",
  google_auth_failed: "Google Sign-In didn't complete. Please try again or use email instead.",
  role_mismatch: "This email is already registered under a different role. Please choose the correct role and try again.",
};

let selectedRole = "student";
let registeredEmailPendingOtp = "";
let resendCooldownTimer = null;
let forgotResendCooldownTimer = null;
let forgotPasswordEmail = "";

function setRole(role) {
  selectedRole = role;
  document.querySelectorAll(".role-pill").forEach((p) => p.classList.toggle("active", p.dataset.role === role));
  document.getElementById("role-title").textContent = ROLE_LABELS[role];
  const d = DEMO_CREDS[role];
  document.getElementById("demo-email").textContent = d.email;
  document.getElementById("demo-password").textContent = d.password;
  document.querySelectorAll(".reg-student-only").forEach((el) => (el.style.display = role === "student" ? "block" : "none"));
  document.querySelectorAll(".reg-company-only").forEach((el) => (el.style.display = role === "company" ? "block" : "none"));
}

function setTab(tab) {
  if (tab !== "login" && document.getElementById("forgot-password-panel")?.style.display !== "none") {
    closeForgotPassword();
  }
  document.querySelectorAll(".login-tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
  document.querySelectorAll(".login-form-panel").forEach((p) => p.classList.toggle("active", p.dataset.panel === tab));
  hideError();
  hideNotice();
}

function showError(msg) {
  const el = document.getElementById("form-error");
  el.textContent = msg;
  el.classList.add("show");
}
function hideError() {
  document.getElementById("form-error").classList.remove("show");
}
function showNotice(msg) {
  const el = document.getElementById("form-notice");
  el.textContent = msg;
  el.classList.add("show");
}
function hideNotice() {
  document.getElementById("form-notice").classList.remove("show");
}

function goToRegisterDetailsStep() {
  document.getElementById("register-otp-step").style.display = "none";
  document.getElementById("register-details-step").style.display = "block";
}
function goToRegisterOtpStep(email) {
  registeredEmailPendingOtp = email;
  document.getElementById("otp-target-email").textContent = email;
  document.getElementById("register-details-step").style.display = "none";
  document.getElementById("register-otp-step").style.display = "block";
  document.getElementById("reg-otp").value = "";
  document.getElementById("reg-otp").focus();
}

function startResendCooldown(seconds = 30) {
  const btn = document.getElementById("resend-otp-btn");
  btn.disabled = true;
  let remaining = seconds;
  btn.textContent = `Resend Code (${remaining}s)`;
  clearInterval(resendCooldownTimer);
  resendCooldownTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(resendCooldownTimer);
      btn.disabled = false;
      btn.textContent = "Resend Code";
    } else {
      btn.textContent = `Resend Code (${remaining}s)`;
    }
  }, 1000);
}

function collectRegisterPayload() {
  const payload = {
    role: selectedRole,
    name: document.getElementById("reg-name").value.trim(),
    email: document.getElementById("reg-email").value.trim().toLowerCase(),
    password: document.getElementById("reg-password").value,
    phone: document.getElementById("reg-phone").value.trim(),
  };
  if (selectedRole === "student") {
    payload.roll_number = document.getElementById("reg-roll").value.trim();
    payload.branch = document.getElementById("reg-branch").value;
  }
  if (selectedRole === "company") {
    payload.company_name = document.getElementById("reg-company-name").value.trim();
    payload.industry = document.getElementById("reg-industry").value.trim();
  }
  return payload;
}


function showForgotStep(step) {
  document.getElementById("forgot-email-step").style.display = step === "email" ? "block" : "none";
  document.getElementById("forgot-otp-step").style.display = step === "otp" ? "block" : "none";
  document.getElementById("forgot-reset-step").style.display = step === "reset" ? "block" : "none";
}

function startForgotResendCooldown(seconds = 30) {
  const btn = document.getElementById("forgot-resend-otp-btn");
  btn.disabled = true;
  let remaining = seconds;
  btn.textContent = `Resend Code (${remaining}s)`;
  clearInterval(forgotResendCooldownTimer);
  forgotResendCooldownTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(forgotResendCooldownTimer);
      btn.disabled = false;
      btn.textContent = "Resend Code";
    } else {
      btn.textContent = `Resend Code (${remaining}s)`;
    }
  }, 1000);
}

function openForgotPassword() {
  document.getElementById("forgot-password-panel").style.display = "block";
  document.getElementById("login-form").style.display = "none";
  document.getElementById("google-login-btn").style.display = "none";
  document.querySelector(".login-form-panel[data-panel='login'] .divider-with-text").style.display = "none";
  document.querySelector(".login-form-panel[data-panel='login'] .demo-hint").style.display = "none";
  showForgotStep("email");
  hideError();
  hideNotice();
  document.getElementById("forgot-email").value = document.getElementById("login-email").value.trim();
  document.getElementById("forgot-email").focus();
}

function closeForgotPassword() {
  document.getElementById("forgot-password-panel").style.display = "none";
  document.getElementById("login-form").style.display = "block";
  document.getElementById("google-login-btn").style.display = "flex";
  document.querySelector(".login-form-panel[data-panel='login'] .divider-with-text").style.display = "flex";
  document.querySelector(".login-form-panel[data-panel='login'] .demo-hint").style.display = "block";
  showForgotStep("email");
  clearInterval(forgotResendCooldownTimer);
  forgotPasswordEmail = "";
}

document.addEventListener("DOMContentLoaded", () => {
  renderStaticIcons();

  // Password-reset controls
  document.getElementById("forgot-password-btn").addEventListener("click", openForgotPassword);
  document.getElementById("forgot-back-btn").addEventListener("click", closeForgotPassword);

  document.getElementById("forgot-send-otp-btn").addEventListener("click", async () => {
    hideError();
    hideNotice();
    const email = document.getElementById("forgot-email").value.trim().toLowerCase();
    if (!email || !email.includes("@")) {
      showError("Please enter a valid email address.");
      return;
    }
    const btn = document.getElementById("forgot-send-otp-btn");
    btn.disabled = true;
    btn.textContent = "Sending code...";
    try {
      const res = await apiRequest("/auth/forgot-password/send-otp", { method: "POST", body: { email } });
      forgotPasswordEmail = email;
      document.getElementById("forgot-otp-target-email").textContent = email;
      showNotice(res.message);
      showForgotStep("otp");
      document.getElementById("forgot-otp").value = "";
      document.getElementById("forgot-otp").focus();
      startForgotResendCooldown();
    } catch (err) {
      showError(err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Send Reset Code";
    }
  });

  document.getElementById("forgot-resend-otp-btn").addEventListener("click", async () => {
    hideError();
    try {
      const res = await apiRequest("/auth/forgot-password/send-otp", { method: "POST", body: { email: forgotPasswordEmail } });
      showNotice(res.message);
      startForgotResendCooldown();
    } catch (err) {
      showError(err.message);
    }
  });

  document.getElementById("forgot-verify-otp-btn").addEventListener("click", async () => {
    hideError();
    const otp = document.getElementById("forgot-otp").value.trim();
    if (!/^\d{6}$/.test(otp)) {
      showError("Please enter the 6-digit verification code.");
      return;
    }
    const btn = document.getElementById("forgot-verify-otp-btn");
    btn.disabled = true;
    btn.textContent = "Verifying...";
    try {
      const res = await apiRequest("/auth/forgot-password/verify-otp", { method: "POST", body: { email: forgotPasswordEmail, otp } });
      showNotice(res.message);
      showForgotStep("reset");
      document.getElementById("forgot-new-password").focus();
    } catch (err) {
      showError(err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Verify Code";
    }
  });

  document.getElementById("forgot-reset-btn").addEventListener("click", async () => {
    hideError();
    const newPassword = document.getElementById("forgot-new-password").value;
    const confirmPassword = document.getElementById("forgot-confirm-password").value;
    if (newPassword.length < 6) {
      showError("Password must be at least 6 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      showError("Passwords do not match.");
      return;
    }
    const btn = document.getElementById("forgot-reset-btn");
    btn.disabled = true;
    btn.textContent = "Resetting...";
    try {
      const res = await apiRequest("/auth/forgot-password/reset", { method: "POST", body: { new_password: newPassword, confirm_password: confirmPassword } });
      showToast(res.message, "success");
      document.getElementById("login-email").value = forgotPasswordEmail;
      document.getElementById("login-password").value = "";
      closeForgotPassword();
    } catch (err) {
      showError(err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Reset Password";
    }
  });

  const params = new URLSearchParams(window.location.search);
  const roleParam = params.get("role");
  setRole(roleParam && ROLE_LABELS[roleParam] ? roleParam : "student");

  const tabParam = params.get("tab");
  if (tabParam === "register") setTab("register");

  const errorParam = params.get("error");
  if (errorParam && GOOGLE_ERROR_MESSAGES[errorParam]) {
    setTab("login");
    showError(GOOGLE_ERROR_MESSAGES[errorParam]);
  }

  document.querySelectorAll(".role-pill").forEach((p) => {
    p.addEventListener("click", () => setRole(p.dataset.role));
  });
  document.querySelectorAll(".login-tab").forEach((t) => {
    t.addEventListener("click", () => setTab(t.dataset.tab));
  });

  // Password visibility toggles
  document.querySelectorAll(".password-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.target);
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      btn.innerHTML = icon(isHidden ? "eye-off" : "eye", 15);
      btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
    });
  });

  // Google buttons — real browser navigation (OAuth requires a full redirect,
  // not a fetch call), server decides whether it's actually configured.
  document.getElementById("google-login-btn").addEventListener("click", () => {
    window.RgLoader ? RgLoader.navigate(`/api/auth/google/login?role=${selectedRole}`, "Connecting to Google…") : (window.location.href = `/api/auth/google/login?role=${selectedRole}`);
  });
  document.getElementById("google-register-btn").addEventListener("click", () => {
    window.RgLoader ? RgLoader.navigate(`/api/auth/google/login?role=${selectedRole}`, "Connecting to Google…") : (window.location.href = `/api/auth/google/login?role=${selectedRole}`);
  });

  // ---- Sign in ----
  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const btn = document.getElementById("login-submit-btn");
    btn.disabled = true;
    btn.textContent = "Signing in...";
    try {
      const data = await apiRequest("/auth/login", { method: "POST", body: { email, password, role: selectedRole } });
      showToast(`Welcome back, ${data.user.name.split(" ")[0]}!`, "success");
      setTimeout(() => (window.RgLoader ? RgLoader.navigate(ROLE_ROUTES[data.user.role], "Signing you in…") : (window.location.href = ROLE_ROUTES[data.user.role])), 400);
    } catch (err) {
      showError(err.message);
      btn.disabled = false;
      btn.textContent = "Sign In";
    }
  });

  document.getElementById("fill-demo-btn").addEventListener("click", () => {
    const d = DEMO_CREDS[selectedRole];
    document.getElementById("login-email").value = d.email;
    document.getElementById("login-password").value = d.password;
  });

  // ---- Register: Step 1 -> send OTP ----
  document.getElementById("send-otp-btn").addEventListener("click", async () => {
    hideError();
    const payload = collectRegisterPayload();
    if (!payload.name || !payload.email || payload.password.length < 6) {
      showError("Please fill in your name, a valid email, and a password of at least 6 characters.");
      return;
    }
    const btn = document.getElementById("send-otp-btn");
    btn.disabled = true;
    btn.textContent = "Sending code...";
    try {
      const res = await apiRequest("/auth/send-otp", { method: "POST", body: { email: payload.email, purpose: "register" } });
      showToast(res.message, res.sent_via_smtp ? "success" : "info");
      goToRegisterOtpStep(payload.email);
      startResendCooldown();
    } catch (err) {
      showError(err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Send Verification Code";
    }
  });

  document.getElementById("change-email-btn").addEventListener("click", () => {
    hideError();
    goToRegisterDetailsStep();
  });

  document.getElementById("resend-otp-btn").addEventListener("click", async () => {
    hideError();
    try {
      const res = await apiRequest("/auth/send-otp", { method: "POST", body: { email: registeredEmailPendingOtp, purpose: "register" } });
      showToast(res.message, res.sent_via_smtp ? "success" : "info");
      startResendCooldown();
    } catch (err) {
      showError(err.message);
    }
  });

  // ---- Register: Step 2 -> verify OTP + create account ----
  document.getElementById("verify-otp-btn").addEventListener("click", async () => {
    hideError();
    const otp = document.getElementById("reg-otp").value.trim();
    if (!otp) {
      showError("Please enter the 6-digit verification code.");
      return;
    }
    const payload = collectRegisterPayload();
    payload.email = registeredEmailPendingOtp;
    payload.otp = otp;

    const btn = document.getElementById("verify-otp-btn");
    btn.disabled = true;
    btn.textContent = "Verifying...";
    try {
      const data = await apiRequest("/auth/register", { method: "POST", body: payload });
      showToast(`Account created! Welcome, ${data.user.name.split(" ")[0]}.`, "success");
      setTimeout(() => (window.RgLoader ? RgLoader.navigate(ROLE_ROUTES[data.user.role], "Signing you in…") : (window.location.href = ROLE_ROUTES[data.user.role])), 400);
    } catch (err) {
      showError(err.message);
      btn.disabled = false;
      btn.textContent = "Verify & Create Account";
    }
  });
});
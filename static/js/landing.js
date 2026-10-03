function goToLogin(role) {
  window.location.href = `/login?role=${role}`;
}

document.addEventListener("DOMContentLoaded", () => renderStaticIcons());

// If already logged in, offer a quick redirect
(async function checkSession() {
  try {
    const res = await fetch("/api/auth/me", { credentials: "include" });
    if (res.ok) {
      const data = await res.json();
      const banner = document.getElementById("session-banner");
      if (banner) {
        const roleRoutes = { student: "/student/dashboard", cdpc: "/cdpc/dashboard", company: "/company/dashboard" };
        banner.style.display = "flex";
        banner.querySelector(".sb-text").textContent = `You're already signed in as ${data.user.name}.`;
        banner.querySelector(".sb-btn").href = roleRoutes[data.user.role];
      }
    }
  } catch (e) {}
})();

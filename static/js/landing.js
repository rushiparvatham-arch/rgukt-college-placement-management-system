function goToLogin(role) {
  window.RgLoader ? RgLoader.navigate(`/login?role=${role}`, "Opening sign-in…") : (window.location.href = `/login?role=${role}`);
}

function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function initNavScroll() {
  const nav = document.querySelector(".lp-nav");
  if (!nav) return;
  const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 12);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
}

function initReveal() {
  const items = document.querySelectorAll(".reveal");
  if (!items.length) return;

  if (prefersReducedMotion() || !("IntersectionObserver" in window)) {
    items.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
  );

  items.forEach((el) => observer.observe(el));
}

function initParallax() {
  const hero = document.getElementById("lp-hero");
  if (!hero || prefersReducedMotion()) return;

  const bg = hero.querySelector('[data-parallax="bg"]');
  const content = hero.querySelector('[data-parallax="content"]');
  const orbs = Array.from(hero.querySelectorAll('[data-parallax="orb"]'));
  const sectionImgs = Array.from(document.querySelectorAll("[data-parallax-section] img"));

  let rafId = 0;
  let mouseX = 0;
  let mouseY = 0;
  let targetMX = 0;
  let targetMY = 0;
  let needsSmooth = false;

  const apply = () => {
    rafId = 0;
    const scrollY = window.scrollY || window.pageYOffset;
    const heroH = hero.offsetHeight || 1;
    const progress = Math.min(Math.max(scrollY / heroH, 0), 1.4);

    mouseX += (targetMX - mouseX) * 0.1;
    mouseY += (targetMY - mouseY) * 0.1;
    needsSmooth =
      Math.abs(targetMX - mouseX) > 0.002 || Math.abs(targetMY - mouseY) > 0.002;

    if (bg) {
      const y = scrollY * 0.42;
      bg.style.transform = `translate3d(${mouseX * 12}px, ${y + mouseY * 8}px, 0) scale(1.08)`;
    }

    if (content) {
      const fade = Math.max(1 - progress * 1.15, 0);
      content.style.transform = `translate3d(${mouseX * -8}px, ${scrollY * 0.18 + mouseY * -6}px, 0)`;
      content.style.opacity = String(fade);
    }

    orbs.forEach((orb) => {
      const speed = parseFloat(orb.getAttribute("data-speed") || "0.2");
      orb.style.transform = `translate3d(${mouseX * (20 + speed * 40)}px, ${scrollY * speed + mouseY * (14 + speed * 30)}px, 0)`;
    });

    sectionImgs.forEach((img) => {
      const rect = img.parentElement.getBoundingClientRect();
      const viewH = window.innerHeight || 1;
      const mid = rect.top + rect.height / 2;
      const offset = ((mid - viewH / 2) / viewH) * -24;
      img.style.transform = `translate3d(0, ${offset}px, 0) scale(1.08)`;
    });

    if (needsSmooth) requestTick();
  };

  const requestTick = () => {
    if (!rafId) rafId = requestAnimationFrame(apply);
  };

  window.addEventListener("scroll", requestTick, { passive: true });
  window.addEventListener("resize", requestTick, { passive: true });

  hero.addEventListener(
    "pointermove",
    (e) => {
      const rect = hero.getBoundingClientRect();
      targetMX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      targetMY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      requestTick();
    },
    { passive: true }
  );

  hero.addEventListener(
    "pointerleave",
    () => {
      targetMX = 0;
      targetMY = 0;
      requestTick();
    },
    { passive: true }
  );

  apply();
}

document.addEventListener("DOMContentLoaded", () => {
  initNavScroll();
  initReveal();
  initParallax();
  if (typeof renderStaticIcons === "function") renderStaticIcons();
});

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
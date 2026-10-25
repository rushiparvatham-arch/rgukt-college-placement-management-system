/* RGUKT logo loader controller.
   - Full-screen preloader on every page load (hidden once the page + its first
     API calls have settled, with a minimum display time so it never flickers).
   - Shown again when navigating between pages.
   - Top progress bar while any /api request is in flight.
   - Buttons that trigger a request show a spinner until it completes.
   Public API: window.RgLoader.{show,hide,navigate,busy} */
(function () {
  "use strict";
  const MIN_SHOW_MS = 900;      // never flash the loader
  const MAX_SHOW_MS = 8000;     // never trap the user behind it
  const IDLE_MS = 250;          // network must be quiet this long
  const t0 = performance.now();
  let pending = 0, hidden = false, idleTimer = null, topTimer = null, pageLoaded = false;

  const $ = (id) => document.getElementById(id);
  const pre = () => $("rg-preloader");

  function setMsg(text) { const m = $("rg-pl-msg"); if (m && text) m.textContent = text; }

  function hide() {
    if (hidden) return;
    const wait = Math.max(0, MIN_SHOW_MS - (performance.now() - t0));
    setTimeout(() => {
      hidden = true;
      const p = pre(); if (p) p.classList.add("is-hidden");
      document.documentElement.classList.remove("rg-loading");
      setTimeout(() => { const q = pre(); if (q && q.classList.contains("is-hidden")) q.style.display = "none"; }, 700);
    }, wait);
  }

  function show(message) {
    const p = pre(); if (!p) return;
    hidden = false;
    p.style.display = "";
    void p.offsetWidth;
    p.classList.remove("is-hidden");
    p.classList.add("is-leaving");
    setMsg(message || "Please wait…");
  }

  function checkIdle() {
    clearTimeout(idleTimer);
    if (hidden || !pageLoaded || pending > 0) return;
    idleTimer = setTimeout(() => { if (pending === 0) hide(); }, IDLE_MS);
  }

  /* ---- top progress bar ---- */
  function barStart() {
    const bar = $("rg-topbar"); if (!bar) return;
    clearTimeout(topTimer);
    topTimer = setTimeout(() => {          // only if request is slower than 150ms
      if (pending <= 0) return;
      bar.classList.add("is-active");
      bar.firstElementChild.style.width = "70%";
    }, 150);
  }
  function barEnd() {
    const bar = $("rg-topbar"); if (!bar || pending > 0) return;
    clearTimeout(topTimer);
    bar.firstElementChild.style.width = "100%";
    setTimeout(() => { if (pending === 0) { bar.classList.remove("is-active"); bar.firstElementChild.style.width = "0"; } }, 350);
  }

  /* ---- button spinner: attach to the button that was just clicked ---- */
  let lastClick = { btn: null, at: 0 };
  document.addEventListener("click", (e) => {
    const b = e.target.closest && e.target.closest("button.btn, a.btn");
    if (b && !b.hasAttribute("data-no-loader")) lastClick = { btn: b, at: performance.now() };
  }, true);

  /* ---- wrap fetch ---- */
  const nativeFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    const url = typeof input === "string" ? input : (input && input.url) || "";
    const isApi = url.indexOf("/api/") !== -1;
    if (!isApi) return nativeFetch(input, init);
    pending++; barStart();
    let btn = null;
    if (lastClick.btn && performance.now() - lastClick.at < 120 && !lastClick.btn.disabled) {
      btn = lastClick.btn; lastClick = { btn: null, at: 0 };
      btn.classList.add("is-loading");
    }
    const done = () => {
      pending = Math.max(0, pending - 1);
      if (btn) btn.classList.remove("is-loading");
      barEnd(); checkIdle();
    };
    return nativeFetch(input, init).then((r) => { done(); return r; }, (err) => { done(); throw err; });
  };

  /* ---- in-site navigation shows the loader ---- */
  function isInternalNav(a) {
    if (!a || !a.href || a.target === "_blank" || a.hasAttribute("download")) return false;
    const u = new URL(a.href, location.href);
    if (u.origin !== location.origin) return false;
    if (u.pathname.indexOf("/api/") === 0 || /\.(csv|pdf|zip|xlsx?)$/i.test(u.pathname)) return false;
    if (u.pathname === location.pathname && u.search === location.search) return false; // hash / same page
    return true;
  }
  document.addEventListener("click", (e) => {
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
    const a = e.target.closest && e.target.closest("a[href]");
    if (a && isInternalNav(a)) show("Opening page…");
  });
  function navigate(url, message) { show(message || "Opening page…"); setTimeout(() => { location.href = url; }, 180); }

  window.addEventListener("pageshow", (e) => { if (e.persisted) { pending = 0; hidden = false; hide(); } }); // back button (bfcache)

  /* ---- smooth view switches inside dashboards ---- */
  function wrapNavigateTo() {
    if (typeof window.navigateTo !== "function" || window.navigateTo.__rg) return;
    const orig = window.navigateTo;
    const wrapped = function (view) {
      const bar = $("rg-topbar");
      if (bar) { bar.classList.add("is-active"); bar.firstElementChild.style.width = "60%"; setTimeout(() => { if (pending === 0) { bar.firstElementChild.style.width = "100%"; setTimeout(() => { bar.classList.remove("is-active"); bar.firstElementChild.style.width = "0"; }, 250); } }, 220); }
      return orig.apply(this, arguments);
    };
    wrapped.__rg = true; window.navigateTo = wrapped;
  }

  const msgs = { "/login": "Preparing sign-in…", "/student": "Loading student workspace…", "/cdpc": "Loading CDPC console…", "/company": "Loading recruiter workspace…" };
  const key = Object.keys(msgs).find((k) => location.pathname.indexOf(k) === 0);
  document.addEventListener("DOMContentLoaded", () => { if (key) setMsg(msgs[key]); setTimeout(wrapNavigateTo, 300); });
  window.addEventListener("load", () => { pageLoaded = true; checkIdle(); });
  setTimeout(hide, MAX_SHOW_MS);

  window.RgLoader = { show, hide, navigate, busy: (b, on) => b && b.classList.toggle("is-loading", !!on) };
})();
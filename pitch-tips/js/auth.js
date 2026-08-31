/**
 * Preflight Computer Vision — Client Authentication Gate
 * Credentials:
 *   Username: PreFlightTip
 *   Password: BetaVersion
 */

(function () {
  const AUTH_KEY = "preflight_auth_session";
  const REQUIRED_USER = "PreFlightTip";
  const REQUIRED_PASS = "BetaVersion";

  // Check initial state
  function isAuthenticated() {
    try {
      return (
        localStorage.getItem(AUTH_KEY) === "true" ||
        sessionStorage.getItem(AUTH_KEY) === "true"
      );
    } catch (e) {
      return false;
    }
  }

  function setAuthenticated() {
    try {
      localStorage.setItem(AUTH_KEY, "true");
      sessionStorage.setItem(AUTH_KEY, "true");
    } catch (e) {}
  }

  function clearAuthenticated() {
    try {
      localStorage.removeItem(AUTH_KEY);
      sessionStorage.removeItem(AUTH_KEY);
    } catch (e) {}
  }

  // Inject early protection styles
  function injectAuthStyles() {
    if (document.getElementById("preflight-auth-styles")) return;
    const style = document.createElement("style");
    style.id = "preflight-auth-styles";
    style.textContent = `
      body.pf-auth-locked > :not(#preflight-auth-overlay) {
        filter: blur(12px) brightness(0.2) !important;
        pointer-events: none !important;
        user-select: none !important;
        overflow: hidden !important;
      }
      body.pf-auth-locked {
        overflow: hidden !important;
        height: 100vh !important;
      }
      #preflight-auth-overlay {
        position: fixed;
        inset: 0;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at center, rgba(13, 22, 36, 0.96) 0%, rgba(6, 10, 16, 0.99) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        padding: 1.25rem;
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #e2e8f0;
      }
      .pf-auth-card {
        width: 100%;
        max-width: 440px;
        background: #0f1722;
        border: 1px solid rgba(59, 130, 246, 0.35);
        border-radius: 12px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.85), 0 0 35px rgba(59, 130, 246, 0.15);
        padding: 2.25rem;
        position: relative;
        overflow: hidden;
        animation: pfAuthPop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      }
      .pf-auth-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa, #38bdf8);
      }
      @keyframes pfAuthPop {
        from { opacity: 0; transform: scale(0.95) translateY(10px); }
        to { opacity: 1; transform: scale(1) translateY(0); }
      }
      .pf-auth-header {
        text-align: center;
        margin-bottom: 1.75rem;
      }
      .pf-auth-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #60a5fa;
        font-size: 0.72rem;
        font-weight: 700;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        margin-bottom: 0.75rem;
      }
      .pf-auth-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.02em;
      }
      .pf-auth-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        margin: 0;
        line-height: 1.45;
      }
      .pf-auth-form {
        display: flex;
        flex-direction: column;
        gap: 1.1rem;
      }
      .pf-auth-field {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        text-align: left;
      }
      .pf-auth-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #cbd5e1;
        letter-spacing: 0.02em;
      }
      .pf-auth-input {
        background: #080d14;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 0.65rem 0.85rem;
        color: #f8fafc;
        font-size: 0.92rem;
        font-family: 'IBM Plex Mono', monospace;
        transition: all 0.15s ease;
        outline: none;
      }
      .pf-auth-input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
        background: #0b121c;
      }
      .pf-auth-btn {
        background: #2563eb;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        font-size: 0.92rem;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.15s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin-top: 0.5rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
      }
      .pf-auth-btn:hover {
        background: #1d4ed8;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.45);
      }
      .pf-auth-btn:active {
        transform: translateY(0);
      }
      .pf-auth-error {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.35);
        color: #fca5a5;
        font-size: 0.82rem;
        padding: 0.6rem 0.75rem;
        border-radius: 6px;
        display: none;
        align-items: center;
        gap: 0.4rem;
        animation: pfAuthShake 0.35s ease;
      }
      @keyframes pfAuthShake {
        0%, 100% { transform: translateX(0); }
        20%, 60% { transform: translateX(-6px); }
        40%, 80% { transform: translateX(6px); }
      }
      .pf-auth-footer {
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid #1e293b;
        text-align: center;
        font-size: 0.76rem;
        color: #64748b;
      }
      .pf-auth-footer a {
        color: #60a5fa;
        text-decoration: none;
      }
      .pf-auth-footer a:hover {
        text-decoration: underline;
      }
      /* Topbar Sign Out Badge */
      .pf-auth-user-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(59, 130, 246, 0.35);
        color: #93c5fd;
        font-size: 0.72rem;
        font-family: 'IBM Plex Mono', monospace;
        padding: 0.25rem 0.55rem;
        border-radius: 4px;
        margin-left: 0.5rem;
      }
      .pf-auth-signout-btn {
        background: none;
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #fca5a5;
        font-size: 0.70rem;
        font-family: 'Manrope', sans-serif;
        font-weight: 600;
        padding: 0.15rem 0.45rem;
        border-radius: 3px;
        cursor: pointer;
        transition: all 0.15s ease;
      }
      .pf-auth-signout-btn:hover {
        background: rgba(239, 68, 68, 0.2);
        color: #fff;
        border-color: #ef4444;
      }
    `;
    document.head.appendChild(style);
  }

  function renderAuthOverlay() {
    if (document.getElementById("preflight-auth-overlay")) return;

    document.body.classList.add("pf-auth-locked");

    const overlay = document.createElement("div");
    overlay.id = "preflight-auth-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Preflight Restricted Access Login");

    overlay.innerHTML = `
      <div class="pf-auth-card">
        <div class="pf-auth-header">
          <div class="pf-auth-badge">
            <span>🔒</span> Preflight CV Platform
          </div>
          <h2 class="pf-auth-title">Operational Access</h2>
          <p class="pf-auth-subtitle">Advance scouting and biomechanical landmark telemetry are protected. Please authenticate to continue.</p>
        </div>

        <div id="pf-auth-error-msg" class="pf-auth-error">
          <span>⚠️</span> <span id="pf-auth-error-text">Invalid username or password.</span>
        </div>

        <form id="pf-auth-form" class="pf-auth-form" onsubmit="return false;">
          <div class="pf-auth-field">
            <label class="pf-auth-label" for="pf-auth-user">Username</label>
            <input
              type="text"
              id="pf-auth-user"
              class="pf-auth-input"
              placeholder="Enter username"
              autocomplete="username"
              required
            />
          </div>

          <div class="pf-auth-field">
            <label class="pf-auth-label" for="pf-auth-pass">Password</label>
            <input
              type="password"
              id="pf-auth-pass"
              class="pf-auth-input"
              placeholder="Enter password"
              autocomplete="current-password"
              required
            />
          </div>

          <button type="submit" id="pf-auth-submit-btn" class="pf-auth-btn">
            <span>Unlock Preflight Site</span> <span>→</span>
          </button>
        </form>

        <div class="pf-auth-footer">
          <span>Preflight Computer Vision · Professional Advance Scouting</span>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    const userInput = document.getElementById("pf-auth-user");
    const passInput = document.getElementById("pf-auth-pass");
    const form = document.getElementById("pf-auth-form");
    const errorBox = document.getElementById("pf-auth-error-msg");
    const errorText = document.getElementById("pf-auth-error-text");

    setTimeout(() => {
      userInput?.focus();
    }, 100);

    function handleSubmit(e) {
      if (e) e.preventDefault();
      const u = (userInput?.value || "").trim();
      const p = passInput?.value || "";

      if (u === REQUIRED_USER && p === REQUIRED_PASS) {
        setAuthenticated();
        document.body.classList.remove("pf-auth-locked");
        overlay.style.transition = "opacity 0.2s ease";
        overlay.style.opacity = "0";
        setTimeout(() => {
          overlay.remove();
          injectSignOutControls();
        }, 200);
      } else {
        if (errorBox && errorText) {
          errorText.textContent = "Invalid username or password. Please try again.";
          errorBox.style.display = "flex";
          // Re-trigger shake
          errorBox.style.animation = "none";
          errorBox.offsetHeight; // trigger reflow
          errorBox.style.animation = "pfAuthShake 0.35s ease";
        }
        if (passInput) {
          passInput.value = "";
          passInput.focus();
        }
      }
    }

    form?.addEventListener("submit", handleSubmit);
    document.getElementById("pf-auth-submit-btn")?.addEventListener("click", handleSubmit);
  }

  function injectSignOutControls() {
    if (document.getElementById("pf-auth-badge-el")) return;

    const nav = document.querySelector(".topbar .nav") || document.querySelector("header .nav") || document.querySelector(".nav");
    if (!nav) return;

    const wrap = document.createElement("div");
    wrap.id = "pf-auth-badge-el";
    wrap.className = "pf-auth-user-badge";
    wrap.innerHTML = `
      <span title="Authenticated Session">🔒 <strong>${REQUIRED_USER}</strong></span>
      <button type="button" class="pf-auth-signout-btn" id="pf-signout-btn" title="Sign out of Preflight">Sign Out</button>
    `;

    nav.appendChild(wrap);

    document.getElementById("pf-signout-btn")?.addEventListener("click", () => {
      clearAuthenticated();
      location.reload();
    });
  }

  function initAuthGate() {
    injectAuthStyles();
    if (isAuthenticated()) {
      document.body.classList.remove("pf-auth-locked");
      injectSignOutControls();
    } else {
      renderAuthOverlay();
    }
  }

  // Global methods
  window.preflightSignOut = function () {
    clearAuthenticated();
    location.reload();
  };

  window.preflightAuthCheck = isAuthenticated;

  // Run immediately or on DOMContentLoaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAuthGate);
  } else {
    initAuthGate();
  }
})();

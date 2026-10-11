/* EcoBuild — main.js (vanilla JS) */

// Auto-dismiss flash alerts after 5 seconds
document.addEventListener("DOMContentLoaded", function () {
  const alerts = document.querySelectorAll(".alert.auto-dismiss");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 5000);
  });
});

// Mobile navbar: close after selecting a navigation link.
const navbarCollapse = document.getElementById("navbarMain");

if (navbarCollapse) {
  navbarCollapse.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      if (
        window.innerWidth < 992 &&
        navbarCollapse.classList.contains("show") &&
        window.bootstrap
      ) {
        bootstrap.Collapse
          .getOrCreateInstance(navbarCollapse)
          .hide();
      }
    });
  });
}

// Fallback if the Bootstrap JavaScript CDN fails to load.
if (!window.bootstrap) {
  const toggle = document.querySelector(
    '[data-bs-target="#navbarMain"]'
  );

  if (toggle && navbarCollapse) {
    toggle.addEventListener("click", function () {
      const isOpen = navbarCollapse.classList.toggle("show");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });
  }
}

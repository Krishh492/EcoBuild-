
/* EcoBuild — main.js (vanilla JS) */

document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss flash alerts after 5 seconds.
  document.querySelectorAll(".alert.auto-dismiss").forEach(function (alert) {
    setTimeout(function () {
      if (!alert.isConnected) return;

      if (window.bootstrap) {
        window.bootstrap.Alert.getOrCreateInstance(alert).close();
      } else {
        alert.remove();
      }
    }, 5000);
  });

  // Manually close flash alerts using the X button.
  document.querySelectorAll(".alert .btn-close").forEach(function (button) {
    button.addEventListener("click", function () {
      const alert = button.closest(".alert");

      if (!alert) return;

      if (window.bootstrap) {
        window.bootstrap.Alert.getOrCreateInstance(alert).close();
      } else {
        alert.remove();
      }
    });
  });

  // Mobile navbar elements.
  const navbarCollapse = document.getElementById("navbarMain");
  const toggle = document.querySelector(
    '[data-bs-target="#navbarMain"]'
  );

  if (navbarCollapse) {
    // Close the mobile menu after clicking a navigation link.
    navbarCollapse.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (
          window.innerWidth < 992 &&
          navbarCollapse.classList.contains("show")
        ) {
          if (window.bootstrap) {
            window.bootstrap.Collapse
              .getOrCreateInstance(navbarCollapse)
              .hide();
          } else {
            navbarCollapse.classList.remove("show");

            if (toggle) {
              toggle.setAttribute("aria-expanded", "false");
            }
          }
        }
      });
    });

    // Fallback if Bootstrap JavaScript fails to load.
    if (!window.bootstrap && toggle) {
      toggle.addEventListener("click", function () {
        const isOpen = navbarCollapse.classList.toggle("show");
        toggle.setAttribute("aria-expanded", String(isOpen));
      });
    }
  }
});

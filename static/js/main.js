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

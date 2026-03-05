/**
 * theme.js — Light / Dark mode toggle with localStorage persistence.
 *
 * - Reads saved preference on every page load (instant, no flash)
 * - Toggles Bootstrap's data-bs-theme attribute on <html>
 * - Saves preference to localStorage as "mg-theme"
 * - Updates the toggle button icon accordingly
 */

(function () {
    // ── Apply saved theme IMMEDIATELY (before DOM paint) to avoid flash ──
    const saved = localStorage.getItem("mg-theme") || "dark";
    document.documentElement.setAttribute("data-bs-theme", saved);
    document.documentElement.setAttribute("data-mg-theme", saved);
})();

document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("theme-toggle");
    if (!toggleBtn) return;

    function getCurrentTheme() {
        return document.documentElement.getAttribute("data-mg-theme") || "dark";
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-bs-theme", theme);
        document.documentElement.setAttribute("data-mg-theme", theme);
        localStorage.setItem("mg-theme", theme);

        const icon = toggleBtn.querySelector("i");
        if (theme === "dark") {
            icon.className = "bi bi-sun-fill";
            toggleBtn.title = "Switch to Light Mode";
        } else {
            icon.className = "bi bi-moon-stars-fill";
            toggleBtn.title = "Switch to Dark Mode";
        }
    }

    // Set initial button icon based on current theme
    applyTheme(getCurrentTheme());

    // Toggle on click
    toggleBtn.addEventListener("click", function () {
        const next = getCurrentTheme() === "dark" ? "light" : "dark";
        applyTheme(next);
    });
});

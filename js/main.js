// Initialize Vanta.js background
document.addEventListener('DOMContentLoaded', function() {
    VANTA.NET({
        el: "#vanta-bg",
        color: 0x0072ff,
        backgroundColor: 0x021027,
        points: 12.00,
        maxDistance: 22.00,
        spacing: 18.00
    });

    // Button click handler
    document.getElementById('getStartedBtn').addEventListener('click', function() {
        // Add button click animation
        this.classList.add('clicked');
        setTimeout(() => {
            window.location.href = "dashboard.html"; // Change to your next page URL
        }, 500);
    });
});
// H.D.A GLOBAL - Main Scripts
document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });

    // Display selected file names in file inputs
    const fileInputs = document.querySelectorAll('input[type="file"][multiple]');
    fileInputs.forEach(function (input) {
        input.addEventListener('change', function () {
            const count = this.files.length;
            const label = this.parentElement.querySelector('.file-count-label');
            if (label) {
                label.textContent = count > 0 ? `${count} fichier(s) sélectionné(s)` : '';
            }
        });
    });
});


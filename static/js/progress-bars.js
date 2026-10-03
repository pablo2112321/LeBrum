(function () {
    'use strict';

    document.querySelectorAll('.js-progress-bar[data-progress]').forEach(function (bar) {
        var progress = Number.parseFloat(bar.dataset.progress);
        if (!Number.isFinite(progress)) {
            progress = 0;
        }
        bar.style.width = Math.min(100, Math.max(0, progress)) + '%';
    });
}());

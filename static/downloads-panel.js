(function () {
    'use strict';

    let trackedActive = {};

    function csrfHeader() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    function cancelJob(id) {
        fetch('/cancel_download/' + encodeURIComponent(id), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfHeader() }
        });
    }

    function announceCompletion(job) {
        const container = document.querySelector('main.container') || document.body;
        const cls = job.status === 'done' ? 'success' : (job.status === 'cancelled' ? 'warning' : 'danger');
        const iconName = job.status === 'done' ? 'check-circle' : (job.status === 'cancelled' ? 'ban' : 'exclamation-circle');
        const alert = document.createElement('div');
        alert.className = 'alert alert-' + cls + ' alert-dismissible fade show mt-4';
        const icon = document.createElement('i');
        icon.className = 'fas fa-' + iconName;
        icon.setAttribute('aria-hidden', 'true');
        alert.appendChild(icon);
        alert.appendChild(document.createTextNode(' ' + (job.message || '')));
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn-close';
        closeBtn.setAttribute('data-bs-dismiss', 'alert');
        closeBtn.setAttribute('aria-label', 'Close');
        alert.appendChild(closeBtn);
        container.insertBefore(alert, container.firstChild);
        setTimeout(function () { alert.remove(); }, 6000);
    }

    function buildJobRow(job) {
        const pct = job.percent || 0;
        const row = document.createElement('div');
        row.className = 'download-job';
        const top = document.createElement('div');
        top.className = 'download-job__top';
        const msg = document.createElement('div');
        msg.className = 'download-job__msg';
        msg.textContent = job.message || (job.status === 'queued' ? 'Queued…' : 'Processing…');
        const cancel = document.createElement('button');
        cancel.type = 'button';
        cancel.className = 'btn btn-sm btn-outline-danger';
        cancel.innerHTML = '<i class="fas fa-times" aria-hidden="true"></i> Cancel';
        cancel.addEventListener('click', function () { cancel.disabled = true; cancelJob(job.id); });
        top.appendChild(msg);
        top.appendChild(cancel);
        const prog = document.createElement('div');
        prog.className = 'progress';
        const bar = document.createElement('div');
        bar.className = 'progress-bar' + (job.status === 'queued' ? ' progress-bar-striped progress-bar-animated' : '');
        bar.setAttribute('role', 'progressbar');
        bar.style.width = pct + '%';
        prog.appendChild(bar);
        row.appendChild(top);
        row.appendChild(prog);
        return row;
    }

    function renderPanel(jobs) {
        const panel = document.getElementById('downloadsPanel');
        const active = jobs.filter(function (j) { return j.status === 'running' || j.status === 'queued'; })
                           .sort(function (a, b) { return (b.seq || 0) - (a.seq || 0); });
        const activeIds = {};
        active.forEach(function (j) { activeIds[j.id] = true; });

        Object.keys(trackedActive).forEach(function (id) {
            if (!activeIds[id]) {
                const finished = jobs.filter(function (j) { return j.id === id; })[0];
                if (finished) { announceCompletion(finished); }
            }
        });
        trackedActive = {};
        active.forEach(function (j) { trackedActive[j.id] = j; });

        if (!panel) { return; }
        if (!active.length) { panel.style.display = 'none'; panel.innerHTML = ''; return; }
        panel.innerHTML = '';
        const title = document.createElement('div');
        title.className = 'downloads-panel__title';
        title.textContent = 'Active downloads (' + active.length + ')';
        panel.appendChild(title);
        active.forEach(function (job) { panel.appendChild(buildJobRow(job)); });
        panel.style.display = 'block';
    }

    function pollDownloads() {
        fetch('/downloads_status')
            .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
            .then(function (data) {
                const jobs = (data && data.jobs) || [];
                renderPanel(jobs);
                const active = jobs.some(function (j) { return j.status === 'running' || j.status === 'queued'; });
                if (active) { setTimeout(pollDownloads, 1500); }
            })
            .catch(function () { /* stop polling on error */ });
    }

    document.addEventListener('DOMContentLoaded', pollDownloads);
})();

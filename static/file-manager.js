(function () {
    'use strict';

    var filenameToDelete = '';
    var deletePrefix = '';
    var itemNoun = 'file';

    function csrfToken() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    function capitalize(text) {
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    function cleanupBootstrapModals() {
        document.querySelectorAll('.modal-backdrop').forEach(function (el) { el.remove(); });
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    function showDeleteConfirm(filename) {
        filenameToDelete = filename;
        cleanupBootstrapModals();
        var modal = document.getElementById('customDeleteModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    function hideDeleteConfirm() {
        var modal = document.getElementById('customDeleteModal');
        if (modal) { modal.style.display = 'none'; }
        document.body.style.overflow = '';
        filenameToDelete = '';
    }

    function confirmDelete() {
        if (!filenameToDelete) { return; }
        var url = deletePrefix + encodeURIComponent(filenameToDelete);
        hideDeleteConfirm();
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() }
        })
            .then(function (response) {
                return response.json().catch(function () { return { success: response.ok }; });
            })
            .then(function (data) {
                if (data.success) {
                    showAlert(capitalize(itemNoun) + ' deleted successfully!', 'success');
                    setTimeout(function () { location.reload(); }, 1000);
                } else {
                    showAlert('Error: ' + (data.error || ('Failed to delete ' + itemNoun)), 'danger');
                }
            })
            .catch(function () { showAlert('Failed to delete ' + itemNoun, 'danger'); });
    }

    function showAlert(message, type) {
        var container = document.getElementById('alertContainer');
        if (!container) { return; }
        var alert = document.createElement('div');
        alert.className = 'alert alert-' + type + ' alert-dismissible fade show';
        var icon = document.createElement('i');
        icon.className = 'fas fa-' + (type === 'success' ? 'check-circle' : 'exclamation-circle');
        icon.setAttribute('aria-hidden', 'true');
        alert.appendChild(icon);
        alert.appendChild(document.createTextNode(' ' + message));
        var closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn-close';
        closeBtn.setAttribute('data-bs-dismiss', 'alert');
        closeBtn.setAttribute('aria-label', 'Close');
        alert.appendChild(closeBtn);
        container.appendChild(alert);
        setTimeout(function () { alert.remove(); }, 5000);
    }

    function searchFiles(input) {
        var filter = input.value.toLowerCase();
        var rows = document.querySelectorAll('#fileTable tbody tr');
        var visible = 0;
        rows.forEach(function (row) {
            var span = row.querySelector('td:first-child span');
            var text = span ? span.textContent.toLowerCase() : '';
            var match = text.indexOf(filter) !== -1;
            row.style.display = match ? '' : 'none';
            if (match) { visible++; }
        });
        var count = document.getElementById('fileCount');
        if (count) { count.textContent = visible; }
        if (typeof window.updateStats === 'function') { window.updateStats(); }
    }

    function init(options) {
        deletePrefix = options.deletePrefix;
        itemNoun = options.itemNoun || 'file';
        document.addEventListener('DOMContentLoaded', function () {
            cleanupBootstrapModals();
            document.addEventListener('click', function (e) {
                var btn = e.target.closest('.js-delete');
                if (btn) { showDeleteConfirm(btn.getAttribute('data-filename')); }
            });
            document.addEventListener('keydown', function (e) {
                if ((e.ctrlKey || e.metaKey) && e.key && e.key.toLowerCase() === 'k') {
                    var search = document.getElementById('searchInput');
                    if (search) { e.preventDefault(); search.focus(); }
                }
            });
            if (typeof window.updateStats === 'function') { window.updateStats(); }
        });
    }

    window.FileManager = {
        init: init,
        hideDeleteConfirm: hideDeleteConfirm,
        confirmDelete: confirmDelete,
        searchFiles: searchFiles,
        showAlert: showAlert
    };
})();

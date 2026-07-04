(function () {
    'use strict';

    var deletePrefix = '';
    var bulkPrefix = '';
    var itemNoun = 'file';
    var itemNounPlural = 'files';
    var pending = null; // { kind: 'single' | 'bulk', names: [...] }

    function csrfToken() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    function capitalize(text) {
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    function plural(n) {
        return n === 1 ? itemNoun : itemNounPlural;
    }

    function postJson(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
            body: body
        }).then(function (response) {
            return response.json().catch(function () { return { success: response.ok }; });
        });
    }

    function cleanupBootstrapModals() {
        document.querySelectorAll('.modal-backdrop').forEach(function (el) { el.remove(); });
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    function openConfirm(message) {
        var msg = document.getElementById('confirmModalMessage');
        if (msg) { msg.textContent = message; }
        cleanupBootstrapModals();
        var modal = document.getElementById('customDeleteModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    function showDeleteConfirm(filename) {
        pending = { kind: 'single', names: [filename] };
        openConfirm('Delete this ' + itemNoun + "? This can't be undone.");
    }

    function showBulkConfirm() {
        var names = getSelected();
        if (!names.length) { return; }
        pending = { kind: 'bulk', names: names };
        openConfirm('Delete ' + names.length + ' ' + plural(names.length) + "? This can't be undone.");
    }

    function hideDeleteConfirm() {
        var modal = document.getElementById('customDeleteModal');
        if (modal) { modal.style.display = 'none'; }
        document.body.style.overflow = '';
        pending = null;
    }

    function confirmDelete() {
        if (!pending) { return; }
        var request = pending;
        hideDeleteConfirm();
        if (request.kind === 'single') {
            postJson(deletePrefix + encodeURIComponent(request.names[0]))
                .then(function (data) {
                    if (data.success) {
                        showAlert(capitalize(itemNoun) + ' deleted.', 'success');
                        setTimeout(function () { location.reload(); }, 800);
                    } else {
                        showAlert('Error: ' + (data.error || ('Failed to delete ' + itemNoun)), 'danger');
                    }
                })
                .catch(function () { showAlert('Failed to delete ' + itemNoun, 'danger'); });
        } else {
            postJson(bulkPrefix, JSON.stringify({ filenames: request.names }))
                .then(function (data) {
                    var deleted = data.deleted || 0;
                    var failed = data.failed || 0;
                    if (deleted > 0) {
                        showAlert('Deleted ' + deleted + ' ' + plural(deleted) + (failed ? ', ' + failed + ' failed' : '') + '.', failed ? 'danger' : 'success');
                        setTimeout(function () { location.reload(); }, 800);
                    } else {
                        showAlert(data.error || ('Failed to delete ' + itemNounPlural), 'danger');
                    }
                })
                .catch(function () { showAlert('Failed to delete ' + itemNounPlural, 'danger'); });
        }
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

    function rowCheckboxes() {
        return Array.prototype.slice.call(document.querySelectorAll('#fileTable tbody .js-select'));
    }

    function isVisible(box) {
        var row = box.closest('tr');
        return row && row.style.display !== 'none';
    }

    function getSelected() {
        return rowCheckboxes()
            .filter(function (box) { return box.checked; })
            .map(function (box) { return box.getAttribute('data-filename'); });
    }

    function clearSelection() {
        rowCheckboxes().forEach(function (box) { box.checked = false; });
        updateSelectionUI();
    }

    function toggleSelectAll(checked) {
        rowCheckboxes().forEach(function (box) {
            if (isVisible(box)) { box.checked = checked; }
        });
        updateSelectionUI();
    }

    function updateSelectionUI() {
        var boxes = rowCheckboxes();
        var visible = boxes.filter(isVisible);
        var checked = boxes.filter(function (box) { return box.checked; });
        var visibleChecked = visible.filter(function (box) { return box.checked; });

        var bar = document.getElementById('bulkBar');
        var count = document.getElementById('bulkCount');
        if (count) { count.textContent = checked.length; }
        if (bar) { bar.style.display = checked.length > 0 ? 'flex' : 'none'; }

        var selectAll = document.querySelector('.js-select-all');
        if (selectAll) {
            selectAll.checked = visible.length > 0 && visibleChecked.length === visible.length;
            selectAll.indeterminate = visibleChecked.length > 0 && visibleChecked.length < visible.length;
        }
    }

    function searchFiles(input) {
        var filter = input.value.toLowerCase();
        var rows = document.querySelectorAll('#fileTable tbody tr');
        var visible = 0;
        rows.forEach(function (row) {
            var span = row.querySelector('.js-filename');
            var text = span ? span.textContent.toLowerCase() : '';
            var match = text.indexOf(filter) !== -1;
            row.style.display = match ? '' : 'none';
            if (match) { visible++; }
        });
        var count = document.getElementById('fileCount');
        if (count) { count.textContent = visible; }
        updateSelectionUI();
        if (typeof window.updateStats === 'function') { window.updateStats(); }
    }

    function init(options) {
        deletePrefix = options.deletePrefix;
        bulkPrefix = options.bulkDelete || '';
        itemNoun = options.itemNoun || 'file';
        itemNounPlural = options.itemNounPlural || (itemNoun + 's');
        document.addEventListener('DOMContentLoaded', function () {
            cleanupBootstrapModals();
            document.addEventListener('click', function (e) {
                var del = e.target.closest('.js-delete');
                if (del) { showDeleteConfirm(del.getAttribute('data-filename')); return; }
                if (e.target.closest('.js-bulk-delete')) { showBulkConfirm(); return; }
                if (e.target.closest('.js-bulk-clear')) { clearSelection(); }
            });
            document.addEventListener('change', function (e) {
                if (e.target.classList.contains('js-select-all')) { toggleSelectAll(e.target.checked); return; }
                if (e.target.classList.contains('js-select')) { updateSelectionUI(); }
            });
            document.addEventListener('keydown', function (e) {
                if ((e.ctrlKey || e.metaKey) && e.key && e.key.toLowerCase() === 'k') {
                    var search = document.getElementById('searchInput');
                    if (search) { e.preventDefault(); search.focus(); }
                }
            });
            updateSelectionUI();
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

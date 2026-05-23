/**
 * Cam Cap — Interactive Frontend Logic
 */
(function () {
    'use strict';

    // ===== State =====
    const state = {
        selectedDrive: null,
        currentPath: '',
        selectedFiles: new Set(),
        allFiles: [],
        mergedFilePaths: [],
        sortBy: 'name',
        saveTo: '',
        resultFilename: '',
    };

    // ===== DOM Refs =====
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const els = {
        ffmpegStatus: $('#ffmpegStatus'),
        drivesGrid: $('#drivesGrid'),
        refreshDrives: $('#refreshDrives'),
        driveSection: $('#driveSection'),
        browserSection: $('#browserSection'),
        breadcrumbTrail: $('#breadcrumbTrail'),
        browserContent: $('#browserContent'),
        filesSection: $('#filesSection'),
        filesDesc: $('#filesDesc'),
        filesList: $('#filesList'),
        selectAllBtn: $('#selectAllBtn'),
        deselectAllBtn: $('#deselectAllBtn'),
        sortByName: $('#sortByName'),
        sortByDate: $('#sortByDate'),
        saveLocation: $('#saveLocation'),
        mergeSummary: $('#mergeSummary'),
        mergeBtn: $('#mergeBtn'),
        processingSection: $('#processingSection'),
        progressBar: $('#progressBar'),
        processingDetail: $('#processingDetail'),
        resultSection: $('#resultSection'),
        resultDetails: $('#resultDetails'),
        videoPreviewContainer: $('#videoPreviewContainer'),
        videoPreview: $('#videoPreview'),
        downloadBtn: $('#downloadBtn'),
        deleteOriginals: $('#deleteOriginals'),
        startOverBtn: $('#startOverBtn'),
        deleteModal: $('#deleteModal'),
        deleteCount: $('#deleteCount'),
        cancelDelete: $('#cancelDelete'),
        confirmDelete: $('#confirmDelete'),
        toastContainer: $('#toastContainer'),
        bgParticles: $('#bgParticles'),
    };

    // ===== Init =====
    function init() {
        createParticles();
        checkFFmpeg();
        loadDrives();
        bindEvents();
    }

    // ===== Particles =====
    function createParticles() {
        const colors = ['#6366f1', '#06b6d4', '#818cf8', '#10b981'];
        for (let i = 0; i < 30; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            const size = Math.random() * 4 + 2;
            p.style.width = size + 'px';
            p.style.height = size + 'px';
            p.style.left = Math.random() * 100 + '%';
            p.style.background = colors[Math.floor(Math.random() * colors.length)];
            p.style.animationDuration = (Math.random() * 15 + 10) + 's';
            p.style.animationDelay = (Math.random() * 10) + 's';
            els.bgParticles.appendChild(p);
        }
    }

    // ===== FFmpeg Check =====
    async function checkFFmpeg() {
        try {
            const res = await fetch('/api/check-ffmpeg/');
            const data = await res.json();
            const dot = els.ffmpegStatus.querySelector('.status-dot');
            const text = els.ffmpegStatus.querySelector('.status-text');
            if (data.installed) {
                dot.className = 'status-dot ok';
                text.textContent = 'FFmpeg Ready';
            } else {
                dot.className = 'status-dot error';
                text.textContent = 'FFmpeg Missing';
                showToast('FFmpeg not found. Please install FFmpeg.', 'error');
            }
        } catch (e) {
            showToast('Could not check FFmpeg status', 'error');
        }
    }

    // ===== Drive Loading =====
    async function loadDrives() {
        els.drivesGrid.innerHTML = '<div class="loading-card"><div class="spinner"></div><p>Scanning drives...</p></div>';
        try {
            const res = await fetch('/api/drives/');
            const data = await res.json();
            if (data.success) renderDrives(data.drives);
            else showToast(data.error || 'Failed to load drives', 'error');
        } catch (e) {
            els.drivesGrid.innerHTML = '<div class="loading-card"><p>Failed to scan drives. Check console.</p></div>';
        }
    }

    function renderDrives(drives) {
        if (!drives.length) {
            els.drivesGrid.innerHTML = '<div class="loading-card"><p>No drives detected.</p></div>';
            return;
        }
        els.drivesGrid.innerHTML = drives.map(d => {
            const isRemovable = d.type === 'removable';
            const warn = d.percent > 85;
            return `
            <div class="drive-card ${isRemovable ? 'removable' : ''}" data-path="${d.mountpoint}">
                <div class="drive-header">
                    <div class="drive-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            ${isRemovable
                                ? '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 8h20"/><circle cx="8" cy="14" r="1"/>'
                                : '<path d="M22 12H2M22 6H2M22 18H2"/><circle cx="18" cy="12" r="1"/>'}
                        </svg>
                    </div>
                    <div>
                        <div class="drive-letter">${d.device}</div>
                        <div class="drive-type ${isRemovable ? 'removable' : ''}">${isRemovable ? '● SD / Removable' : d.type}</div>
                    </div>
                </div>
                <div class="drive-bar"><div class="drive-bar-fill ${warn ? 'warn' : ''}" style="width:${d.percent}%"></div></div>
                <div class="drive-stats"><span>${d.used_display} used</span><span>${d.free_display} free</span></div>
            </div>`;
        }).join('');

        // Click events
        els.drivesGrid.querySelectorAll('.drive-card').forEach(card => {
            card.addEventListener('click', () => selectDrive(card.dataset.path));
        });
    }

    function selectDrive(path) {
        state.selectedDrive = path;
        els.drivesGrid.querySelectorAll('.drive-card').forEach(c => c.classList.remove('selected'));
        const sel = els.drivesGrid.querySelector(`[data-path="${CSS.escape(path)}"]`);
        if (sel) sel.classList.add('selected');
        browseTo(path);
    }

    // ===== Folder Browsing =====
    async function browseTo(path) {
        state.currentPath = path;
        els.browserSection.classList.remove('hidden');
        els.browserContent.innerHTML = '<div class="loading-card"><div class="spinner"></div><p>Loading folder...</p></div>';
        updateBreadcrumbs(path);

        try {
            const res = await fetch(`/api/browse/?path=${encodeURIComponent(path)}`);
            const data = await res.json();
            if (data.success) renderBrowser(data.data);
            else showToast(data.error || 'Cannot browse folder', 'error');
        } catch (e) {
            els.browserContent.innerHTML = '<div class="loading-card"><p>Error loading folder</p></div>';
        }
    }

    function updateBreadcrumbs(path) {
        const parts = path.replace(/\\/g, '/').split('/').filter(Boolean);
        let html = '';
        let accumulated = '';
        parts.forEach((part, i) => {
            accumulated += part + '/';
            const isLast = i === parts.length - 1;
            if (i > 0) html += '<span class="breadcrumb-sep">›</span>';
            html += `<span class="breadcrumb-item ${isLast ? 'active' : ''}" data-path="${accumulated}">${part}</span>`;
        });
        els.breadcrumbTrail.innerHTML = html;
        els.breadcrumbTrail.querySelectorAll('.breadcrumb-item:not(.active)').forEach(b => {
            b.addEventListener('click', () => browseTo(b.dataset.path));
        });
    }

    function renderBrowser(data) {
        let html = '';

        // Parent folder link
        if (data.parent_path && data.parent_path !== data.current_path) {
            html += `
            <div class="folder-item" data-path="${data.parent_path}">
                <div class="folder-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
                </div>
                <span class="folder-name">..</span>
            </div>`;
        }

        // Folders
        data.folders.forEach(f => {
            html += `
            <div class="folder-item" data-path="${f.path}">
                <div class="folder-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                </div>
                <span class="folder-name">${f.name}</span>
                ${f.build_count > 0 ? `<span class="folder-badge">${f.build_count} .build</span>` : ''}
            </div>`;
        });

        // Build files found → show file section
        if (data.files.length > 0) {
            state.allFiles = data.files;
            state.selectedFiles.clear();
            renderFiles(data.files);
            els.filesSection.classList.remove('hidden');
            els.filesDesc.textContent = `${data.build_file_count} files found — ${data.total_build_size_display} total`;
        } else {
            state.allFiles = [];
            state.selectedFiles.clear();
            els.filesSection.classList.add('hidden');
        }

        if (!data.folders.length && !data.files.length) {
            html += '<div class="loading-card"><p>This folder is empty</p></div>';
        }

        els.browserContent.innerHTML = html;

        // Folder click
        els.browserContent.querySelectorAll('.folder-item').forEach(fi => {
            fi.addEventListener('click', () => browseTo(fi.dataset.path));
        });
    }

    function renderFiles(files) {
        els.filesList.innerHTML = files.map((f, i) => `
        <div class="file-item ${state.selectedFiles.has(f.path) ? 'selected' : ''}" data-path="${f.path}" data-index="${i}">
            <div class="file-checkbox ${state.selectedFiles.has(f.path) ? 'checked' : ''}" data-path="${f.path}"></div>
            <div class="file-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            </div>
            <div class="file-info">
                <div class="file-name">${f.name}</div>
                <div class="file-meta">
                    <span>${f.size_display}</span>
                    <span>${f.duration_display}</span>
                    <span>${f.modified}</span>
                </div>
            </div>
        </div>`).join('');

        // File checkbox click
        els.filesList.querySelectorAll('.file-checkbox').forEach(cb => {
            cb.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleFile(cb.dataset.path);
            });
        });
        // Row click toggles too
        els.filesList.querySelectorAll('.file-item').forEach(row => {
            row.addEventListener('click', () => toggleFile(row.dataset.path));
        });

        updateMergeSummary();
    }

    function toggleFile(path) {
        if (state.selectedFiles.has(path)) state.selectedFiles.delete(path);
        else state.selectedFiles.add(path);

        const row = els.filesList.querySelector(`.file-item[data-path="${CSS.escape(path)}"]`);
        const cb = els.filesList.querySelector(`.file-checkbox[data-path="${CSS.escape(path)}"]`);
        if (row) row.classList.toggle('selected', state.selectedFiles.has(path));
        if (cb) cb.classList.toggle('checked', state.selectedFiles.has(path));
        updateMergeSummary();
    }

    function updateMergeSummary() {
        const count = state.selectedFiles.size;
        let totalSize = 0;
        state.allFiles.forEach(f => { if (state.selectedFiles.has(f.path)) totalSize += f.size; });
        els.mergeSummary.innerHTML = `
            <span class="merge-count">${count} file${count !== 1 ? 's' : ''} selected</span>
            <span class="merge-size">${formatSize(totalSize)} total</span>`;
        els.mergeBtn.disabled = count === 0;
    }

    // ===== Merge & Convert =====
    async function mergeFiles() {
        if (state.selectedFiles.size === 0) return;

        state.mergedFilePaths = [...state.selectedFiles];
        els.filesSection.classList.add('hidden');
        els.browserSection.classList.add('hidden');
        els.processingSection.classList.remove('hidden');
        els.progressBar.style.width = '10%';
        els.processingDetail.textContent = 'Starting merge...';

        // Simulate progress
        let progress = 10;
        const progressInterval = setInterval(() => {
            if (progress < 85) { progress += Math.random() * 5; els.progressBar.style.width = progress + '%'; }
        }, 800);

        try {
            els.processingDetail.textContent = 'Merging .build files with FFmpeg...';
            const res = await fetch('/api/merge/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    files: state.mergedFilePaths,
                    sort_by: state.sortBy,
                    save_to: state.saveTo,
                }),
            });
            clearInterval(progressInterval);
            const data = await res.json();

            if (data.success) {
                els.progressBar.style.width = '100%';
                els.processingDetail.textContent = 'Complete!';
                setTimeout(() => showResult(data.data), 600);
            } else {
                showToast(data.error || 'Merge failed', 'error');
                resetToFiles();
            }
        } catch (e) {
            clearInterval(progressInterval);
            showToast('Network error during merge', 'error');
            resetToFiles();
        }
    }

    function showResult(data) {
        state.resultFilename = data.filename;
        els.processingSection.classList.add('hidden');
        els.resultSection.classList.remove('hidden');
        els.resultDetails.innerHTML = `
            <span><strong>File:</strong> ${data.filename}</span>
            <span><strong>Size:</strong> ${data.size_display}</span>`;
        els.downloadBtn.href = `/api/download/${data.filename}/`;

        // Show video preview
        els.videoPreview.src = `/api/preview/${data.filename}/`;
        els.videoPreviewContainer.style.display = 'block';

        showToast('Merge & conversion complete!', 'success');
    }

    // ===== Delete Originals =====
    function showDeleteModal() {
        els.deleteCount.textContent = state.mergedFilePaths.length;
        els.deleteModal.classList.remove('hidden');
    }

    async function deleteOriginals() {
        els.deleteModal.classList.add('hidden');
        try {
            const res = await fetch('/api/delete/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: state.mergedFilePaths }),
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Deleted ${data.data.deleted} files from SD card`, 'success');
                if (data.data.failed > 0) showToast(`${data.data.failed} files failed to delete`, 'error');
            } else {
                showToast(data.error || 'Delete failed', 'error');
            }
        } catch (e) {
            showToast('Network error during delete', 'error');
        }
    }

    // ===== Helpers =====
    function resetToFiles() {
        els.processingSection.classList.add('hidden');
        els.filesSection.classList.remove('hidden');
        els.browserSection.classList.remove('hidden');
    }

    function startOver() {
        els.resultSection.classList.add('hidden');
        els.processingSection.classList.add('hidden');
        els.filesSection.classList.add('hidden');
        els.browserSection.classList.add('hidden');
        state.selectedFiles.clear();
        state.allFiles = [];
        state.mergedFilePaths = [];
        state.resultFilename = '';
        els.videoPreview.src = '';
        els.videoPreviewContainer.style.display = 'none';
        loadDrives();
    }

    function formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB'];
        let i = 0, s = bytes;
        while (s >= 1024 && i < units.length - 1) { s /= 1024; i++; }
        return s.toFixed(1) + ' ' + units[i];
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icons = {
            success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        };
        toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
        els.toastContainer.appendChild(toast);
        setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(40px)'; setTimeout(() => toast.remove(), 400); }, 4000);
    }

    // ===== Event Bindings =====
    function bindEvents() {
        els.refreshDrives.addEventListener('click', loadDrives);
        els.selectAllBtn.addEventListener('click', () => {
            state.allFiles.forEach(f => state.selectedFiles.add(f.path));
            renderFiles(state.allFiles);
        });
        els.deselectAllBtn.addEventListener('click', () => {
            state.selectedFiles.clear();
            renderFiles(state.allFiles);
        });
        els.sortByName.addEventListener('click', () => {
            state.sortBy = 'name';
            els.sortByName.classList.add('active');
            els.sortByDate.classList.remove('active');
        });
        els.sortByDate.addEventListener('click', () => {
            state.sortBy = 'date';
            els.sortByDate.classList.add('active');
            els.sortByName.classList.remove('active');
        });
        els.mergeBtn.addEventListener('click', mergeFiles);
        els.deleteOriginals.addEventListener('click', showDeleteModal);
        els.cancelDelete.addEventListener('click', () => els.deleteModal.classList.add('hidden'));
        els.confirmDelete.addEventListener('click', deleteOriginals);
        els.startOverBtn.addEventListener('click', startOver);
    }

    // ===== Boot =====
    document.addEventListener('DOMContentLoaded', init);
})();

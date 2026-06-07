/**
 * CamCap — File System Access API Logic for Converter
 */
document.addEventListener('DOMContentLoaded', () => {
    const pickerContainer = document.getElementById('pickerContainer');
    const selectFolderBtn = document.getElementById('selectFolderBtn');
    const fallbackInput = document.getElementById('fallbackInput');
    const fallbackFolderInput = document.getElementById('fallbackFolderInput');
    
    const filesSection = document.getElementById('filesSection');
    const filesList = document.getElementById('filesList');
    const mergeBtn = document.getElementById('mergeBtn');
    const mergeSummary = document.getElementById('mergeSummary');
    
    const processingSection = document.getElementById('processingSection');
    const progressBar = document.getElementById('progressBar');
    const processingDetail = document.getElementById('processingDetail');
    
    const resultSection = document.getElementById('resultSection');
    const resultDetails = document.getElementById('resultDetails');
    const videoPreviewContainer = document.getElementById('videoPreviewContainer');
    const videoPreview = document.getElementById('videoPreview');
    const downloadBtn = document.getElementById('downloadBtn');
    const startOverBtn = document.getElementById('startOverBtn');
    
    // Modal Elements
    const videoModal = document.getElementById('videoModal');
    const modalVideo = document.getElementById('modalVideo');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const modalTitle = document.getElementById('modalTitle');
    let currentPreviewUrl = null;
    
    let allBuildFiles = [];
    let selectedFiles = new Set();
    
    // Check API support
    if (!window.showDirectoryPicker) {
        fallbackInput.classList.remove('hidden');
        selectFolderBtn.classList.add('hidden');
    }
    
    // Modern API Picker
    selectFolderBtn.addEventListener('click', async () => {
        try {
            const dirHandle = await window.showDirectoryPicker();
            await scanDirectory(dirHandle);
        } catch (error) {
            console.error(error);
            if (error.name !== 'AbortError') {
                alert('Error accessing folder. Please try again or use a different browser.');
            }
        }
    });
    
    // Fallback Picker
    fallbackFolderInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        processFilesList(files);
    });
    
    async function scanDirectory(dirHandle) {
        pickerContainer.classList.add('hidden');
        filesSection.classList.remove('hidden');
        filesList.innerHTML = '<div class="p-4 text-center">Scanning folder...</div>';
        
        const files = [];
        try {
            for await (const entry of dirHandle.values()) {
                if (entry.kind === 'file' && entry.name.toLowerCase().endsWith('.build')) {
                    const file = await entry.getFile();
                    files.push(file);
                } else if (entry.kind === 'directory') {
                    // Optional: recursive scan. Keeping it shallow for performance unless requested.
                }
            }
            processFilesList(files);
        } catch (error) {
            console.error(error);
            filesList.innerHTML = '<div class="p-4 text-center text-red">Error scanning folder.</div>';
        }
    }
    
    function processFilesList(files) {
        // Filter .build files and sort by name
        allBuildFiles = files.filter(f => f.name.toLowerCase().endsWith('.build'));
        allBuildFiles.sort((a, b) => a.name.localeCompare(b.name));
        
        selectedFiles.clear();
        
        if (allBuildFiles.length === 0) {
            filesList.innerHTML = '<div class="p-4 text-center text-secondary">No .build files found in this folder.</div>';
            return;
        }
        
        renderFilesList();
    }
    
    function renderFilesList() {
        filesList.innerHTML = allBuildFiles.map((f, i) => `
            <div class="file-item ${selectedFiles.has(i) ? 'selected' : ''}" data-index="${i}" style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 1rem; flex: 1;">
                    <div class="file-checkbox"></div>
                    <div class="file-info">
                        <div class="file-name">${f.name}</div>
                        <div class="file-meta">
                            <span>${formatSize(f.size)}</span>
                            <span>${new Date(f.lastModified).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
                <button class="btn btn-ghost btn-sm preview-btn" data-index="${i}" style="padding: 4px 10px; font-size: 0.8rem;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px;"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    Preview
                </button>
            </div>
        `).join('');
        
        // Add click events for selection
        document.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.preview-btn')) return; // Ignore clicks on preview button
                
                const idx = parseInt(item.dataset.index);
                if (selectedFiles.has(idx)) {
                    selectedFiles.delete(idx);
                } else {
                    selectedFiles.add(idx);
                }
                renderFilesList();
                updateSummary();
            });
        });
        
        // Add click events for preview
        document.querySelectorAll('.preview-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = parseInt(btn.dataset.index);
                const file = allBuildFiles[idx];
                openPreviewModal(file);
            });
        });
        
        pickerContainer.classList.add('hidden');
        filesSection.classList.remove('hidden');
        updateSummary();
    }
    
    function updateSummary() {
        mergeSummary.innerHTML = `<span class="merge-count">${selectedFiles.size} file${selectedFiles.size !== 1 ? 's' : ''} selected</span>`;
        mergeBtn.disabled = selectedFiles.size === 0;
    }
    
    // Modal Logic
    function openPreviewModal(file) {
        modalTitle.textContent = `Preview: ${file.name}`;
        
        if (currentPreviewUrl) {
            URL.revokeObjectURL(currentPreviewUrl);
        }
        
        // Try setting standard mp4 MIME type just in case browser rejects unknown .build
        const blob = new Blob([file], { type: 'video/mp4' });
        currentPreviewUrl = URL.createObjectURL(blob);
        
        modalVideo.src = currentPreviewUrl;
        videoModal.classList.remove('hidden');
        modalVideo.play().catch(e => console.warn('Autoplay prevented', e));
    }
    
    function closePreviewModal() {
        videoModal.classList.add('hidden');
        modalVideo.pause();
        modalVideo.src = '';
        if (currentPreviewUrl) {
            URL.revokeObjectURL(currentPreviewUrl);
            currentPreviewUrl = null;
        }
    }
    
    closeModalBtn.addEventListener('click', closePreviewModal);
    videoModal.addEventListener('click', (e) => {
        if (e.target === videoModal) closePreviewModal();
    });
    
    // Select All / Deselect All
    document.getElementById('selectAllBtn').addEventListener('click', () => {
        allBuildFiles.forEach((_, i) => selectedFiles.add(i));
        renderFilesList();
    });
    
    document.getElementById('deselectAllBtn').addEventListener('click', () => {
        selectedFiles.clear();
        renderFilesList();
    });
    
    // Upload and Merge
    mergeBtn.addEventListener('click', async () => {
        if (selectedFiles.size === 0) return;
        
        filesSection.classList.add('hidden');
        processingSection.classList.remove('hidden');
        progressBar.style.width = '10%';
        processingDetail.textContent = 'Uploading files...';
        
        const formData = new FormData();
        selectedFiles.forEach(idx => {
            formData.append('files', allBuildFiles[idx]);
        });
        
        formData.append('sort_by', document.querySelector('.toggle-btn.active').dataset.sort);
        
        // Simulate progress for UI
        let progress = 10;
        const progressInterval = setInterval(() => {
            if (progress < 85) {
                progress += Math.random() * 5;
                progressBar.style.width = progress + '%';
            }
        }, 1000);
        
        try {
            const response = await fetch('/api/merge/', {
                method: 'POST',
                body: formData
                // Don't set Content-Type header, let browser set it with boundary for multipart/form-data
            });
            
            clearInterval(progressInterval);
            const data = await response.json();
            
            if (data.success) {
                progressBar.style.width = '100%';
                processingDetail.textContent = 'Complete!';
                setTimeout(() => showResult(data.data), 800);
            } else {
                alert('Error: ' + data.error);
                processingSection.classList.add('hidden');
                filesSection.classList.remove('hidden');
            }
        } catch (error) {
            clearInterval(progressInterval);
            console.error(error);
            alert('Network error occurred.');
            processingSection.classList.add('hidden');
            filesSection.classList.remove('hidden');
        }
    });
    
    function showResult(data) {
        processingSection.classList.add('hidden');
        resultSection.classList.remove('hidden');
        
        resultDetails.innerHTML = `
            <p><strong>File:</strong> ${data.filename}</p>
            <p><strong>Size:</strong> ${data.size_display}</p>
        `;
        
        downloadBtn.href = `/api/download/${data.filename}/`;
        
        videoPreview.src = `/api/preview/${data.filename}/`;
        videoPreviewContainer.classList.remove('hidden');
    }
    
    startOverBtn.addEventListener('click', () => {
        resultSection.classList.add('hidden');
        pickerContainer.classList.remove('hidden');
        videoPreview.src = '';
        selectedFiles.clear();
        allBuildFiles = [];
    });
    
    // Sort Toggles
    document.getElementById('sortByName').addEventListener('click', (e) => {
        e.target.classList.add('active');
        document.getElementById('sortByDate').classList.remove('active');
        allBuildFiles.sort((a, b) => a.name.localeCompare(b.name));
        renderFilesList();
    });
    
    document.getElementById('sortByDate').addEventListener('click', (e) => {
        e.target.classList.add('active');
        document.getElementById('sortByName').classList.remove('active');
        allBuildFiles.sort((a, b) => a.lastModified - b.lastModified);
        renderFilesList();
    });
    
    function formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB'];
        let i = 0, s = bytes;
        while (s >= 1024 && i < units.length - 1) { s /= 1024; i++; }
        return s.toFixed(1) + ' ' + units[i];
    }
});

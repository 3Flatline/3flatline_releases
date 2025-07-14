/*
 * 3Flatline Vulnerability Scanner
 * Frontend JavaScript
 */

// State management
const appState = {
    files: [],
    selectedFile: null,
    vulnerabilities: [],
    statistics: {},
    currentVulnerability: null,
};

// DOM elements
const elements = {
    // Dashboard stats
    totalTasks: document.getElementById("total-tasks"),
    pendingTasks: document.getElementById("pending-tasks"),
    processingTasks: document.getElementById("processing-tasks"),
    completedTasks: document.getElementById("completed-tasks"),
    failedTasks: document.getElementById("failed-tasks"),
    vulnerabilitiesCount: document.getElementById("vulnerabilities-count"),
    exportMarkdown: document.getElementById("export-markdown"),

    // Scan forms
    scanFileForm: document.getElementById("scan-file-form"),
    filePath: document.getElementById("file-path"),
    scanDirectoryForm: document.getElementById("scan-directory-form"),
    directoryPath: document.getElementById("directory-path"),
    scanProgress: document.getElementById("scan-progress"),
    scanStatusText: document.getElementById("scan-status-text"),
    progressBarFill: document.querySelector(".progress-bar-fill"),

    // Results section
    filesList: document.getElementById("files-list"),
    fileSearch: document.getElementById("file-search"),
    noFileSelected: document.getElementById("no-file-selected"),
    fileVulnerabilities: document.getElementById("file-vulnerabilities"),
    selectedFileName: document.getElementById("selected-file-name"),
    vulnerabilitiesContainer: document.getElementById(
        "vulnerabilities-container",
    ),

    // Modal
    vulnerabilityModal: document.getElementById("vulnerability-modal"),
    modalTitle: document.getElementById("modal-title"),
    modalFilename: document.getElementById("modal-filename"),
    modalFiletype: document.getElementById("modal-filetype"),
    modalVulnClass: document.getElementById("modal-vuln-class"),
    modalDescription: document.getElementById("modal-description"),
    modalChunk: document.getElementById("modal-chunk"),
    modalFix: document.getElementById("modal-fix"),
    closeModal: document.getElementById("close-modal"),
    deleteVulnerability: document.getElementById("delete-vulnerability"),
};

// API endpoints
const API = {
    STATISTICS: "/api/statistics",
    FILES: "/api/files",
    VULNERABILITIES: "/api/vulnerabilities",
    VULNERABILITY: "/api/vulnerability",
    SCAN_FILE: "/scanfile",
    SCAN_DIRECTORY: "/api/scan/directory",
    EXPORT_MARKDOWN: "/api/export/markdown",
};

// Initialize application
function initApp() {
    // Load initial data
    fetchStatistics();
    fetchFiles();

    // Set up event listeners
    setupEventListeners();

    // Set up periodic refresh
    setInterval(fetchStatistics, 10000); // Refresh stats every 10 seconds
}

// Event listeners setup
function setupEventListeners() {
    // Scan file form submission
    elements.scanFileForm.addEventListener("submit", function (e) {
        e.preventDefault();
        scanFile(elements.filePath.value);
    });

    // Scan directory form submission
    elements.scanDirectoryForm.addEventListener("submit", function (e) {
        e.preventDefault();
        scanDirectory(elements.directoryPath.value);
    });

    // File search
    elements.fileSearch.addEventListener("input", function () {
        filterFiles(this.value);
    });

    // Modal close button
    elements.closeModal.addEventListener("click", function () {
        elements.vulnerabilityModal.style.display = "none";
    });

    // Close modal when clicking outside
    window.addEventListener("click", function (e) {
        if (e.target === elements.vulnerabilityModal) {
            elements.vulnerabilityModal.style.display = "none";
        }
    });

    // Delete vulnerability button
    elements.deleteVulnerability.addEventListener("click", function () {
        if (appState.currentVulnerability) {
            deleteVulnerabilityReport(appState.currentVulnerability.GUID);
        }
    });

    // Export to Markdown button
    elements.exportMarkdown.addEventListener("click", function () {
        exportVulnerabilityReportsAsMarkdown();
    });
}

// API Calls

// Fetch dashboard statistics
async function fetchStatistics() {
    try {
        const response = await fetch(API.STATISTICS);
        const data = await response.json();

        appState.statistics = data;
        updateStatistics(data);
    } catch (error) {
        console.error("Error fetching statistics:", error);
    }
}

// Fetch list of scanned files
async function fetchFiles() {
    try {
        const response = await fetch(API.FILES);
        const data = await response.json();

        appState.files = data;
        renderFilesList(data);
    } catch (error) {
        console.error("Error fetching files:", error);
    }
}

// Fetch vulnerabilities for a specific file
async function fetchVulnerabilities(fileName) {
    try {
        const response = await fetch(
            `${API.VULNERABILITIES}?fileName=${encodeURIComponent(fileName)}`,
        );
        const data = await response.json();

        appState.vulnerabilities = data;
        appState.selectedFile = fileName;

        renderVulnerabilities(data, fileName);
    } catch (error) {
        console.error("Error fetching vulnerabilities:", error);
    }
}

// Fetch a specific vulnerability report
async function fetchVulnerabilityReport(guid) {
    try {
        const response = await fetch(`${API.VULNERABILITY}?guid=${guid}`);
        const data = await response.json();

        appState.currentVulnerability = data;
        showVulnerabilityModal(data);
    } catch (error) {
        console.error("Error fetching vulnerability report:", error);
    }
}

// Scan a single file
async function scanFile(filePath) {
    try {
        showProgress(true);
        updateProgress(10, "Starting scan...");

        const response = await fetch(API.SCAN_FILE, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ filePath }),
        });

        const data = await response.json();
        updateProgress(100, "Scan complete!");

        // Refresh data
        setTimeout(() => {
            fetchStatistics();
            fetchFiles();
            showProgress(false);

            // Show a success message
            alert("File scan completed successfully.");
        }, 1000);
    } catch (error) {
        console.error("Error scanning file:", error);
        updateProgress(0, "Scan failed");
        showProgress(false);
        alert(
            "Error scanning file. Please check that the file exists and is accessible.",
        );
    }
}

// Scan a directory
async function scanDirectory(directoryPath) {
    try {
        showProgress(true);
        updateProgress(10, "Starting directory scan...");

        const response = await fetch(API.SCAN_DIRECTORY, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ directoryPath }),
        });

        const data = await response.json();
        updateProgress(100, "Directory scan complete!");

        // Show how many files were scanned
        const scannedCount = data.scannedFiles ? data.scannedFiles.length : 0;

        // Refresh data
        setTimeout(() => {
            fetchStatistics();
            fetchFiles();
            showProgress(false);

            // Show a success message
            alert(`Directory scan completed. Scanned ${scannedCount} files.`);
        }, 1000);
    } catch (error) {
        console.error("Error scanning directory:", error);
        updateProgress(100, "Working");
        fetchStatistics();
        // Forces a reload from the server, bypassing the cache
        location.reload(true);
    }
}

// Delete a vulnerability report
async function deleteVulnerabilityReport(guid) {
    if (
        !confirm("Are you sure you want to delete this vulnerability report?")
    ) {
        return;
    }

    try {
        const response = await fetch(`${API.VULNERABILITY}?guid=${guid}`, {
            method: "DELETE",
        });

        const data = await response.json();

        if (data.success) {
            elements.vulnerabilityModal.style.display = "none";

            // Refresh vulnerability list for the currently selected file
            if (appState.selectedFile) {
                fetchVulnerabilities(appState.selectedFile);
            }

            // Refresh statistics
            fetchStatistics();
        }
    } catch (error) {
        console.error("Error deleting vulnerability report:", error);
        alert("Error deleting vulnerability report.");
    }
}

// Export vulnerability reports as Markdown
async function exportVulnerabilityReportsAsMarkdown() {
    try {
        // Direct the browser to download the file
        window.location.href = API.EXPORT_MARKDOWN;
    } catch (error) {
        console.error("Error exporting vulnerability reports:", error);
        alert("Error exporting vulnerability reports.");
    }
}

// UI Updates

// Update dashboard statistics
function updateStatistics(stats) {
    elements.totalTasks.textContent = stats.total || 0;
    elements.pendingTasks.textContent = stats.pending || 0;
    elements.processingTasks.textContent = stats.processing || 0;
    elements.completedTasks.textContent = stats.completed || 0;
    elements.failedTasks.textContent = stats.failed || 0;
    elements.vulnerabilitiesCount.textContent = stats.vulnerabilities || 0;
}

// Render the list of scanned files
function renderFilesList(files) {
    elements.filesList.innerHTML = "";

    if (files.length === 0) {
        const li = document.createElement("li");
        li.textContent = "No files scanned yet";
        elements.filesList.appendChild(li);
        return;
    }

    files.forEach((file) => {
        const li = document.createElement("li");
        li.textContent = file;
        li.addEventListener("click", () => {
            // Highlight the selected file
            document.querySelectorAll("#files-list li").forEach((el) => {
                el.classList.remove("active");
            });
            li.classList.add("active");

            // Fetch vulnerabilities for this file
            fetchVulnerabilities(file);
        });
        elements.filesList.appendChild(li);
    });
}

// Render vulnerabilities for a file
function renderVulnerabilities(vulnerabilities, fileName) {
    elements.noFileSelected.classList.add("hidden");
    elements.fileVulnerabilities.classList.remove("hidden");
    elements.selectedFileName.textContent = fileName;
    elements.vulnerabilitiesContainer.innerHTML = "";

    if (vulnerabilities.length === 0) {
        const div = document.createElement("div");
        div.className = "placeholder";
        div.innerHTML = `
            <i class="fas fa-check-circle" style="color: var(--success-color);"></i>
            <p>No vulnerabilities found in this file</p>
        `;
        elements.vulnerabilitiesContainer.appendChild(div);
        return;
    }

    vulnerabilities.forEach((vuln) => {
        const card = document.createElement("div");
        card.className = "vulnerability-card";
        card.innerHTML = `
            <h4>${vuln.VulnClass || "Unknown Vulnerability"}</h4>
            <p>${truncateText(vuln.Description || "No description available", 100)}</p>
            <div class="details">
                <span>${vuln.Date || ""} ${vuln.Time || ""}</span>
                <span><i class="fas fa-arrow-right"></i> View Details</span>
            </div>
        `;

        card.addEventListener("click", () => {
            fetchVulnerabilityReport(vuln.GUID);
        });

        elements.vulnerabilitiesContainer.appendChild(card);
    });
}

// Show vulnerability details in modal
function showVulnerabilityModal(vulnerability) {
    elements.modalFilename.textContent =
        vulnerability.FileName || "Unknown File";
    elements.modalFiletype.textContent =
        vulnerability.Extension || "Unknown Type";
    elements.modalVulnClass.textContent =
        vulnerability.VulnClass || "Unknown Vulnerability";
    elements.modalDescription.textContent =
        vulnerability.Description || "No description available";
    elements.modalChunk.textContent =
        vulnerability.ChunkScanned || "No code available";
    elements.modalFix.textContent = vulnerability.Fix || "No fix available";

    elements.vulnerabilityModal.style.display = "block";
}

// Filter files list based on search input
function filterFiles(searchTerm) {
    const items = elements.filesList.getElementsByTagName("li");
    searchTerm = searchTerm.toLowerCase();

    for (let i = 0; i < items.length; i++) {
        const text = items[i].textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            items[i].style.display = "";
        } else {
            items[i].style.display = "none";
        }
    }
}

// Show/hide progress indicator
function showProgress(show) {
    if (show) {
        elements.scanProgress.classList.remove("hidden");
    } else {
        elements.scanProgress.classList.add("hidden");
    }
}

// Update progress bar
function updateProgress(percent, text) {
    elements.progressBarFill.style.width = `${percent}%`;
    elements.scanStatusText.textContent = text;
}

// Helper function to truncate text
function truncateText(text, maxLength) {
    if (!text) return "";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
}

// Initialize the application when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", initApp);

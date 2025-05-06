/**
 * AirGhost Platform Detection and Compatibility Module
 * Handles OS detection, hardware capabilities, and platform-specific features
 */

class PlatformManager {
    constructor() {
        this.systemInfo = null;
        this.wifiInterfaces = [];
        this.compatibilityInfo = {};
        this.missingDependencies = [];
        this.initialized = false;
    }

    /**
     * Initialize the platform manager
     */
    async init() {
        try {
            await this.loadSystemInfo();
            await this.loadCompatibilityInfo();
            await this.loadWifiInterfaces();
            await this.loadMissingDependencies();
            this.initialized = true;
            this.updateUIWithPlatformInfo();
        } catch (error) {
            console.error('Error initializing platform manager:', error);
            showNotification('Error loading platform information', 'error');
        }
    }

    /**
     * Load system information from the server
     */
    async loadSystemInfo() {
        try {
            const response = await fetch('/api/system-info');
            if (!response.ok) throw new Error('Failed to fetch system info');
            const data = await response.json();
            
            if (data.success && data.data) {
                this.systemInfo = data.data;
                console.log('System info loaded:', this.systemInfo);
                return this.systemInfo;
            } else {
                throw new Error(data.error || 'Invalid system info response');
            }
        } catch (error) {
            console.error('Error loading system info:', error);
            // Fallback to browser-based OS detection
            this.systemInfo = this.detectOSFromBrowser();
            return this.systemInfo;
        }
    }

    /**
     * Load compatibility information based on the detected OS
     */
    async loadCompatibilityInfo() {
        if (!this.systemInfo) return;

        try {
            const response = await fetch('/api/compatibility');
            if (!response.ok) throw new Error('Failed to fetch compatibility info');
            const data = await response.json();
            
            if (data.success && data.data) {
                this.compatibilityInfo = data.data;
                console.log('Compatibility info loaded:', this.compatibilityInfo);
                return this.compatibilityInfo;
            } else {
                throw new Error(data.error || 'Invalid compatibility info response');
            }
        } catch (error) {
            console.error('Error loading compatibility info:', error);
            return {};
        }
    }

    /**
     * Load available WiFi interfaces
     */
    async loadWifiInterfaces() {
        try {
            const response = await fetch('/api/wifi-interfaces');
            if (!response.ok) throw new Error('Failed to fetch WiFi interfaces');
            const data = await response.json();
            
            if (data.success && data.data) {
                this.wifiInterfaces = data.data;
                console.log('WiFi interfaces loaded:', this.wifiInterfaces);
                return this.wifiInterfaces;
            } else {
                throw new Error(data.error || 'Invalid WiFi interfaces response');
            }
        } catch (error) {
            console.error('Error loading WiFi interfaces:', error);
            return [];
        }
    }

    /**
     * Load missing dependencies
     */
    async loadMissingDependencies() {
        try {
            const response = await fetch('/api/missing-dependencies');
            if (!response.ok) throw new Error('Failed to fetch missing dependencies');
            const data = await response.json();
            
            if (data.success && data.data) {
                this.missingDependencies = data.data;
                console.log('Missing dependencies loaded:', this.missingDependencies);
                return this.missingDependencies;
            } else {
                throw new Error(data.error || 'Invalid missing dependencies response');
            }
        } catch (error) {
            console.error('Error loading missing dependencies:', error);
            return [];
        }
    }

    /**
     * Fallback OS detection using browser information
     */
    detectOSFromBrowser() {
        const userAgent = navigator.userAgent;
        let os = {
            os_type: 'unknown',
            os_name: 'Unknown OS',
            compatibility: 'unknown'
        };

        if (userAgent.indexOf('Win') !== -1) {
            os.os_type = 'windows';
            os.os_name = 'Windows';
            os.compatibility = 'limited';
        } else if (userAgent.indexOf('Mac') !== -1) {
            os.os_type = 'macos';
            os.os_name = 'macOS';
            os.compatibility = 'partial';
        } else if (userAgent.indexOf('Linux') !== -1) {
            os.os_type = 'linux';
            os.os_name = 'Linux';
            os.compatibility = 'full';
        } else if (userAgent.indexOf('Android') !== -1) {
            os.os_type = 'android';
            os.os_name = 'Android';
            os.compatibility = 'limited';
        } else if (userAgent.indexOf('iOS') !== -1) {
            os.os_type = 'ios';
            os.os_name = 'iOS';
            os.compatibility = 'limited';
        }

        return os;
    }

    /**
     * Update the UI with platform information
     */
    updateUIWithPlatformInfo() {
        if (!this.initialized) return;

        this.updateOSDetectionUI();
        this.updateWifiInterfacesUI();
        this.updateFeatureCompatibilityUI();
        this.updateMissingDependenciesUI();

        // Show notification about platform detection
        const osName = this.systemInfo ? this.systemInfo.os_name : 'Unknown OS';
        const compatLevel = this.systemInfo ? this.systemInfo.compatibility : 'unknown';
        showNotification(`Detected ${osName} with ${this.getCompatibilityText(compatLevel)}`, 'info');
    }

    /**
     * Update OS detection UI
     */
    updateOSDetectionUI() {
        const osDetectionEl = document.getElementById('os-detection');
        if (!osDetectionEl) return;

        if (!this.systemInfo) {
            osDetectionEl.innerHTML = `
                <div class="detection-status detection-unknown">
                    <i class="fas fa-question-circle"></i>
                    <span>OS Detection Failed</span>
                </div>
            `;
            return;
        }

        const osIcon = this.getOSIcon(this.systemInfo.os_type);
        const compatClass = this.getCompatibilityClass(this.systemInfo.compatibility);
        const compatText = this.getCompatibilityText(this.systemInfo.compatibility);

        osDetectionEl.innerHTML = `
            <div class="detection-status detection-success">
                <i class="${osIcon}"></i>
                <div class="detection-info">
                    <span class="os-name">${this.systemInfo.os_name}</span>
                    <span class="compatibility ${compatClass}">${compatText}</span>
                </div>
            </div>
            <div class="os-details">
                <div class="detail-item">
                    <span class="detail-label">Architecture:</span>
                    <span class="detail-value">${this.systemInfo.architecture || 'Unknown'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Package Manager:</span>
                    <span class="detail-value">${this.systemInfo.package_manager || 'Unknown'}</span>
                </div>
            </div>
        `;
    }

    /**
     * Update WiFi interfaces UI
     */
    async updateWifiInterfacesUI() {
        const wifiInterfacesEl = document.getElementById('wifi-interfaces');
        if (!wifiInterfacesEl) return;

        if (!this.wifiInterfaces || this.wifiInterfaces.length === 0) {
            wifiInterfacesEl.innerHTML = `
                <div class="no-interfaces">
                    <i class="fas fa-wifi"></i>
                    <span>No WiFi interfaces detected</span>
                </div>
            `;
            return;
        }

        let interfacesHTML = `
            <div class="interfaces-header">
                <h3>Available WiFi Interfaces</h3>
                <button id="refresh-interfaces" class="refresh-button">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>
            <div class="interfaces-list">
        `;

        this.wifiInterfaces.forEach(iface => {
            const monitorSupported = iface.monitor_supported ? 
                '<span class="feature-supported"><i class="fas fa-check"></i> Monitor Mode</span>' : 
                '<span class="feature-unsupported"><i class="fas fa-times"></i> Monitor Mode</span>';
            
            interfacesHTML += `
                <div class="interface-item" data-interface="${iface.name}">
                    <div class="interface-header">
                        <span class="interface-name">${iface.name}</span>
                        <button class="select-interface" data-interface="${iface.name}">
                            Select
                        </button>
                    </div>
                    <div class="interface-details">
                        <div class="detail-item">
                            <span class="detail-label">MAC:</span>
                            <span class="detail-value">${iface.mac || 'Unknown'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Driver:</span>
                            <span class="detail-value">${iface.driver || 'Unknown'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Features:</span>
                            <div class="detail-value features-list">
                                ${monitorSupported}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        interfacesHTML += `</div>`;
        wifiInterfacesEl.innerHTML = interfacesHTML;

        // Add event listeners
        const refreshBtn = document.getElementById('refresh-interfaces');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', async () => {
                refreshBtn.classList.add('refreshing');
                try {
                    await this.loadWifiInterfaces();
                    this.updateWifiInterfacesUI();
                    showNotification('WiFi interfaces refreshed', 'success');
                } catch (error) {
                    showNotification('Failed to refresh WiFi interfaces', 'error');
                }
                refreshBtn.classList.remove('refreshing');
            });
        }

        // Add event listeners for select interface buttons
        const selectBtns = document.querySelectorAll('.select-interface');
        selectBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const interfaceName = btn.getAttribute('data-interface');
                this.selectInterface(interfaceName);
            });
        });
    }

    /**
     * Update feature compatibility UI
     */
    updateFeatureCompatibilityUI() {
        const featuresEl = document.getElementById('feature-compatibility');
        if (!featuresEl) return;

        if (!this.compatibilityInfo || Object.keys(this.compatibilityInfo).length === 0) {
            featuresEl.innerHTML = `
                <div class="no-compatibility">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Compatibility information not available</span>
                </div>
            `;
            return;
        }

        let featuresHTML = `
            <div class="features-header">
                <h3>Feature Compatibility</h3>
            </div>
            <div class="features-list">
        `;

        // Monitor Mode
        const monitorSupported = this.isFeatureSupported('monitor_mode');
        const monitorClass = monitorSupported ? 'feature-supported' : 'feature-unsupported';
        const monitorIcon = monitorSupported ? 'fa-check' : 'fa-times';
        const monitorInstructions = this.getFeatureInstructions('monitor_mode');

        featuresHTML += `
            <div class="feature-item">
                <div class="feature-header ${monitorClass}">
                    <i class="fas ${monitorIcon}"></i>
                    <span class="feature-name">Monitor Mode</span>
                </div>
                ${monitorInstructions ? `
                <div class="feature-instructions">
                    <pre>${monitorInstructions}</pre>
                </div>
                ` : ''}
            </div>
        `;

        // Packet Injection
        const injectionSupported = this.isFeatureSupported('packet_injection');
        const injectionClass = injectionSupported ? 'feature-supported' : 'feature-unsupported';
        const injectionIcon = injectionSupported ? 'fa-check' : 'fa-times';
        const injectionInstructions = this.getFeatureInstructions('packet_injection');

        featuresHTML += `
            <div class="feature-item">
                <div class="feature-header ${injectionClass}">
                    <i class="fas ${injectionIcon}"></i>
                    <span class="feature-name">Packet Injection</span>
                </div>
                ${injectionInstructions ? `
                <div class="feature-instructions">
                    <pre>${injectionInstructions}</pre>
                </div>
                ` : ''}
            </div>
        `;

        // WiFi Tools
        if (this.compatibilityInfo.wifi_tools) {
            featuresHTML += `
                <div class="feature-item">
                    <div class="feature-header">
                        <i class="fas fa-tools"></i>
                        <span class="feature-name">WiFi Tools</span>
                    </div>
                    <div class="tools-list">
            `;

            for (const [tool, info] of Object.entries(this.compatibilityInfo.wifi_tools)) {
                const toolAvailable = info.available;
                const toolClass = toolAvailable ? 'tool-available' : 'tool-unavailable';
                const toolIcon = toolAvailable ? 'fa-check' : 'fa-times';

                featuresHTML += `
                    <div class="tool-item ${toolClass}">
                        <i class="fas ${toolIcon}"></i>
                        <span class="tool-name">${tool}</span>
                        ${info.version ? `<span class="tool-version">${info.version}</span>` : ''}
                    </div>
                `;
            }

            featuresHTML += `
                    </div>
                </div>
            `;
        }

        featuresHTML += `</div>`;
        featuresEl.innerHTML = featuresHTML;
    }

    /**
     * Update missing dependencies UI
     */
    updateMissingDependenciesUI() {
        const dependenciesEl = document.getElementById('missing-dependencies');
        if (!dependenciesEl) return;

        if (!this.missingDependencies || this.missingDependencies.length === 0) {
            dependenciesEl.innerHTML = `
                <div class="no-dependencies">
                    <i class="fas fa-check-circle"></i>
                    <span>All dependencies are installed</span>
                </div>
            `;
            return;
        }

        let dependenciesHTML = `
            <div class="dependencies-header">
                <h3>Missing Dependencies</h3>
                <button id="install-dependencies" class="install-button">
                    <i class="fas fa-download"></i> Install All
                </button>
            </div>
            <div class="dependencies-list">
        `;

        this.missingDependencies.forEach(dep => {
            dependenciesHTML += `
                <div class="dependency-item">
                    <span class="dependency-name">${dep}</span>
                </div>
            `;
        });

        dependenciesHTML += `</div>`;
        dependenciesEl.innerHTML = dependenciesHTML;

        // Add event listener for install button
        const installBtn = document.getElementById('install-dependencies');
        if (installBtn) {
            installBtn.addEventListener('click', () => {
                this.installMissingDependencies();
            });
        }
    }

    /**
     * Install missing dependencies
     */
    async installMissingDependencies() {
        if (!this.missingDependencies || this.missingDependencies.length === 0) {
            showNotification('No missing dependencies to install', 'info');
            return;
        }

        const installBtn = document.getElementById('install-dependencies');
        if (installBtn) {
            installBtn.disabled = true;
            installBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Installing...';
        }

        try {
            const response = await fetch('/api/install-dependencies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) throw new Error('Failed to install dependencies');
            const data = await response.json();

            if (data.success) {
                showNotification(data.data.message || 'Dependencies installed successfully', 'success');
                await this.loadMissingDependencies();
                this.updateMissingDependenciesUI();
            } else {
                throw new Error(data.error || 'Failed to install dependencies');
            }
        } catch (error) {
            console.error('Error installing dependencies:', error);
            showNotification(`Error installing dependencies: ${error.message}`, 'error');
        } finally {
            if (installBtn) {
                installBtn.disabled = false;
                installBtn.innerHTML = '<i class="fas fa-download"></i> Install All';
            }
        }
    }

    /**
     * Select a WiFi interface
     */
    async selectInterface(interfaceName) {
        if (!interfaceName) return;

        // Find the interface in the list
        const selectedInterface = this.wifiInterfaces.find(iface => iface.name === interfaceName);
        if (!selectedInterface) {
            showNotification(`Interface ${interfaceName} not found`, 'error');
            return;
        }

        try {
            const response = await fetch('/api/select-interface', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ interface: interfaceName })
            });

            if (!response.ok) throw new Error('Failed to select interface');
            const data = await response.json();

            if (data.success) {
                // Update UI to show selected interface
                const interfaceItems = document.querySelectorAll('.interface-item');
                interfaceItems.forEach(item => {
                    item.classList.remove('selected');
                    if (item.getAttribute('data-interface') === interfaceName) {
                        item.classList.add('selected');
                    }
                });

                showNotification(`Interface ${interfaceName} selected`, 'success');
            } else {
                throw new Error(data.error || 'Failed to select interface');
            }
        } catch (error) {
            console.error('Error selecting interface:', error);
            showNotification(`Error selecting interface: ${error.message}`, 'error');
        }
    }

    /**
     * Check if a feature is supported based on compatibility info
     */
    isFeatureSupported(feature) {
        if (!this.compatibilityInfo) return false;

        if (feature === 'monitor_mode') {
            return this.compatibilityInfo.monitor_mode && 
                   this.compatibilityInfo.monitor_mode.supported === true;
        }

        if (feature === 'packet_injection') {
            return this.compatibilityInfo.packet_injection && 
                   this.compatibilityInfo.packet_injection.supported === true;
        }

        return false;
    }

    /**
     * Get instructions for a feature
     */
    getFeatureInstructions(feature) {
        if (!this.compatibilityInfo) return '';

        if (feature === 'monitor_mode') {
            if (this.compatibilityInfo.monitor_mode && 
                this.compatibilityInfo.monitor_mode.instructions) {
                return this.compatibilityInfo.monitor_mode.instructions;
            }
        }
        
        if (feature === 'packet_injection') {
            if (this.compatibilityInfo.packet_injection && 
                this.compatibilityInfo.packet_injection.instructions) {
                return this.compatibilityInfo.packet_injection.instructions;
            }
        }
        
        return '';
    }

    /**
     * Get OS icon class based on OS type
     */
    getOSIcon(osType) {
        switch (osType) {
            case 'macos':
                return 'fab fa-apple';
            case 'windows':
                return 'fab fa-windows';
            case 'linux':
            case 'kali':
            case 'ubuntu':
            case 'debian':
            case 'arch':
            case 'fedora':
                return 'fab fa-linux';
            case 'android':
                return 'fab fa-android';
            default:
                return 'fas fa-desktop';
        }
    }

    /**
     * Get compatibility class based on compatibility level
     */
    getCompatibilityClass(compatibility) {
        switch (compatibility) {
            case 'full':
                return 'compatibility-full';
            case 'partial':
                return 'compatibility-partial';
            case 'limited':
                return 'compatibility-limited';
            default:
                return 'compatibility-unknown';
        }
    }

    /**
     * Get compatibility text based on compatibility level
     */
    getCompatibilityText(compatibility) {
        switch (compatibility) {
            case 'full':
                return 'Full Compatibility';
            case 'partial':
                return 'Partial Compatibility';
            case 'limited':
                return 'Limited Compatibility';
            default:
                return 'Unknown Compatibility';
        }
    }
}

/**
 * Show a notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${getNotificationIcon(type)}"></i>
        </div>
        <div class="notification-content">
            ${message}
        </div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Add animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Add event listener for close button
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Auto-close after 5 seconds for non-error notifications
    if (type !== 'error') {
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
}

/**
 * Get notification icon based on type
 */
function getNotificationIcon(type) {
    switch (type) {
        case 'success':
            return 'fa-check-circle';
        case 'error':
            return 'fa-exclamation-circle';
        case 'warning':
            return 'fa-exclamation-triangle';
        case 'info':
        default:
            return 'fa-info-circle';
    }
}

// Initialize platform manager when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.platformManager = new PlatformManager();
    window.platformManager.init();
});

/**
 * AirGhost - WiFi Penetration Testing Platform
 * Main JavaScript for the web interface
 */

// Global variables
let socket;
let currentPage = 'dashboard';
let scanningNetworks = false;
let networksList = [];
let activeAttacks = {};
let systemStatus = {
    ap_running: false,
    dhcp_running: false,
    interfaces: {}
};

// DOM ready
$(document).ready(function() {
    // Initialize Socket.io
    initializeSocketIO();
    
    // Set up navigation
    setupNavigation();
    
    // Set up interface selector
    updateInterfaceSelector();
    
    // Set up event handlers
    setupEventHandlers();
    
    // Load initial data
    loadSystemStatus();
    
    // Update timestamps every minute
    setInterval(updateTimestamps, 60000);
});

/**
 * Initialize Socket.io connection
 */
function initializeSocketIO() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        showNotification('Connected to server', 'success');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        showNotification('Disconnected from server', 'error');
    });
    
    socket.on('status_update', function(data) {
        console.log('Status update:', data);
        systemStatus = data;
        updateStatusIndicators();
        updateInterfaceTable();
    });
    
    socket.on('attack_update', function(data) {
        console.log('Attack update:', data);
        updateActiveAttacks(data);
    });
    
    socket.on('log_update', function(data) {
        console.log('Log update:', data);
        updateLogs(data);
    });
    
    socket.on('credential_capture', function(data) {
        console.log('Credential captured:', data);
        updateCredentialCapture(data);
    });
}

/**
 * Set up navigation between pages
 */
function setupNavigation() {
    $('.nav-links li').on('click', function() {
        const page = $(this).data('page');
        navigateTo(page);
    });
}

/**
 * Navigate to a specific page
 * @param {string} page - The page to navigate to
 */
function navigateTo(page) {
    // Hide all pages
    $('.page-content').addClass('hidden');
    
    // Show selected page
    $(`#${page}-page`).removeClass('hidden');
    
    // Update active navigation
    $('.nav-links li').removeClass('active');
    $(`.nav-links li[data-page="${page}"]`).addClass('active');
    
    // Update page title
    $('#page-title').text(page.charAt(0).toUpperCase() + page.slice(1));
    
    // Store current page
    currentPage = page;
    
    // Special actions for specific pages
    if (page === 'networks') {
        if (networksList.length === 0) {
            $('#no-networks-row').show();
        } else {
            $('#no-networks-row').hide();
        }
    }
}

/**
 * Set up event handlers for buttons and forms
 */
function setupEventHandlers() {
    // Refresh button
    $('#refresh-btn').on('click', function() {
        loadSystemStatus();
    });
    
    // Interface selector change
    $('#interface-select').on('change', function() {
        const selectedInterface = $(this).val();
        console.log('Selected interface:', selectedInterface);
        // Save the selected interface to localStorage
        localStorage.setItem('selectedInterface', selectedInterface);
    });
    
    // Scan networks button
    $('#scan-btn').on('click', function() {
        scanWifiNetworks();
    });
    
    // Evil Twin form events
    $('#et-security').on('change', function() {
        if ($(this).is(':checked')) {
            $('#et-password-group').show();
        } else {
            $('#et-password-group').hide();
        }
    });
    
    $('#start-et-btn').on('click', function() {
        startEvilTwinAttack();
    });
    
    $('#stop-et-btn').on('click', function() {
        stopAttack('evil_twin');
    });
    
    // Captive Portal form events
    $('#start-cp-btn').on('click', function() {
        startCaptivePortalAttack();
    });
    
    $('#stop-cp-btn').on('click', function() {
        stopAttack('captive_portal');
    });
    
    // Deauthentication form events
    $('#start-deauth-btn').on('click', function() {
        startDeauthAttack();
    });
    
    $('#stop-deauth-btn').on('click', function() {
        stopAttack('deauth');
    });
    
    // Settings form events
    $('#save-settings-btn').on('click', function() {
        saveSettings();
    });
    
    // Network modal actions
    $(document).on('click', '.action-btn', function() {
        const action = $(this).data('action');
        const networkIndex = $(this).data('index');
        
        if (networkIndex >= 0 && networkIndex < networksList.length) {
            const network = networksList[networkIndex];
            openNetworkModal(network, action);
        }
    });
    
    // Modal action buttons
    $('#modal-deauth-btn').on('click', function() {
        const bssid = $('#modal-bssid').text();
        $('#deauth-bssid').val(bssid);
        $('#network-modal').removeClass('show');
        navigateTo('deauth');
    });
    
    $('#modal-eviltwin-btn').on('click', function() {
        const ssid = $('#modal-ssid').text();
        const bssid = $('#modal-bssid').text();
        const channel = $('#modal-channel').text();
        
        $('#et-ssid').val(ssid);
        $('#et-bssid').val(bssid);
        $('#et-channel').val(channel);
        
        $('#network-modal').removeClass('show');
        navigateTo('evil-twin');
    });
    
    $('#modal-captive-btn').on('click', function() {
        const ssid = $('#modal-ssid').text();
        $('#cp-ssid').val(ssid);
        
        $('#network-modal').removeClass('show');
        navigateTo('captive-portal');
    });
    
    // Close modal
    $('.close, .modal-footer button').on('click', function() {
        $('#network-modal').removeClass('show');
    });
    
    // Clear logs button
    $('#clear-logs-btn').on('click', function() {
        $('#system-logs').val('');
    });
}

/**
 * Load system status from server
 */
function loadSystemStatus() {
    $.get('/status', function(data) {
        systemStatus = data;
        updateStatusIndicators();
        updateInterfaceSelector();
        updateInterfaceTable();
    });
}

/**
 * Update the interface selector dropdown
 */
function updateInterfaceSelector() {
    $.get('/interfaces', function(data) {
        const $select = $('#interface-select');
        const $defaultInterface = $('#default-interface');
        const selectedInterface = localStorage.getItem('selectedInterface');
        
        $select.empty();
        $defaultInterface.empty();
        
        Object.keys(data).forEach(function(interface) {
            const info = data[interface];
            const option = `<option value="${interface}">${interface} (${info.mac})</option>`;
            $select.append(option);
            $defaultInterface.append(option);
        });
        
        if (selectedInterface && $select.find(`option[value="${selectedInterface}"]`).length > 0) {
            $select.val(selectedInterface);
        }
    });
}

/**
 * Update status indicators in the sidebar
 */
function updateStatusIndicators() {
    // AP status
    if (systemStatus.ap_running) {
        $('#ap-status').html('<i class="fas fa-circle status-indicator online"></i> Online');
    } else {
        $('#ap-status').html('<i class="fas fa-circle status-indicator offline"></i> Offline');
    }
    
    // DHCP status
    if (systemStatus.dhcp_running) {
        $('#dhcp-status').html('<i class="fas fa-circle status-indicator online"></i> Online');
    } else {
        $('#dhcp-status').html('<i class="fas fa-circle status-indicator offline"></i> Offline');
    }
}

/**
 * Update the interface table on the dashboard
 */
function updateInterfaceTable() {
    const $table = $('#interface-table');
    $table.empty();
    
    Object.keys(systemStatus.interfaces).forEach(function(interface) {
        const info = systemStatus.interfaces[interface];
        const row = `
        <tr>
            <td>${interface}</td>
            <td>${info.mac}</td>
            <td>${info.mode}</td>
            <td>${info.channel}</td>
            <td><span class="${info.status === 'Up' ? 'text-success' : 'text-danger'}">${info.status}</span></td>
        </tr>
        `;
        $table.append(row);
    });
}

/**
 * Scan for WiFi networks
 */
function scanWifiNetworks() {
    if (scanningNetworks) {
        return;
    }
    
    const selectedInterface = $('#interface-select').val();
    
    if (!selectedInterface) {
        showNotification('No interface selected', 'error');
        return;
    }
    
    scanningNetworks = true;
    showNotification('Scanning for networks...', 'info');
    
    $('#scanning-indicator').removeClass('hidden');
    $('#networks-list').addClass('hidden');
    
    $.ajax({
        url: '/scan',
        type: 'POST',
        data: JSON.stringify({
            interface: selectedInterface
        }),
        contentType: 'application/json',
        success: function(data) {
            scanningNetworks = false;
            $('#scanning-indicator').addClass('hidden');
            $('#networks-list').removeClass('hidden');
            
            if (data.success) {
                networksList = data.networks;
                updateNetworksTable();
            } else {
                showNotification(data.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            scanningNetworks = false;
            $('#scanning-indicator').addClass('hidden');
            $('#networks-list').removeClass('hidden');
            showNotification('Error scanning networks: ' + error, 'error');
        }
    });
}

/**
 * Update the networks table with scan results
 */
function updateNetworksTable() {
    const $table = $('#networks-table');
    $table.empty();
    
    if (networksList.length === 0) {
        $table.append('<tr id="no-networks-row"><td colspan="6" class="text-center">No networks found</td></tr>');
        return;
    }
    
    networksList.forEach(function(network, index) {
        // Convert signal strength to readable format
        const signal = parseInt(network.power);
        let signalStrength = 'Unknown';
        let signalClass = '';
        
        if (!isNaN(signal)) {
            if (signal > -50) {
                signalStrength = 'Excellent';
                signalClass = 'text-success';
            } else if (signal > -60) {
                signalStrength = 'Good';
                signalClass = 'text-success';
            } else if (signal > -70) {
                signalStrength = 'Fair';
                signalClass = 'text-warning';
            } else {
                signalStrength = 'Poor';
                signalClass = 'text-danger';
            }
        }
        
        const row = `
        <tr>
            <td>${network.essid || '<Hidden>'}</td>
            <td>${network.bssid}</td>
            <td>${network.channel}</td>
            <td>${network.privacy}</td>
            <td class="${signalClass}">${signalStrength} (${network.power})</td>
            <td>
                <button class="btn btn-sm btn-primary action-btn" data-action="view" data-index="${index}">
                    <i class="fas fa-ellipsis-h"></i>
                </button>
            </td>
        </tr>
        `;
        $table.append(row);
    });
}

/**
 * Open the network actions modal
 * @param {object} network - The network data
 * @param {string} action - The action to perform
 */
function openNetworkModal(network, action) {
    $('#modal-ssid').text(network.essid || '<Hidden>');
    $('#modal-bssid').text(network.bssid);
    $('#modal-channel').text(network.channel);
    $('#modal-security').text(network.privacy);
    
    $('#network-modal').addClass('show');
}

/**
 * Start an Evil Twin attack
 */
function startEvilTwinAttack() {
    const ssid = $('#et-ssid').val();
    const bssid = $('#et-bssid').val();
    const channel = $('#et-channel').val();
    const security = $('#et-security').is(':checked');
    const password = $('#et-password').val();
    const deauth = $('#et-deauth').is(':checked');
    const selectedInterface = $('#interface-select').val();
    
    if (!ssid) {
        showNotification('SSID is required', 'error');
        return;
    }
    
    if (security && (!password || password.length < 8)) {
        showNotification('WPA2 Password must be at least 8 characters', 'error');
        return;
    }
    
    const params = {
        ssid: ssid,
        interface: selectedInterface,
        channel: channel,
        security: security,
        password: password,
        deauth: deauth
    };
    
    if (bssid) {
        params.bssid = bssid;
    }
    
    $.ajax({
        url: '/attack/start',
        type: 'POST',
        data: JSON.stringify({
            type: 'evil_twin',
            params: params
        }),
        contentType: 'application/json',
        success: function(data) {
            if (data.success) {
                showNotification('Evil Twin attack started', 'success');
                $('#start-et-btn').prop('disabled', true);
                $('#stop-et-btn').prop('disabled', false);
            } else {
                showNotification(data.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            showNotification('Error starting attack: ' + error, 'error');
        }
    });
}

/**
 * Start a Captive Portal attack
 */
function startCaptivePortalAttack() {
    const ssid = $('#cp-ssid').val();
    const template = $('#cp-template').val();
    const channel = $('#cp-channel').val();
    const deauth = $('#cp-deauth').is(':checked');
    const selectedInterface = $('#interface-select').val();
    
    if (!ssid) {
        showNotification('SSID is required', 'error');
        return;
    }
    
    const params = {
        ssid: ssid,
        template: template,
        interface: selectedInterface,
        channel: channel,
        deauth: deauth
    };
    
    $.ajax({
        url: '/attack/start',
        type: 'POST',
        data: JSON.stringify({
            type: 'captive_portal',
            params: params
        }),
        contentType: 'application/json',
        success: function(data) {
            if (data.success) {
                showNotification('Captive Portal attack started', 'success');
                $('#start-cp-btn').prop('disabled', true);
                $('#stop-cp-btn').prop('disabled', false);
            } else {
                showNotification(data.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            showNotification('Error starting attack: ' + error, 'error');
        }
    });
}

/**
 * Start a Deauthentication attack
 */
function startDeauthAttack() {
    const bssid = $('#deauth-bssid').val();
    const client = $('#deauth-client').val();
    const count = $('#deauth-count').val();
    const selectedInterface = $('#interface-select').val();
    
    if (!bssid) {
        showNotification('Target BSSID is required', 'error');
        return;
    }
    
    const params = {
        bssid: bssid,
        interface: selectedInterface,
        count: count
    };
    
    if (client) {
        params.client = client;
    }
    
    $.ajax({
        url: '/attack/start',
        type: 'POST',
        data: JSON.stringify({
            type: 'deauth',
            params: params
        }),
        contentType: 'application/json',
        success: function(data) {
            if (data.success) {
                showNotification('Deauthentication attack started', 'success');
                $('#start-deauth-btn').prop('disabled', true);
                $('#stop-deauth-btn').prop('disabled', false);
            } else {
                showNotification(data.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            showNotification('Error starting attack: ' + error, 'error');
        }
    });
}

/**
 * Stop an attack
 * @param {string} attackType - The type of attack to stop
 */
function stopAttack(attackType) {
    $.ajax({
        url: '/attack/stop',
        type: 'POST',
        data: JSON.stringify({
            type: attackType
        }),
        contentType: 'application/json',
        success: function(data) {
            if (data.success) {
                showNotification(`${attackType.replace('_', ' ')} attack stopped`, 'success');
                
                if (attackType === 'evil_twin') {
                    $('#start-et-btn').prop('disabled', false);
                    $('#stop-et-btn').prop('disabled', true);
                } else if (attackType === 'captive_portal') {
                    $('#start-cp-btn').prop('disabled', false);
                    $('#stop-cp-btn').prop('disabled', true);
                } else if (attackType === 'deauth') {
                    $('#start-deauth-btn').prop('disabled', false);
                    $('#stop-deauth-btn').prop('disabled', true);
                }
            } else {
                showNotification(data.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            showNotification('Error stopping attack: ' + error, 'error');
        }
    });
}

/**
 * Save system settings
 */
function saveSettings() {
    const defaultInterface = $('#default-interface').val();
    const apIp = $('#ap-ip').val();
    const dhcpStart = $('#dhcp-start').val();
    const dhcpEnd = $('#dhcp-end').val();
    const internetSharing = $('#internet-sharing').is(':checked');
    
    const settings = {
        default_interface: defaultInterface,
        ap_ip: apIp,
        dhcp_start: dhcpStart,
        dhcp_end: dhcpEnd,
        internet_sharing: internetSharing
    };
    
    $.ajax({
        url: '/config/settings',
        type: 'POST',
        data: JSON.stringify(settings),
        contentType: 'application/json',
        success: function(data) {
            if (data.success) {
                showNotification('Settings saved successfully', 'success');
            } else {
                showNotification(data.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            showNotification('Error saving settings: ' + error, 'error');
        }
    });
}

/**
 * Update active attacks display
 * @param {object} data - The attack data
 */
function updateActiveAttacks(data) {
    activeAttacks = data;
    
    const $table = $('#attacks-table');
    
    // Clear the table except for the "no attacks" row
    $table.find('tr:not(#no-attacks-row)').remove();
    
    if (Object.keys(activeAttacks).length === 0) {
        $('#no-attacks-row').show();
        return;
    }
    
    $('#no-attacks-row').hide();
    
    Object.keys(activeAttacks).forEach(function(attackType) {
        const attack = activeAttacks[attackType];
        
        if (!attack.process) {
            return;
        }
        
        const startTime = new Date(attack.start_time * 1000);
        const duration = formatDuration(Math.floor((Date.now() / 1000) - attack.start_time));
        
        let target = '';
        if (attackType === 'evil_twin' || attackType === 'captive_portal') {
            target = attack.params.ssid;
        } else if (attackType === 'deauth') {
            target = attack.params.bssid;
        }
        
        const row = `
        <tr>
            <td>${attackType.replace('_', ' ')}</td>
            <td>${target}</td>
            <td>${duration}</td>
            <td><span class="text-success">Running</span></td>
            <td>
                <button class="btn btn-sm btn-danger stop-attack-btn" data-type="${attackType}">
                    <i class="fas fa-stop"></i> Stop
                </button>
            </td>
        </tr>
        `;
        $table.append(row);
    });
    
    // Add event handlers to stop buttons
    $('.stop-attack-btn').on('click', function() {
        const attackType = $(this).data('type');
        stopAttack(attackType);
    });
}

/**
 * Update logs display
 * @param {object} data - The log data
 */
function updateLogs(data) {
    const $logs = $('#system-logs');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${data.level}: ${data.message}\n`;
    
    // Append to logs and scroll to bottom
    $logs.val($logs.val() + logEntry);
    $logs.scrollTop($logs[0].scrollHeight);
}

/**
 * Update captured credentials display
 * @param {object} data - The credential data
 */
function updateCredentialCapture(data) {
    const $logs = $('#cp-logs');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${data.username}:${data.password}\n`;
    
    // Append to logs and scroll to bottom
    $logs.val($logs.val() + logEntry);
    $logs.scrollTop($logs[0].scrollHeight);
    
    // Show notification
    showNotification('New credentials captured!', 'success');
}

/**
 * Update timestamps for ongoing attacks
 */
function updateTimestamps() {
    if (Object.keys(activeAttacks).length > 0) {
        updateActiveAttacks(activeAttacks);
    }
}

/**
 * Format duration in seconds to human-readable string
 * @param {number} seconds - Duration in seconds
 * @returns {string} - Formatted duration
 */
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

/**
 * Show a notification
 * @param {string} message - The notification message
 * @param {string} type - The notification type (success, error, warning, info)
 */
function showNotification(message, type) {
    const $container = $('#notification-container');
    const id = 'notification-' + Date.now();
    
    let icon = '';
    switch (type) {
        case 'success':
            icon = '<i class="fas fa-check-circle"></i>';
            break;
        case 'error':
            icon = '<i class="fas fa-exclamation-circle"></i>';
            break;
        case 'warning':
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            break;
        case 'info':
            icon = '<i class="fas fa-info-circle"></i>';
            break;
    }
    
    const notification = `
    <div id="${id}" class="notification ${type}">
        <span class="notification-icon">${icon}</span>
        <span class="notification-message">${message}</span>
        <span class="notification-close">&times;</span>
    </div>
    `;
    
    $container.append(notification);
    
    // Add close event
    $(`#${id} .notification-close`).on('click', function() {
        $(`#${id}`).remove();
    });
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        $(`#${id}`).fadeOut(300, function() {
            $(this).remove();
        });
    }, 5000);
}

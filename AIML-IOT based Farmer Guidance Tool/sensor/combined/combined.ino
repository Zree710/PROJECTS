#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

#define MOISTURE_SENSOR_PIN 34  // Connect soil moisture sensor to GPIO34
#define DHTPIN 4  // Connect DHT11 data pin to GPIO4
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Zree";  // 🔥 Replace with your WiFi SSID
const char* password = "qwertyuiop";  // 🔥 Replace with your WiFi password
const char* serverUrl = "http://192.168.131.182:5000/api/moisture"; // 🔥 Replace with backend IP

// Define sensor dry/wet values (calibrate these for your soil)
#define DRY_VALUE 4095    // Sensor reading in **completely dry soil**
#define WET_VALUE 2000    // Sensor reading in **fully wet soil**

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  dht.begin();

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    int rawMoisture = analogRead(MOISTURE_SENSOR_PIN); // Read moisture sensor value
    Serial.print("Raw Moisture Value: ");
    Serial.println(rawMoisture);

    // 🔥 Convert Raw Value to Percentage
    int moisturePercentage = map(rawMoisture, DRY_VALUE, WET_VALUE, 0, 100);
    moisturePercentage = constrain(moisturePercentage, 0, 100); // Keep within 0-100%

    Serial.print("Moisture Percentage: ");
    Serial.print(moisturePercentage);
    Serial.println("%");

    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.print("%  Temperature: ");
    Serial.print(temperature);
    Serial.println("°C");

    String postData = "moisture=" + String(rawMoisture) + "&humidity=" + String(humidity) + "&temperature=" + String(temperature);

    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    int httpResponseCode = http.POST(postData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Server Response: " + response);
    } else {
      Serial.print("Error in sending POST request: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }
  delay(5000); // Wait 5 seconds before next reading
}

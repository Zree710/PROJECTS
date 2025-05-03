from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

moisture_percentage = 0
temperature = 0.0
humidity = 0.0

# ✅ API 1: Receive Soil Moisture, Temperature, and Humidity Data from ESP32
@app.route('/api/moisture', methods=['POST'])
def receive_moisture():
    global moisture_percentage, temperature, humidity
    try:
        data = request.json
        print("Received raw data:", data)  # 🔥 Log incoming data
        if "moisture" in data and "temperature" in data and "humidity" in data:
            moisture_percentage = data["moisture"]
            temperature = data["temperature"]
            humidity = data["humidity"]
            print(f"Received data -> Moisture: {moisture_percentage}%, Temperature: {temperature}°C, Humidity: {humidity}%")
            return jsonify({"message": "Sensor data received"}), 200
        else:
            print("Invalid Data Format")  # Debugging 
            return jsonify({"error": "Invalid data"}), 400
    except Exception as e:
        print("Error:", str(e))  # Debugging
        return jsonify({"error": str(e)}), 500

# ✅ API 2: Provide Real-Time Sensor Data to Frontend
@app.route('/api/moisture', methods=['GET'])
def get_moisture():
    return jsonify({
        "moisture": moisture_percentage,
        "temperature": temperature,
        "humidity": humidity
    })

@app.route('/api/recommendations', methods=['POST'])
def get_recommendation():
    try:
        data = request.json

        # Validate input data
        required_fields = ["nitrogen", "phosphorus", "potassium", "ph", "rainfall", "temperature", "humidity", "soilMoisture"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "All fields are required"}), 400

        # Convert input values to float
        for key in data:
            data[key] = float(data[key])

        # Generate recommendations
        recommendations = generate_recommendations(data)

        return jsonify(recommendations)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_recommendations(data):
    nitrogen, phosphorus, potassium, ph, rainfall, temperature, humidity, soilMoisture = (
        data["nitrogen"], data["phosphorus"], data["potassium"], data["ph"], 
        data["rainfall"], data["temperature"], data["humidity"], data["soilMoisture"]
    )

    # Initialize recommendations
    recommendations = {
        "suitableCrops": [],
        "fertilizerRecommendations": {},
        "soilHealth": "",
        "irrigationAdvice": "",
        "additionalNotes": []
    }

    # Crop recommendation
    api_url = "http://127.0.0.1:5001/api/recommendations"  # Replace with actual API endpoint
    response = requests.post(api_url, json=data)
    recommendations["suitableCrops"] = response.json()
    # Ensure the API always returns an array ✅ (Add this fix)
    if isinstance(recommendations["suitableCrops"], dict):
        recommendations["suitableCrops"] = list(recommendations["suitableCrops"].values())
    elif not isinstance(recommendations["suitableCrops"], list):
        recommendations["suitableCrops"] = [recommendations["suitableCrops"]]

    # Determine soil health
    if nitrogen < 30 or phosphorus < 30 or potassium < 30:
        recommendations["soilHealth"] = "Poor"
    elif nitrogen < 60 or phosphorus < 60 or potassium < 60:
        recommendations["soilHealth"] = "Moderate"
    else:
        recommendations["soilHealth"] = "Good"

    # Soil pH
    if ph < 5.5:
        recommendations["additionalNotes"].append("Your soil is acidic. Consider adding lime to raise pH.")
    elif 5.5 <= ph < 6.5:
        recommendations["additionalNotes"].append("Your soil is slightly acidic.")
    elif 6.5 <= ph < 7.5:
        recommendations["additionalNotes"].append("Your soil is neutral.")
    else:
        recommendations["additionalNotes"].append("Your soil is alkaline. Consider adding sulfur to lower pH.")

    # Crops based on temperature
    if temperature > 30:
        recommendations["additionalNotes"].append("High temperatures detected. Focus on heat-tolerant crops.")
    elif temperature < 15:
        recommendations["additionalNotes"].append("Cool temperatures detected. Focus on cold-tolerant crops.")

    # Fertilizer recommendations
    recommendations["fertilizerRecommendations"] = {
        "nitrogen": f"Add {50 - nitrogen} kg/ha of nitrogen fertilizer" if nitrogen < 50 else "Nitrogen levels are sufficient",
        "phosphorus": f"Add {50 - phosphorus} kg/ha of phosphorus fertilizer" if phosphorus < 50 else "Phosphorus levels are sufficient",
        "potassium": f"Add {50 - potassium} kg/ha of potassium fertilizer" if potassium < 50 else "Potassium levels are sufficient"
    }

    # Irrigation advice
    if soilMoisture < 30:
        recommendations["irrigationAdvice"] = "Soil is dry. Increase irrigation frequency."
    elif soilMoisture > 70:
        recommendations["irrigationAdvice"] = "Soil is very moist. Reduce irrigation to prevent waterlogging."
    else:
        recommendations["irrigationAdvice"] = "Soil moisture is optimal. Maintain current irrigation schedule."

    # Ensure at least one crop is recommended
    if not recommendations["suitableCrops"]:
        recommendations["suitableCrops"] = ["No ideal crops found"]
        recommendations["additionalNotes"].append("Consider greenhouse cultivation or soil amendments.")

    return recommendations

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)  # 🔥 Allows access from ESP32

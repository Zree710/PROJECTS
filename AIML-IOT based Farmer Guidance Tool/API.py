from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Load trained XGBoost model
with open("xgboost_crop_model.pkl", "rb") as f:
    model = pickle.load(f)

# Load Label Encoder for crop names
with open("label_encoder.pkl", "rb") as f:
    le = pickle.load(f)

@app.route('/api/recommendations', methods=['POST'])
def get_recommendation():
    try:
        data = request.json

        # Validate input data
        required_fields = ["nitrogen", "phosphorus", "potassium", "ph", "rainfall", "temperature", "humidity", "soilMoisture"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "All fields are required"}), 400

        # Convert input values to float
        input_features = np.array([
            float(data["ph"]), float(data["nitrogen"]), float(data["phosphorus"]), float(data["potassium"]),
            float(data["rainfall"]), float(data["temperature"]), float(data["humidity"]), float(data["soilMoisture"])
        ]).reshape(1, -1)

        # Handle extreme cases where no crop can grow
        if float(data["temperature"]) > 55:
          return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Extreme heat detected (>55°C). No crops can survive."})

        if float(data["soilMoisture"]) < 2:
          return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Extremely dry soil detected (<2%). No crops can survive."})

        if float(data["rainfall"]) < 5 and float(data["temperature"]) > 50:
          return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Very low rainfall (<5mm) and extreme heat (>50°C). No crops can survive."})

        if float(data["temperature"]) < 0:
            return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Extreme cold detected (<0°C). No crops can survive."})

        if float(data["soilMoisture"]) > 90:
            return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Excessive water detected (>90%). No crops can survive."})

        if float(data["ph"]) < 4.5 or float(data["ph"]) > 9.0:
            return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Unsuitable soil pH detected (<4.5 or >9.0). No crops can survive."})

        if float(data["nitrogen"]) > 80 and float(data["phosphorus"]) < 10 and float(data["potassium"]) < 10:
            return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Nitrogen toxicity detected (>80). No crops can survive."})

        if float(data["phosphorus"]) > 80 and float(data["nitrogen"]) < 10 and float(data["potassium"]) < 10:
            return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Phosphorus toxicity detected (>80). No crops can survive."})

        if float(data["potassium"]) > 80 and float(data["nitrogen"]) < 10 and float(data["phosphorus"]) < 10:
            return jsonify({"recommendedCrop": "No Growth Possible", "reason": "Potassium toxicity detected (>80). No crops can survive."})









        # Make prediction using the trained model
        prediction = model.predict(input_features)
        recommended_crop = le.inverse_transform(prediction)[0]  # Convert label to crop name

        return jsonify({"recommendedCrop": recommended_crop})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

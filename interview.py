from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

genai.configure(api_key="AIzaSyBRnWsaXoX30zdpLClvJ78VjSyDFPTdFvU")
model = genai.GenerativeModel("gemini-2.0-flash")

@app.route("/")
def index():
    return render_template("interview.html")  # Serves your HTML

@app.route("/api/analyze", methods=["POST"])
def analyze_text():
    data = request.json
    text = data.get("text")
    input_type = data.get("type", "general")

    if not text:
        return jsonify({"error": "No input provided"}), 400

    prompt = f"Please review and provide feedback on this {input_type}:\n\n{text}"

    try:
        response = model.generate_content(prompt)
        return jsonify({"feedback": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

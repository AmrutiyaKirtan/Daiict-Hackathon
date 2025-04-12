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

    prompt = (
        f"You're an expert communication coach. "
        f"Please provide a brief (3-4 points) professional review of the following {input_type}.each point should be in a new line and should be 15 words long"
        f"Focus on tone, clarity, grammar, and effectiveness. each point should be in a new line. and begin with a number\n\n"
        f"---\n{text}\n---"
        f"Be specific but concise.\n\n"
        f"---\n{text}\n---"
    )

    try:
        response = model.generate_content(prompt)
        return jsonify({"feedback": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

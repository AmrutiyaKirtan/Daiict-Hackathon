from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from PIL import Image
import fitz  # PyMuPDF
import os
import uuid
import socket

app = Flask(__name__, template_folder='.')
# Enable CORS for all routes - this allows requests from any origin
CORS(app, supports_credentials=True)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Set your Gemini API key
GEMINI_API_KEY = "AIzaSyBRnWsaXoX30zdpLClvJ78VjSyDFPTdFvU"
client = genai.Client(api_key=GEMINI_API_KEY)

def get_first_page_image(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        doc = fitz.open(file_path)
        page = doc.load_page(0)
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return image
    elif ext in ['.png', '.jpg', '.jpeg']:
        return Image.open(file_path)
    elif ext in ['.doc', '.docx']:
        # For handling Word documents, you might need additional libraries
        # This is a placeholder for docx conversion to image
        # You could use docx2pdf or other libraries for this conversion
        # For now, we'll raise an error
        raise ValueError("Word document processing not implemented yet")
    else:
        raise ValueError("Unsupported file format")

def analyze_resume(image):
    review_prompt = """
    You are a resume reviewing expert. Please review the attached resume image based on the following parameters:

    1. **Spelling and Grammar**: Point out any spelling or grammatical errors.
    2. **ATS-Friendliness**: Evaluate if the resume is likely to be parsed correctly by an Applicant Tracking System (ATS).
    3. **Use of Action Words**: Check if the resume uses strong, industry-approved action words (refer to Harvard's action word list).
    4. **Structure and Formatting**: Comment on the layout, font consistency, white space, section headers, and overall readability.
    5. **Professional Tone**: Evaluate the tone and language of the resume.
    6. **Suggestions for Improvement**: Give concise suggestions to improve the resume.

    Format your response in three sections:
    1. Content Improvements (with 3-4 bullet points)
    2. Formatting Suggestions (with 3-4 bullet points)
    3. ATS Optimization (with 3-4 bullet points)

    Also calculate a "Resume Strength" percentage score from 0-100% based on the overall quality.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[review_prompt, image]
        )
        
        # Parse the response to extract each section
        feedback = response.text
        
        # A simple algorithm to generate a resume strength score if not provided in the response
        # This is a placeholder - you may want to implement a more sophisticated scoring system
        score = calculate_resume_strength(feedback)
        
        # Structure the response to match the expected format from the frontend
        structured_feedback = {
            "score": score,
            "content_improvements": extract_section(feedback, "Content Improvements"),
            "formatting_suggestions": extract_section(feedback, "Formatting Suggestions"),
            "ats_optimization": extract_section(feedback, "ATS Optimization")
        }
        
        return structured_feedback
    except Exception as e:
        return {"error": f"Error analyzing resume: {str(e)}"}

def calculate_resume_strength(feedback):
    # Look for explicit score in the feedback
    import re
    score_match = re.search(r'Resume Strength[:\s]+(\d+)%', feedback)
    if score_match:
        return int(score_match.group(1))
    
    # Simple heuristic score calculation based on positive/negative language
    positive_words = ['excellent', 'good', 'strong', 'impressive', 'effective', 'clear']
    negative_words = ['weak', 'poor', 'missing', 'lacking', 'unclear', 'inconsistent', 'error', 'mistake']
    
    positive_count = sum(feedback.lower().count(word) for word in positive_words)
    negative_count = sum(feedback.lower().count(word) for word in negative_words)
    
    total = positive_count + negative_count
    if total == 0:
        return 70  # Default value if no indicators found
    
    score = int((positive_count / total) * 100)
    # Ensure score is reasonable
    return max(40, min(95, score))  # Cap between 40% and 95%

def extract_section(feedback, section_name):
    # Simple parser to extract bullet points from a section
    import re
    
    # Try to find the section
    section_pattern = f"{section_name}[:\\s]+(.*?)(?=\\n\\s*\\n|$)"
    section_match = re.search(section_pattern, feedback, re.DOTALL)
    
    if not section_match:
        # Return placeholder items if section not found
        return [
            f"Recommendation for {section_name.lower()}",
            f"Another suggestion related to {section_name.lower()}"
        ]
    
    section_text = section_match.group(1).strip()
    
    # Extract bullet points (lines starting with -, *, •, or numbers)
    bullet_points = re.findall(r'(?:^|\n)\s*(?:[-•*]|\d+\.)\s*(.*?)(?=\n\s*(?:[-•*]|\d+\.)|$)', section_text, re.DOTALL)
    
    # If no bullet points found, split by new lines
    if not bullet_points:
        bullet_points = [line.strip() for line in section_text.split('\n') if line.strip()]
    
    # Limit to 3-4 bullet points and clean them up
    bullet_points = [point.strip() for point in bullet_points[:4]]
    
    # Ensure we have at least some content
    if not bullet_points:
        bullet_points = [f"Recommendation for {section_name.lower()}"]
    
    return bullet_points

@app.route('/')
def index():
    return render_template('resume_upload.html')  # Use your HTML file here

@app.route('/api-info')
def api_info():
    """Return info about the API server for client discovery"""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = request.environ.get('SERVER_PORT', 5000)
    
    return jsonify({
        "status": "online",
        "host": hostname,
        "ip": local_ip,
        "port": port
    })

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    # Handle preflight OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
        
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file:
        # Generate a unique filename to avoid collisions
        original_filename = file.filename
        ext = os.path.splitext(original_filename)[1].lower()
        
        if ext not in ['.pdf', '.png', '.jpg', '.jpeg', '.doc', '.docx']:
            return jsonify({"error": "Invalid file type. Please upload a PDF, DOCX, or image file."}), 400
        
        # Create a unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(file_path)
        
        try:
            # Process the file
            image = get_first_page_image(file_path)
            feedback_result = analyze_resume(image)
            
            # Clean up the file after processing
            os.remove(file_path)
            
            return jsonify({
                "filename": original_filename,
                "score": feedback_result.get("score", 70),
                "content_improvements": feedback_result.get("content_improvements", []),
                "formatting_suggestions": feedback_result.get("formatting_suggestions", []),
                "ats_optimization": feedback_result.get("ats_optimization", [])
            })
        except Exception as e:
            # Clean up the file in case of error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # You can specify the port when running the app
    # Default to port 5000 if no port is specified
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    
    print(f"Starting Flask server on port {port}")
    print(f"Open your browser to http://localhost:{port} to use the application")
    
    # Allow connections from any IP address (0.0.0.0)
    app.run(host='0.0.0.0', port=port, debug=True)
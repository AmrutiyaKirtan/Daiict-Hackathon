from google import genai
from PIL import Image
import fitz  # PyMuPDF
import os

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
    else:
        raise ValueError("Unsupported file format")

# === Input your file path here ===
file_path = "C:/Users/kirta/OneDrive/Desktop/Internship notes/Resume/Kirtan_Amrutiya_RESUME.pdf"
image = get_first_page_image(file_path)

# === Gemini API Call ===
client = genai.Client(api_key="AIzaSyBRnWsaXoX30zdpLClvJ78VjSyDFPTdFvU")

review_prompt = """
You are a resume reviewing expert. Please review the attached resume image based on the following parameters:

1. **Spelling and Grammar**: Point out any spelling or grammatical errors.
2. **ATS-Friendliness**: Evaluate if the resume is likely to be parsed correctly by an Applicant Tracking System (ATS).
3. **Use of Action Words**: Check if the resume uses strong, industry-approved action words (refer to Harvard’s action word list).
4. **Structure and Formatting**: Comment on the layout, font consistency, white space, section headers, and overall readability.
5. **Professional Tone**: Evaluate the tone and language of the resume.
6. **Suggestions for Improvement**: Give concise suggestions to improve the resume.

Respond in a clear and structured format. Do not summarize the resume. Just provide feedback.
"""

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[review_prompt, image]
)

print(response.text)

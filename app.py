import os
import json
import base64
from io import BytesIO
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Utility
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Gemini AI class
class GeminiAI:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Use appropriate model

    def analyze_image(self, image_path):
        try:
            # Open and validate image
            with Image.open(image_path) as img:
                # Convert image to base64
                buffered = BytesIO()
                img.save(buffered, format=img.format if img.format else "PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # Prepare prompt for image analysis
            prompt = (
    "You are tasked with analyzing the provided construction plan image.\n\n"
    "First, perform a detailed visual inspection and identify key structural elements such as:\n"
    "- Walls\n"
    "- Floors\n"
    "- Doors\n"
    "- Windows\n"
    "- Visible materials and notable design features\n\n"
    "Provide a structured, detailed description of the building's design, structure, and layout.\n\n"
    "Then, based on visual estimation, calculate the approximate quantities of the following construction materials:\n"
    "1. Bricks (in numbers)\n"
    "2. Cement (in bags)\n"
    "3. Water (in liters)\n"
    "4. Fine Aggregate (Sand) (in cubic feet or kilograms)\n"
    "5. Coarse Aggregate (Gravel) (in cubic feet or kilograms)\n\n"
    "Further, estimate:\n"
    "6. Plastering area and material required:\n"
    "   - Inner walls (10 mm thickness)\n"
    "   - Outer walls (15 mm thickness)\n"
    "   - Ceiling (6 mm thickness)\n"
    "(Provide the area in square feet or square meters.)\n\n"
    "7. Painting area:\n"
    "- Include all walls, ceilings, and surfaces to be painted (in square feet or square meters).\n"
    "- Assume two coats of painting unless otherwise specified.\n\n"
    "8. Provide an approximate cost estimate based on the following material rates:\n"
    "- Brick: ₹9 per brick\n"
    "- Cement: ₹400 per bag\n"
    "- Sand: ₹75 per kilogram\n"
    "- (Assume standard rates for water and aggregates if necessary.)\n\n"
    "Make sure to:\n"
    "* Clearly list all assumptions (such as estimated wall areas, plastering coverage, number of coats, standard mix ratios, and inferred dimensions).\n"
    "* Present the material quantity and cost estimation separately for easy reference.\n"
    "* Maintain clarity, with sections properly organized under suitable headings."
)



            # Call Gemini API
            response = self.model.generate_content([{
                "mime_type": f"image/{img.format.lower() if img.format else 'png'}", "data": img_base64
            }, {
                "text": prompt
            }])

            if response and response.text:
                return {"description": response.text}
            return {"error": "No valid response from Gemini API"}
        except Exception as e:
            return {"error": f"Error analyzing image: {str(e)}"}

@app.route('/')
def index():
    return render_template('index.html')

# Routes
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty file name"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return jsonify({"message": "Uploaded successfully", "file_path": path}), 200
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    file_path = data.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 400

    gemini = GeminiAI()
    result = gemini.analyze_image(file_path)
    return jsonify({"analysis_results": result}), 200

if __name__ == '__main__':
    app.run(debug=True)

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
    "Analyze the provided construction plan image.\n\n"
    "Identify and describe key structural elements:\n"
    "- Walls\n"
    "- Floors\n"
    "- Doors\n"
    "- Windows\n"
    "- Materials and notable design features\n\n"
    "Provide a structured description of the building's design, structure, and layout.\n\n"
    "Estimate the following material quantities based on visual assessment:\n"
    "1. Bricks (number)\n"
    "   - Cost: ₹9 per brick\n"
    "   - Total cost = (Number of bricks) * ₹9\n"
    "2. Cement (bags)\n"
    "   - Cost: ₹400 per bag\n"
    "   - Total cost = (Number of bags) * ₹400\n"
    "3. Water (liters)\n"
    "   - Assume standard cost rate\n"
    "   - Total cost = (Liters of water) * (Cost per liter)\n"
    "4. Fine Aggregate - Sand (cubic feet or kilograms)\n"
    "   - Cost: ₹75 per kilogram\n"
    "   - Total cost = (Kilograms of sand) * ₹75\n"
    "5. Coarse Aggregate - Gravel (cubic feet or kilograms)\n"
    "   - Assume standard cost rate\n"
    "   - Total cost = (Kilograms of gravel) * (Cost per kg)\n\n"
    
    "Estimate plastering material requirements for the following areas:\n"
    "- Inner walls (10 mm thickness)\n"
    "- Outer walls (15 mm thickness)\n"
    "- Ceiling (6 mm thickness)\n\n"
    "For plastering, calculate cement and water requirements based on the area:\n"
    "- Cement: Assume standard plaster mix ratio (1:6 for cement:sand)\n"
    "- Water: Assume water-cement ratio (0.5)\n\n"
    "Estimate the painting area (all walls and ceilings) assuming two coats.\n"
    "For painting, calculate the required paint quantity in liters:\n"
    "- Paint coverage: Assume 1 liter covers 10 square meters\n"
    "- Total paint required = (Total area to be painted) / 10\n"
    "- Paint cost: (Total liters of paint) * (Cost per liter)\n\n"
    
    "Clearly state all assumptions (wall areas, plastering coverage, paint coats, material mix ratios, etc.).\n\n"
    "Provide:\n"
    "- Material Quantity Estimation (for bricks, cement, sand, water, gravel, paint, etc.)\n"
    "- Cost Estimation for each material\n"
    "   (List cost for bricks, cement, water, sand, gravel, plastering, and paint)\n\n"
    "Organize sections clearly for easy reference."
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
    app.run(host='0.0.0.0',debug=True)

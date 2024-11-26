import os
import uuid
import aiohttp
from quart import Quart, request, redirect, send_file, abort, render_template_string
import random
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import io

# URL for the Arial font
FONT_URL = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/Arial.ttf"
FONT_PATH = "Arial.ttf"  # Font will be downloaded here

# Function to download the font if it doesn't exist
def download_font():
    if not os.path.exists(FONT_PATH):
        print("Font not found, downloading...")
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        print("Font downloaded successfully.")

app = Quart(__name__)

# Directory to save images
IMAGES_DIR = './images'
os.makedirs(IMAGES_DIR, exist_ok=True)

# Your DeepAI API key
API_KEY = 'API_TOKEN'
DEEP_AI_URL = 'https://api.deepai.org/api/text2img'


# Sample phrases with "racknerd" to use when text is missing
SAMPLE_TEXTS = [
    "server rack with racknerd text",
    "racknerd engineer",
    "racknerd text on a computer memory stick",
    "racknerd datacenter",
    "racknerd hosting server",
    "racknerd hosting a giveaway",
    "racknerd server in a racknerd datacenter, racknerd branded",
    "racknerd branded CPU",
    "computer with 'Racknerd' text on it",
    "a beautiful image featuring racknerd branding"
]

@app.route('/', methods=['GET'])
async def generate_image():
    # Retrieve the text parameter from the query string
    text = request.args.get('text')

    # If text is missing, generate a random text containing "racknerd"
    if not text:
        text = random.choice(SAMPLE_TEXTS)
    elif "racknerd" not in text.lower():
        return {"error": "The text must include the word 'racknerd'"}, 400

    print("requesting " + text)

    # Send the POST request to the DeepAI API with "hd" version and 720x720 resolution
    async with aiohttp.ClientSession() as session:
        async with session.post(
            DEEP_AI_URL,
            headers={"api-key": API_KEY},
            data={
                "text": text,
                "image_generator_version": "hd",  # "hd" version for high resolution
                "width": "720",                   # Width set to 720
                "height": "720"                   # Height set to 720
            }
        ) as response:
            if response.status != 200:
                return {"error": f"Failed to generate image, status code: {response.status}"}, 500
            result = await response.json()

    # Extract the image URL
    image_url = result.get('output_url')
    if not image_url:
        return {"error": "Failed to retrieve image URL from API response"}, 500

    # Download the image and save it locally
    unique_id = str(uuid.uuid4())
    image_path = os.path.join(IMAGES_DIR, f"{unique_id}.jpg")
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as img_response:
            if img_response.status != 200:
                return {"error": "Failed to download image"}, 500
            image_data = await img_response.read()

    # Download the font if not already available
    download_font()

    # Open the image using Pillow
    with Image.open(io.BytesIO(image_data)) as img:
        # Draw the text on the image
        draw = ImageDraw.Draw(img)
        
        # Load the Arial font with scaling
        try:
            font = ImageFont.truetype(FONT_PATH, 40)  # Use Arial font with font size 40
        except IOError:
            return {"error": "Error loading the font"}, 500
        
        # Scale the font size
        scaling_factor = 0.40  # Adjust this factor to increase or decrease text size
        try:
            font = ImageFont.truetype(FONT_PATH, int(40 * scaling_factor))  # Apply scaling factor
        except IOError:
            return {"error": "Error loading the scaled font"}, 500
        
        text = "made possible by @DeadlyChemist | @dustinc, please upgrade racknerd-1fc9ea 23.94.217.1"

        # Calculate text size using textbbox method
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Position the text (bottom-right corner with a small margin)
        position = (img.width - text_width - 10, img.height - text_height - 10)

        # Draw the text with adjusted size
        draw.text(position, text, font=font, fill=(255, 255, 255))

        # Save the image with the watermark
        img.save(image_path)

        # Redirect the user to the /image/{id} route
        embed_text = f'![](https://racknerd.thechemicalworkshop.com/image/{unique_id} "")'
    
    # Render an HTML response with the embed code and a copy button
    return await render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Image Generated</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #f9f9f9;
            }}
            .container {{
                text-align: center;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                max-width: 90%;
                height: 90%;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                align-items: center;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
                margin-bottom: 20px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: bold;
                text-align: left;
                flex-grow: 1;
            }}
            button {{
                padding: 10px 20px;
                font-size: 18px;
                cursor: pointer;
                border: none;
                background-color: #007BFF;
                color: white;
                border-radius: 4px;
            }}
            button:hover {{
                background-color: #0056b3;
            }}
            img {{
                max-width: 100%;
                max-height: 90%;
                object-fit: contain;
                margin-top: 20px;
                border-radius: 5px;
            }}
            #embed-code {{
                display: none; /* Hidden textarea */
            }}
        </style>
        <script>
            function copyToClipboard() {{
                const embedCode = document.getElementById('embed-code');
                navigator.clipboard.writeText(embedCode.value)
                    .then(() => console.log("Embed code copied!"))
                    .catch((err) => console.error("Failed to copy embed code:", err));
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Your Image</h1>
                <button onclick="copyToClipboard()">Copy Embed</button>
            </div>
            <img src="/image/{unique_id}" alt="Generated Image" />
            <textarea id="embed-code" readonly>{embed_text}</textarea>
        </div>
    </body>
    </html>
""")
    # return redirect(f"/image/{unique_id}")


@app.route('/image/<image_id>', methods=['GET'])
async def serve_image(image_id):
    # Sanitize the image_id to prevent path traversal
    if '..' in image_id or '/' in image_id or '\\' in image_id:
        return abort(400, description="Invalid image ID")

    # Ensure only alphanumeric and dash/underscore characters are allowed
    if not image_id.replace('-', '').replace('_', '').isalnum():
        return abort(400, description="Invalid image ID")

    # Construct the absolute path securely
    image_path = os.path.abspath(os.path.join(IMAGES_DIR, f"{image_id}.jpg"))

    # Ensure the path is within the intended directory
    if not image_path.startswith(os.path.abspath(IMAGES_DIR)):
        return abort(403, description="Access forbidden")

    # Check if the file exists
    if not os.path.exists(image_path):
        return abort(404)

    return await send_file(image_path, mimetype='image/jpeg', as_attachment=False)


@app.route('/gallery', methods=['GET'])
async def gallery():
    # List all image files in the /images directory
    image_files = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]

    # Generate HTML to list all images in a grid
    gallery_html = """
    <h1>Image Gallery</h1>
    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; padding: 20px;">
    """
    
    for image_file in image_files:
        image_id = os.path.splitext(image_file)[0]  # Extract the image ID (filename without extension)
        gallery_html += f'''
            <div style="text-align: center;">
                <a href="/image/{image_id}">
                    <img src="/image/{image_id}" alt="{image_id}" style="width: 200px; height: auto; border-radius: 8px;" />
                </a>
            </div>
        '''
    
    gallery_html += "</div>"

    return await render_template_string(gallery_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9030)

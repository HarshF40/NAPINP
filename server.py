# ⚠️ DISCLAIMER
# This script is intended strictly for educational and experimental purposes only.
# Do NOT use this on your personal browser profile or with your main account on the target website.
# Automating interactions with production websites may violate their Terms of Service (ToS).
# Misuse of such scripts can lead to account bans or legal consequences.
# The author is not responsible for any misuse or damage caused by this script.
# Only works with one site
# Version 2.1; Base64 Image Support

import time
from dotenv import load_dotenv
import os
from playwright.sync_api import sync_playwright
from flask import Flask, jsonify, request
import base64
from pathlib import Path
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)
playwright = None 
browser = None 
page = None

# Create uploads folder if it doesn't exist
UPLOAD_FOLDER = "uploaded_images"
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

def init_page():
    global playwright, browser, user_data_dir, page

    # Initializing
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir=os.getenv("USER_DATA_DIR"),
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-extensions",
        ],
        viewport={"width": 1280, "height": 800}
    )

    # Initializing Page
    page = browser.new_page()
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'platform', { get: () => 'Linux x86_64' });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    """)
    page.goto(os.getenv("SITE"))
    time.sleep(2)

    # Removing any popups or other obstacles
    try:
        locater = page.locator('//span[text()="No thanks"]')
        locater.first.click(timeout=2000)
    except:
        pass
    page.mouse.move(640, 400)
    page.mouse.click(640, 400)


@app.route('/receive', methods=['POST'])
def receive_request():
    global playwright, browser, page 

    data = request.get_json(force=True)
    query = data.get("query")

    # Locate the input field
    textbox = page.get_by_role("textbox", name="Enter a prompt here")
    textbox.click()
    time.sleep(1)

    # Enter the query and send
    textbox.fill(query)
    time.sleep(2)
    textbox.press("Enter")
    time.sleep(2)
    
    # Locate the closest user query bubble
    # Checking if content is loaded completely
    # Wait for the spinner below that specific query bubble to be marked as completed
    page.wait_for_selector('.text-input-field >> xpath=preceding::span[contains(@class, "user-query-bubble-with-background")][1]/following::div[@data-test-lottie-animation-status="completed"][1]', timeout=6000000)

    # Locate the Response content
    locater = page.locator('xpath=(//div[contains(@class, "text-input-field")])[1]/preceding::message-content[1]')
    locater.wait_for(timeout=10000000)

    # Extract the content
    response = locater.inner_text()
    return jsonify({"status": "success", "response":response})

@app.route('/img', methods=['POST'])
def receive_img():
    global playwright, browser, page 
    data = request.get_json(force=True)
    query = data.get("query")
    base64_image = data.get("image")  # Get base64 encoded image
    
    if not base64_image:
        return jsonify({"status": "error", "message": "No image provided"}), 400
    
    try:
        # Remove data URI prefix if present (e.g., "data:image/png;base64,")
        if "," in base64_image:
            base64_image = base64_image.split(",")[1]
        
        # Decode base64 image
        image_data = base64.b64decode(base64_image)
        
        # Generate unique filename with timestamp
        timestamp = int(time.time() * 1000)
        image_path = os.path.join(UPLOAD_FOLDER, f"image_{timestamp}.png")
        
        # Save the image to disk
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        print(f"✅ Image saved to: {image_path}")
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to decode/save image: {str(e)}"}), 400
    
    # Locate the input field
    textbox = page.get_by_role("textbox", name="Enter a prompt here")
    textbox.click()
    time.sleep(1)

    textbox.fill(query)
    time.sleep(2)

    upload_button = page.locator('button[aria-label="Open upload file menu"].upload-card-button.open')
    upload_button.wait_for(timeout=10000000)
    upload_button.click()
    time.sleep(1)

    upload_files_menu_item = page.locator("div.menu-text", has_text="Upload files")
    upload_files_menu_item.wait_for(timeout=10000000)
    upload_files_menu_item.click()
    time.sleep(1)

    import subprocess
    subprocess.run('hyprctl dispatch closewindow address:$(hyprctl clients -j | jq -r \'.[] | select(.class=="Chrome" and .title=="Open Files") | .address\')',
        shell=True,
        check=True
    )
    time.sleep(3)
    
    # Use the saved image path
    file_input = page.locator('input[type="file"]')
    absolute_path = os.path.abspath(image_path)
    file_input.set_input_files(absolute_path)
    print(f"✅ Image uploaded successfully from: {absolute_path}") 
    
    time.sleep(15) # Statically wait for the image to upload
    textbox.click()
    textbox.press("Enter")
    time.sleep(2)
    
    # Locate the closest user query bubble
    # Checking if content is loaded completely
    # Wait for the spinner below that specific query bubble to be marked as completed
    page.wait_for_selector('.text-input-field >> xpath=preceding::span[contains(@class, "user-query-bubble-with-background")][1]/following::div[@data-test-lottie-animation-status="completed"][1]', timeout=6000000)

    # Locate the Response content
    locater = page.locator('xpath=(//div[contains(@class, "text-input-field")])[1]/preceding::message-content[1]')
    locater.wait_for(timeout=10000000)

    # Extract the content
    response = locater.inner_text()
    
    # Optional: Clean up the saved image after processing
    try:
        os.remove(absolute_path)
        print(f"🗑️ Cleaned up image: {absolute_path}")
    except:
        pass
    
    return jsonify({"status": "success", "response": response})


if __name__ == "__main__":
    init_page()
    app.run(host='0.0.0.0', port=5000, threaded=False)

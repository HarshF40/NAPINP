# ⚠️ DISCLAIMER
# This script is intended strictly for educational and experimental purposes only.
# Do NOT use this on your personal browser profile or with your main account on the target website.
# Automating interactions with production websites may violate their Terms of Service (ToS).
# Misuse of such scripts can lead to account bans or legal consequences.
# The author is not responsible for any misuse or damage caused by this script.
# Only works with one site

import time
from dotenv import load_dotenv
import os
from playwright.sync_api import sync_playwright
from flask import Flask, jsonify, request

load_dotenv()

app = Flask(__name__)
playwright = None 
browser = None 
page = None

def init_page():
    global playwright, browser, user_data_dir, page

    # Initializing
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir=os.getenv("USER_DATA_DIR"),
        headless=True,
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
    textbox.type(query, delay=80)
    time.sleep(1)
    textbox.press("Enter")
    time.sleep(2)
    
    # Locate the closest user query bubble
    # Checking if content is loaded completely
    # Wait for the spinner below that specific query bubble to be marked as completed
    page.wait_for_selector('.text-input-field >> xpath=preceding::span[contains(@class, "user-query-bubble-with-background")][1]/following::div[@data-test-lottie-animation-status="completed"][1]', timeout=6000000)

    # Locate the Response content
    locater = page.locator('xpath=(//div[contains(@class, "text-input-field")])[1]/preceding::message-content[1]')
    locater.wait_for(timeout=10000)

    # Extract the content
    response = locater.inner_text()
    return jsonify({"status": "success", "response":response})

if __name__ == "__main__":
    init_page()
    app.run(threaded=False)

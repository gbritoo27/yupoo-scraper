from flask import Flask, request, jsonify, Response
from playwright.sync_api import sync_playwright
import json
from urllib.parse import unquote

app = Flask(__name__)

def scrape_yupoo(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # Wait for images to load
        page.wait_for_selector("img")

        # Collect images
        images = page.evaluate("""
            () => Array.from(document.querySelectorAll('img')).map(img => img.src)
        """)

        browser.close()
        return images

def clean_images(images):
    cleaned = []
    seen = set()
    for img in images:
        if "logo/YupooDemo" in img:
            continue
        if not any(img.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
            continue
        if img not in seen:
            seen.add(img)
            cleaned.append(img)
    return cleaned

@app.route("/scrape", methods=["GET"])
def scrape():
    raw_url = request.args.get("url")
    if not raw_url:
        return Response(json.dumps({"error": "Missing url parameter"}), status=400, mimetype="application/json")
    url = unquote(raw_url)
    try:
        images = scrape_yupoo(url)
        cleaned_images = clean_images(images)
        return Response(json.dumps({"images": cleaned_images}), mimetype="application/json")
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype="application/json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

from flask import Flask, request, jsonify, Response
import asyncio
from pyppeteer import launch
import json
from urllib.parse import unquote

app = Flask(__name__)

async def scrape_yupoo_async(url):
    browser = await launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    )
    page = await browser.newPage()
    await page.goto(url, {"waitUntil": "networkidle2"})

    # Wait for images
    await page.waitForSelector("img")

    # Extract image URLs
    images = await page.evaluate(
        "() => Array.from(document.querySelectorAll('img')).map(img => img.src)"
    )

    await browser.close()
    return images

def scrape_yupoo(url):
    return asyncio.get_event_loop().run_until_complete(scrape_yupoo_async(url))

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

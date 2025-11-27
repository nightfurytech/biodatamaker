import os
import uuid

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory, make_response, g
from flask_cors import CORS
from openai import OpenAI
from supabase import create_client, Client
from flask import redirect, abort
import requests
import threading, time

from supabase_client import supabase, upload_html
from worker_process_pending import process_pending

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:8080",  # when you open FE via localhost
            "http://127.0.0.1:8080",  # just in case
            "http://192.168.0.3:8080",  # when you open FE via LAN IP
            "http://13.201.121.48:4000"  # deployed frontend
        ]
    }
})

load_dotenv()  # this loads .env into os.environ
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]  # service role, backend only


def generate_unique_id() -> str:
    # short friendly id for URL
    return uuid.uuid4().hex[:10]


def build_placeholder_html(name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your Biodata is Being Prepared</title>
<style>
  body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(135deg, #ffe6f1 0%, #f6f7ff 100%);
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    color: #333;
  }}

  .card {{
    background: #ffffff;
    padding: 2.5rem 3rem;
    border-radius: 1.75rem;
    box-shadow: 0 15px 50px rgba(0,0,0,0.08);
    max-width: 480px;
    width: 90%;
    text-align: center;
    animation: fadeIn 0.8s ease-out;
  }}

  h1 {{
    font-size: 1.85rem;
    margin-bottom: 1.2rem;
    font-weight: 700;
    line-height: 1.3;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.4rem;
  }}

  p {{
    font-size: 1rem;
    line-height: 1.6;
    color: #555;
    margin: 0.35rem 0;
  }}

  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}
</style>
</head>

<body>
  <div class="card">
    <h1>✨ Your biodata is getting ready ✨</h1>

    <p>Hi {name}, your biodata page is being generated.</p>
    <p>Give us 5–10 minutes, and the final version will be available.</p>
  </div>
</body>
</html>
"""


@app.route("/api/v1/generate-bio", methods=["POST"])
def generate_bio():
    form = request.form

    # 1. Read form fields from FE
    name = form.get("name", "").strip()
    dob = form.get("dob")  # "2025-11-02"
    job_role = form.get("jobRole", "")
    curr_loc = form.get("location", "")
    social_media = form.get("socialMedia", "")
    about_me = form.get("aboutMe", "")
    partner_pref = form.get("partnerPreferences", "")
    image_url = form.get("image", "")  # already a Supabase public URL

    if not name or not dob:
        return jsonify({"error": "name and dob are required"}), 400

    # 2. Generate unique slug for this biodata
    unique_id = generate_unique_id()

    # 3. Build and upload placeholder HTML
    placeholder_html = build_placeholder_html(name)
    public_bio_url = upload_html(unique_id, placeholder_html)

    # 4. Insert into Supabase table
    row = {
        "name": name,
        "dob": dob,
        "job_role": job_role,
        "curr_loc": curr_loc,
        "social_media": social_media,
        "about_me": about_me,
        "partner_preference": partner_pref,
        "image_url": image_url,
        "status": "PENDING",
        "public_bio_url": public_bio_url,
        "unique_id": unique_id,
    }

    supabase.table("biodatainfo").insert(row).execute()

    # 5. Return URL that user can open/share
    # {{domain}} is your own domain where the next route will live
    share_url = f"{request.host_url.rstrip('/')}/{unique_id}"

    return jsonify({"url": share_url}), 200

@app.get("/<unique_id>")
def show_biodata(unique_id):
    # Get row safely without .single()
    resp = supabase.table("biodatainfo") \
                   .select("public_bio_url") \
                   .eq("unique_id", unique_id) \
                   .limit(1) \
                   .execute()

    rows = resp.data or []

    if len(rows) == 0:
        return (
            "<h1 style='text-align:center;margin-top:40px;'>Invalid biodata link</h1>",
            404,
            {"Content-Type": "text/html; charset=utf-8"},
        )

    row = rows[0]
    if not row.get("public_bio_url"):
        return (
            "<h1 style='text-align:center;margin-top:40px;'>Biodata not ready yet</h1>",
            404,
            {"Content-Type": "text/html; charset=utf-8"},
        )

    # ✅ Fetch raw bytes, not .text
    r = requests.get(row["public_bio_url"])
    r.raise_for_status()

    # ✅ Return bytes as utf-8 HTML
    return r.content, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/ping/", methods=["GET"])
def serve_ui():
    return jsonify({"hello": "world"}), 200

def background_worker():
    while True:
        try:
            process_pending()
        except Exception as e:
            print("Worker error:", e)
        time.sleep(300)  # 5 mins


if __name__ == "__main__":
    worker_thread = threading.Thread(target=background_worker, daemon=True)
    worker_thread.start()
    app.run(host="0.0.0.0", port=8081, debug=True)

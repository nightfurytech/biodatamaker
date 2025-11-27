# worker_process_pending.py
import os
from supabase_client import supabase, upload_html
from dotenv import load_dotenv
from openai import OpenAI

from datetime import datetime


BUCKET_NAME = "biodata-images"
load_dotenv()  # this loads .env into os.environ
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def format_dob(date_str: str) -> str:
  """
  Converts '2025-11-02' -> '2 November, 2025'
  """
  try:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%-d %B, %Y")  # Linux / Mac
  except:
    # Windows does not support %-d (no leading zero)
    return dt.strftime("%#d %B, %Y")

def count_words(text: str) -> int:
  return len(text.split())

def generate_biodata_html(
        name: str,
        dob: str,
        job_role: str,
        location: str,
        social_handles_csv: str,
        about_me: str,
        partner_preferences: str,
        image_url: str,
        model: str = "gpt-4.1-mini",
):
  """
  Generates a purple-themed, dating-friendly biodata HTML page with:
  - centered card layout (fixed)
  - redesigned Basic Details as mini-cards
  - dynamic age JS
  - modern dating fonts
  - purple gradient
  - no vertical pipes
  """

  # Word validations
  if not (50 <= count_words(about_me) <= 250):
    raise ValueError("'about_me' must be 50–250 words.")
  if not (50 <= count_words(partner_preferences) <= 250):
    raise ValueError("'partner_preferences' must be 50–250 words.")

  system_prompt = (
    "You are an expert UI/UX designer who builds modern, romantic, premium, "
    "dating-app-style biodata pages with a purple theme. "
    "You must output ONLY valid HTML. No Markdown. No explanations."
  )

  #
  # ——— STRUCTURED USER DATA BLOCK ———
  #
  structured_block = f"""
Name: {name}
Date of Birth: {dob}
Job Role: {job_role}
Current Location: {location}
Social Handles (comma separated): {social_handles_csv}

[ABOUT ME]
{about_me}

[PARTNER PREFERENCES]
{partner_preferences}

Image URL: {image_url}
"""

  #
  # ——— MAIN PROMPT ———
  #
  user_prompt = f"""
The following is the user's biodata information:

{structured_block}

Generate a COMPLETE HTML5 biodata page with:

############################################################
### ✨ GLOBAL DESIGN — DATING-APP STYLE
############################################################
- Full-screen smooth purple gradient background:

  body {{
    background: linear-gradient(135deg, #f5e9ff 0%, #e3d1ff 50%, #d8c2ff 100%);
    margin: 0;
    padding: 0;
    min-height: 100vh;

    display: flex;
    justify-content: center;
    align-items: center;   /* CENTER vertically */
    padding-top: 40px;     /* avoid sticking to top */
    padding-bottom: 40px;
    font-family: "Inter", "Poppins", "SF Pro Display", system-ui, -apple-system, sans-serif;
    color: #1a1a1a;
  }}

- The card MUST be centered perfectly on the screen.

############################################################
### 💜 CARD DESIGN
############################################################
- White card (#ffffff)
- max-width: 820px
- width: 90%
- margin: auto
- border-radius: 24px
- box-shadow: 0 12px 38px rgba(140, 84, 255, 0.18)
- padding: 40px 32px 50px
- smooth hover micro-lift:
    .card:hover {{ transform: translateY(-4px); }}

############################################################
### 🚫 NO vertical colored pipe before headings
############################################################
Headings must be clean:
- Purple text (#6a1fb4)
- Bold, dating-style
- No left border/pipeline

############################################################
### 💖 HERO SECTION (CENTERED)
############################################################
Centered hero:

- Circular profile photo (170–180px)
- border: 4px solid #d7b6ff
- glow shadow
- hover-scale effect

- Name in big purple font
- Dating-style tagline:
    “Open to something meaningful 💜”
- 2–3 line warm summary based on About Me

############################################################
### ⭐ BASIC DETAILS (LEFT-ALIGNED MINI-CARDS)
############################################################
NO vertical pipes.

Use mini cards:

  .details-grid {{
     display: grid;
     grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
     gap: 14px 18px;
     margin-top: 16px;
  }}

  .detail-card {{
     background: #f7f0ff;
     border-radius: 16px;
     padding: 12px 16px;
     box-shadow: 0 2px 6px rgba(150,90,255,0.15);
  }}

Inside each card:

  .detail-label {{
     font-size: 0.70rem;
     text-transform: uppercase;
     letter-spacing: 0.08em;
     color: #7a7a8a;
     margin-bottom: 4px;
  }}

  .detail-value {{
     font-size: 1rem;
     font-weight: 500;
  }}

Basic detail items to include:
- Name
- Date of Birth
- Age (*dynamic using JS*)
- Location
- Job Role

Use:

  <span id="calculated-age"></span>

For age.

############################################################
### 🔮 JS AGE CALCULATION
############################################################
At the bottom of HTML before </body>, include:

<script>
  const dobString = "{dob}";
  const birth = new Date(dobString);

  function calculateAge(date) {{
    if (isNaN(date)) return "";
    const today = new Date();
    let age = today.getFullYear() - date.getFullYear();
    if (
      today.getMonth() < date.getMonth() ||
      (today.getMonth() === date.getMonth() && today.getDate() < date.getDate())
    ) {{
      age--;
    }}
    return age;
  }}

  const ageElem = document.getElementById("calculated-age");
  if (ageElem && !isNaN(birth)) {{
    const age = calculateAge(birth);
    if (age) ageElem.textContent = age;
  }}
</script>

############################################################
### 💜 INTERESTS & HOBBIES (LEFT-ALIGNED)
############################################################
Extract hobbies/interests from ABOUT ME.
Display as cute purple pill badges:

  .badge {{
     display: inline-block;
     background: #f1e6ff;
     color: #5a2ca0;
     padding: 6px 14px;
     border-radius: 999px;
     font-size: 0.85rem;
     font-weight: 500;
     margin: 6px 8px 0 0;
     box-shadow: 0 2px 6px rgba(150,90,255,0.18);
  }}

############################################################
### 💼 SOCIAL PROFILES 💜 (LEFT)
############################################################
Parse social_handles_csv and produce:

- Instagram 📸 @handle or clickable link
- LinkedIn 💼 URL clickable
- X/Twitter 🐦 @handle or URL

No inventions.

############################################################
### 📄 ABOUT ME + PARTNER PREFERENCES
############################################################
Use the provided text but rewrite in smooth dating tone.
Warm, clean, readable.

############################################################
### 📝 FOOTER
############################################################
Centered small line:
“Share this profile with someone special 💜”

############################################################
### HTML STRUCTURE
############################################################
Return:

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{name} - Biodata</title>
  <style> ALL CSS HERE </style>
</head>
<body>
  EVERYTHING HERE
  <script> AGE SCRIPT </script>
</body>
</html>

############################################################
### RULES
############################################################
- Output ONLY raw HTML
- No Markdown
- No lorem ipsum
- Inline CSS only
- Only JS allowed is age calculation
"""

  response = client.chat.completions.create(
    model=model,
    messages=[
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_prompt},
    ],
    temperature=0.75,
  )

  return response.choices[0].message.content



def process_pending():
  # 1. Get all PENDING rows
  resp = supabase.table("biodatainfo").select("*").eq("status", "PENDING").execute()
  rows = resp.data or []

  for row in rows:
    unique_id = row["unique_id"]
    print(f"Processing biodata {unique_id}")
    dob_formatted = format_dob(str(row["dob"]))

    # 2. Generate final HTML for this row
    final_html = generate_biodata_html(
      name=row["name"],
      dob=dob_formatted,
      job_role=row["job_role"],
      location=row["curr_loc"],
      social_handles_csv=row["social_media"],
      about_me=row["about_me"],
      partner_preferences=row["partner_preference"],
      image_url=row["image_url"]
    )

    # 3. Upload HTML and get public URL (same path as placeholder)
    public_url = upload_html(unique_id, final_html)

    # 4. Update row as COMPLETED
    supabase.table("biodatainfo").update(
      {
        "status": "COMPLETED",
        "public_bio_url": public_url,
      }
    ).eq("id", row["id"]).execute()
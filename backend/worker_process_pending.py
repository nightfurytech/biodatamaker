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
    Generates a fully mobile-responsive biodata HTML page:
    - Perfect on iPhone/Android screens
    - Centered beautifully on desktop
    - Scrolls naturally on mobile (no forced vertical centering)
    - Mini-cards, badges, dynamic age script
    """

    if not (50 <= count_words(about_me) <= 250):
        raise ValueError("'about_me' must be 50–250 words.")
    if not (50 <= count_words(partner_preferences) <= 250):
        raise ValueError("'partner_preferences' must be 50–250 words.")

    system_prompt = (
        "You are an expert UI/UX designer who builds modern, romantic, premium, "
        "dating-app-style biodata pages in HTML. "
        "You must output ONLY HTML. No Markdown."
    )

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

    user_prompt = f"""
The following is the user's biodata information:

{structured_block}

Generate a **complete HTML5 biodata** page with:

############################################################
### 📱 MOBILE-FIRST RESPONSIVE LAYOUT (VERY IMPORTANT)
############################################################

The page MUST:
- Look perfect on iPhone, Android, small screens
- Use **scrolling layout** on mobile (NO vertical centering)
- Use **centered layout only on desktop**
- Use responsive units (%, rem, max-width, minmax grid)
- Card width:
    - mobile: width 94%
    - tablet: width 90%
    - desktop: max-width 820px

- Add this meta tag:

  <meta name="viewport" content="width=device-width, initial-scale=1.0">

############################################################
### 🎨 GLOBAL DESIGN (DATING-APP STYLE)
############################################################
body {{
  background: linear-gradient(135deg, #f5e9ff 0%, #e3d1ff 50%, #d8c2ff 100%);
  margin: 0;
  padding: 0;

  display: flex;
  justify-content: center;

  /* MOBILE MUST SCROLL */
  align-items: flex-start;

  padding-top: 40px;
  padding-bottom: 60px;

  font-family: "Inter", "Poppins", "SF Pro Display", system-ui, -apple-system, sans-serif;
  color: #1a1a1a;
}}

############################################################
### 💜 CARD DESIGN (RESPONSIVE)
############################################################
.card {{
  background: #ffffff;
  width: 94%;
  max-width: 820px;
  margin: auto;

  border-radius: 24px;
  box-shadow: 0 12px 38px rgba(140,84,255,0.18);

  padding: 32px 22px 45px;
  transition: 0.25s ease;
}}

@media (min-width: 768px) {{
  .card {{
    padding: 40px 32px 50px;
    width: 90%;
  }}
}}

@media (min-width: 1024px) {{
  .card {{
    width: 820px;
  }}
}}

############################################################
### 🚫 NO VERTICAL PIPE BEFORE HEADINGS
############################################################

############################################################
### 💖 HERO SECTION (CENTERED)
############################################################

- Circular profile image 140px mobile → 170px desktop.
- Center-aligned.
- Purple glow ring.

############################################################
### ⭐ BASIC DETAILS (RESPONSIVE GRID MINI CARDS)
############################################################
.details-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
}}

.detail-card {{
  background: #f7f0ff;
  border-radius: 16px;
  padding: 12px 14px;
  box-shadow: 0 2px 6px rgba(150,90,255,0.15);
}}

.detail-label {{
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7a7a8a;
}}

.detail-value {{
  font-size: 1rem;
  font-weight: 500;
}}

############################################################
### 🔮 DYNAMIC AGE SCRIPT
############################################################
Age must be:

<span id="calculated-age"></span>

Age JS:

<script>
  const dobString = "{dob}";
  const birth = new Date(dobString);

  function calculateAge(d) {{
    if (isNaN(d)) return "";
    const t = new Date();
    let age = t.getFullYear() - d.getFullYear();
    if (t.getMonth() < d.getMonth() ||
       (t.getMonth()==d.getMonth() && t.getDate()<d.getDate())) {{
      age--;
    }}
    return age;
  }}

  const ageEl = document.getElementById("calculated-age");
  if (ageEl && !isNaN(birth)) {{
    ageEl.textContent = calculateAge(birth);
  }}
</script>

############################################################
### 💜 INTEREST BADGES (RESPONSIVE)
############################################################
.badge {{
  display: inline-block;
  background: #f1e6ff;
  color: #5a2ca0;
  padding: 6px 14px;
  border-radius: 999px;
  margin: 6px 8px 0 0;
  font-size: 0.85rem;
  box-shadow: 0 2px 6px rgba(150,90,255,0.18);
}}

############################################################
### SOCIAL PROFILES 💜 (LEFT ALIGNED)
############################################################

############################################################
### ABOUT ME + PARTNER PREFERENCES
############################################################

############################################################
### FOOTER
############################################################
Centered:
“Share this profile with someone special 💜”

############################################################
### MUST RETURN FULL HTML5 DOCUMENT
############################################################

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} - Biodata</title>
<style>
ALL CSS MUST BE INCLUDED HERE
</style>
</head>
<body>
FULL BIODATA HERE
<script> AGE SCRIPT </script>
</body>
</html>

ONLY RETURN RAW HTML. NO MARKDOWN.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
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

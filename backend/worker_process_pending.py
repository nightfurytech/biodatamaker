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
  - Centered nicely on desktop
  - Mini-cards, badges, dynamic age JS
  - SAFE when job role or social handles are missing
  - Supports multiple social handles (Instagram, LinkedIn, Snapchat, TikTok, etc.)
  """

    if not (50 <= count_words(about_me) <= 250):
        raise ValueError("'about_me' must be 50–250 words.")
    if not (50 <= count_words(partner_preferences) <= 250):
        raise ValueError("'partner_preferences' must be 50–250 words.")

    # Pre-compute flags so the model knows what is actually present
    job_role_present = bool(job_role.strip())
    socials_present = bool(social_handles_csv.strip())

    system_prompt = (
        "You are an expert UI/UX designer who builds modern, romantic, premium, "
        "dating-app-style biodata pages in HTML. "
        "You must output ONLY HTML. No Markdown."
    )

    structured_block = f"""
Name: {name}
Date of Birth: {dob}
Job Role: {job_role or "(not provided)"}
Job Role Present: {"yes" if job_role_present else "no"}
Current Location: {location or "(not provided)"}
Social Handles CSV: {social_handles_csv or "(none)"}
Social Handles Present: {"yes" if socials_present else "no"}

[ABOUT ME]
{about_me}

[PARTNER PREFERENCES]
{partner_preferences}

Image URL: {image_url}
"""

    user_prompt = f"""
The following is the user's biodata information:

{structured_block}

Use this data to generate a **complete HTML5 biodata page**.

VERY IMPORTANT:
- If a field is marked as "(not provided)" or "Present: no", do NOT invent it.
- Omit that card/section entirely instead of writing placeholders.

############################################################
### 📱 MOBILE-FIRST RESPONSIVE LAYOUT
############################################################

The page MUST:
- Work beautifully on small mobile screens (iOS/Android).
- Use a scrolling layout (NO vertical centering tricks that cut off content).
- Be centered within the viewport on larger screens.

Use:

body {{
  background: linear-gradient(135deg, #f5e9ff 0%, #e3d1ff 50%, #d8c2ff 100%);
  margin: 0;
  padding: 0;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 40px;
  padding-bottom: 60px;
  font-family: "Inter", "Poppins", "SF Pro Display", system-ui, -apple-system, sans-serif;
  color: #1a1a1a;
}}

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
### 💖 HERO SECTION
############################################################
- Circular profile image (140px mobile → 170px desktop).
- Centered, with purple ring and glow.
- Name big and bold.
- Small dating-style tagline.
- 2–3 line highlight summary based on ABOUT ME.

############################################################
### ⭐ BASIC DETAILS (SAFE MINI CARDS)
############################################################
Use a responsive grid:

.details-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
  margin-top: 16px;
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
  margin-bottom: 4px;
}}

.detail-value {{
  font-size: 1rem;
  font-weight: 500;
}}

Include cards for:
- Name (always, if provided)
- Date of Birth
- Age (with dynamic JS span)
- Current Location
- Job Role **ONLY IF** Job Role Present is "yes".
  → If Job Role Present is "no", DO NOT render a “Job Role” card.

Age value must be:

<span id="calculated-age"></span>

############################################################
### 🔮 DYNAMIC AGE SCRIPT
############################################################
At the bottom of HTML, before </body>, include:

<script>
  const dobString = "{dob}";
  const birth = new Date(dobString);

  function calculateAge(d) {{
    if (isNaN(d)) return "";
    const t = new Date();
    let age = t.getFullYear() - d.getFullYear();
    if (t.getMonth() < d.getMonth() ||
       (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) {{
      age--;
    }}
    return age;
  }}

  const ageEl = document.getElementById("calculated-age");
  if (ageEl && !isNaN(birth)) {{
    const age = calculateAge(birth);
    if (age) ageEl.textContent = age;
  }}
</script>

############################################################
### 💜 INTEREST BADGES
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
### 💼 SOCIAL PROFILES 💜 (ROBUST)
############################################################
You are given:

Social Handles CSV: a comma-separated string. Examples:
- "Instagram: billi"
- "Instagram: @billi, LinkedIn:https://linkedin.com/in/billi"
- "Instagram @billi, Snapchat: billisnap, TikTok: @billi.cat"

RULES:

1. If **Social Handles Present** is "no" OR the string is "(none)":
   → Do NOT render the “Social Profiles 💜” section at all.

2. If there is at least one handle:
   - Render a section with heading: "Social Profiles 💜"
   - Use a simple list:

     <ul class="social-list">
       <li>...</li>
       ...
     </ul>

   - CSS:

     .social-list {{
       list-style: none;
       padding: 0;
       margin: 6px 0 0;
     }}

     .social-list li {{
       margin-bottom: 6px;
       font-size: 0.95rem;
     }}

     .social-label {{
       font-weight: 500;
       color: #6a1fb4;
       margin-right: 4px;
     }}

     .social-link {{
       color: #7a35d2;
       text-decoration: none;
       font-weight: 500;
     }}

     .social-link:hover {{
       text-decoration: underline;
     }}

3. Parsing each handle (be defensive!):
   - Split the CSV string by commas → each part is one handle entry.
   - Trim whitespace.
   - If entry is empty after trimming → skip it.

   For each non-empty entry:
   - Try to detect platform name (case-insensitive substring match):
       - contains "instagram" → Instagram 📸
       - contains "linkedin" → LinkedIn 💼
       - contains "snapchat" → Snapchat 👻
       - contains "tiktok" → TikTok 🎵
       - otherwise → Generic "Profile" ⭐

   - Try to separate label and value:
       - If there is a ":" character → left is label, right is value.
       - Else if there is a space and it starts with a platform word (e.g., "Instagram @billi"):
           - Treat the first word as label and the rest as value.
       - Else if it only looks like "@username" or "username":
           - Treat label as "Profile" and value as that text.

   - If the extracted value **looks like a URL** (contains "http://" or "https://" or "www."):
       - Render it as a clickable link:

         <li><span class="social-label">📸 Instagram:</span>
             <a href="URL_HERE" class="social-link" target="_blank" rel="noopener noreferrer">URL_HERE</a>
         </li>

   - Otherwise, just render label + plain text (no link):

         <li><span class="social-label">📸 Instagram:</span> @billi</li>

4. ALWAYS keep the HTML valid:
   - All list items must be inside a single <ul>.
   - Do not create nested <ul> accidentally.
   - If after parsing no valid handles remain → skip the whole Social Profiles section.

############################################################
### ABOUT ME + PARTNER PREFERENCES
############################################################
Use the given text, polish lightly, keep first-person voice and meaning.

############################################################
### FOOTER
############################################################
Centered text:
“Share this profile with someone special 💜”

############################################################
### FULL HTML5 DOCUMENT
############################################################
Return FULL HTML5 like:

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} - Biodata</title>
  <style>
    /* all CSS here */
  </style>
</head>
<body>
  <div class="card">
    <!-- profile content here -->
  </div>
  <!-- age script here -->
</body>
</html>

RULES:
- ONLY return raw HTML (no Markdown, no ```).
- No lorem ipsum.
- Do NOT invent data for missing fields.
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

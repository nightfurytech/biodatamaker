# worker_process_pending.py
import os
from supabase_client import supabase, upload_html
from dotenv import load_dotenv
from openai import OpenAI
import html
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
    - Works on iPhone/Android + desktop
    - Handles missing job role & socials
    - Handles arbitrary social text safely (Instagram/LinkedIn/Facebook/Snapchat/TikTok etc.)
    - Social text can NEVER break the HTML
    """

    if not (50 <= count_words(about_me) <= 250):
        raise ValueError("'about_me' must be 50–250 words.")
    if not (50 <= count_words(partner_preferences) <= 250):
        raise ValueError("'partner_preferences' must be 50–250 words.")

    # Flags + sanitized inputs for safety
    job_role_present = bool(job_role.strip())
    socials_present = bool(social_handles_csv.strip())

    # Escape anything that could be interpreted as HTML
    safe_social_text = html.escape(social_handles_csv or "")
    safe_name = html.escape(name or "")
    safe_dob = html.escape(dob or "")
    safe_job_role = html.escape(job_role or "")
    safe_location = html.escape(location or "")
    safe_image_url = html.escape(image_url or "")

    system_prompt = (
        "You are an expert UI/UX designer who builds modern, romantic, premium, "
        "dating-app-style biodata pages in pure HTML+CSS. "
        "You must output ONLY valid HTML. No Markdown. No comments."
    )

    structured_block = f"""
Name: {safe_name}
Date of Birth: {safe_dob}
Job Role: {safe_job_role or "(not provided)"}
Job Role Present: {"yes" if job_role_present else "no"}
Current Location: {safe_location or "(not provided)"}
Social Handles Raw Text: {safe_social_text or "(none provided)"}
Social Handles Present: {"yes" if socials_present else "no"}

[ABOUT ME]
{about_me}

[PARTNER PREFERENCES]
{partner_preferences}

Image URL: {safe_image_url}
"""

    user_prompt = f"""
The following is the user's biodata information:

{structured_block}

Generate a **complete HTML5 biodata** page.

############################################
## GLOBAL REQUIREMENTS
############################################
- Mobile-first, responsive, scrolling layout.
- Card centered on larger screens, full-width-ish on mobile.
- Use this approximate layout:

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

- Do NOT draw any vertical colored pipe/line next to headings.

############################################
## BASIC DETAILS MINI CARDS
############################################
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
- Name (if provided)
- Date of Birth
- Age (value is <span id="calculated-age"></span>)
- Current Location (if provided)
- Job Role **ONLY IF** “Job Role Present: yes”. If "no", omit the card.

############################################
## DYNAMIC AGE (JS)
############################################
In the HTML body (near the bottom), you must include:

<script>
  const dobString = "{safe_dob}";
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

############################################
## SOCIAL PROFILES 💜 (ROBUST & UNBREAKABLE)
############################################
You are given **Social Handles Raw Text** which is arbitrary user text. It may be:
- Empty
- Single handle like: `Instagram: billi`
- Multiple handles:
    `Instagram: billi, LinkedIn : https://linkedin.com/in/billi,
     Snapchat billisnap Tiktok: @billi`
- Or any messy combination, with extra spaces/newlines.

RULES (MUST FOLLOW):

1. If “Social Handles Present” is "no" or the raw text is "(none provided)":
   → Do NOT render a “Social Profiles 💜” section at all.

2. Never treat this user text as HTML.
   - Do NOT insert it inside HTML tags (like inside an `<a>` tag).
   - Only ever place it as text content inside `<span>` or `<li>`.
   - It is already HTML-escaped (using &lt;, &gt;, &amp;), so just output it as plain text.

3. Try to parse platforms **only by keyword**, case-insensitive:
   - contains "instagram" → Instagram 📸
   - contains "linkedin" → LinkedIn 💼
   - contains "facebook" → Facebook 👍
   - contains "snapchat" → Snapchat 👻
   - contains "tiktok" or "tik tok" → TikTok 🎵

4. Splitting into entries:
   - First, replace newlines with commas conceptually.
   - Then split by commas.
   - Trim surrounding whitespace from each piece.
   - Ignore pieces that are now empty.

5. For each non-empty piece:
   - Detect platform keyword (as above). If none match, label it as “Profile ⭐”.
   - Do **NOT** try to be too clever; if unsure, just show the text under “Profile ⭐”.
   - Render as:

     <li>
       <span class="social-label">📸 Instagram:</span>
       <span class="social-text">billi</span>
     </li>

   - Use this CSS:

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

     .social-text {{
       font-weight: 500;
     }}

6. Clickable URLs (optional but MUST be safe):
   - Only treat a value as a URL and wrap in <a> if:
       - it starts with "http://" or "https://" or "www."
       - AND it contains no spaces or quotes.
   - In that case:

     <a href="THE_URL" class="social-link" target="_blank" rel="noopener noreferrer">THE_URL</a>

   - .social-link {{
       color: #7a35d2;
       text-decoration: none;
       font-weight: 500;
     }}
     .social-link:hover {{
       text-decoration: underline;
     }}

7. If you cannot confidently parse the text into multiple entries:
   - Render ONE list item:

     <li>
       <span class="social-label">Social:</span>
       <span class="social-text">FULL_RAW_TEXT_HERE</span>
     </li>

   - This way, the HTML NEVER breaks, regardless of what the user typed.

############################################
## ABOUT ME, INTERESTS, PARTNER PREFS
############################################
- Use ABOUT ME and PARTNER PREFERENCES text, lightly polished.
- Extract interests/hobbies into .badge elements as before.
- Tone: dating-app friendly but family-shareable.

############################################
## FOOTER
############################################
Centered text:
“Share this profile with someone special 💜”

############################################
## HTML SKELETON
############################################
Return a full HTML5 page:

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_name} - Biodata</title>
  <style>
    /* all CSS here, including .card, .details-grid, .badge, .social-list, etc. */
  </style>
</head>
<body>
  <div class="card">
    <!-- hero + sections here -->
  </div>
  <!-- age script here -->
</body>
</html>

CRITICAL RULES:
- ONLY output raw HTML (no backticks, no Markdown).
- Never echo user social text as raw HTML; it is already escaped, treat as plain text.
- If parsing social text is confusing, fall back to the simple “one <li> with full text” approach.
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

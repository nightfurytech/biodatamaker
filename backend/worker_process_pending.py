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
    - Social text is robust and can’t break HTML
    - Tight, consistent spacing between headings & content
    - Always shows an “Interests & Hobbies” header above badges
    """

    if not (50 <= count_words(about_me) <= 250):
        raise ValueError("'about_me' must be 50–250 words.")
    if not (50 <= count_words(partner_preferences) <= 250):
        raise ValueError("'partner_preferences' must be 50–250 words.")

    job_role_present = bool(job_role.strip())
    socials_present = bool(social_handles_csv.strip())

    # Escape anything dangerous
    safe_name = html.escape(name or "")
    safe_dob = html.escape(dob or "")
    safe_job_role = html.escape(job_role or "")
    safe_location = html.escape(location or "")
    safe_social_text = html.escape(social_handles_csv or "")
    safe_image_url = html.escape(image_url or "")

    system_prompt = (
        "You are an expert UI/UX designer who builds modern, romantic, premium, "
        "dating-app-style biodata pages in pure HTML+CSS. "
        "You must output ONLY valid HTML. No Markdown, no comments."
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

Generate a complete, mobile-first **HTML5 biodata page**.

############################################
## GLOBAL LAYOUT & TYPOGRAPHY
############################################
- Mobile-first, scrolling layout (no full-page vertical centering).
- Center card on larger screens.
- Use this base:

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

- NO vertical colored line/pipe next to headings.

############################################
## CONSISTENT SECTION SPACING (IMPORTANT)
############################################
Define sections and text styles so that headings and paragraphs are close together,
without huge gaps:

.section {{
  margin-top: 28px;
}}

.section-title {{
  font-size: 1.4rem;
  font-weight: 600;
  color: #6a1fb4;
  margin: 0 0 8px 0;   /* small gap below heading */
}}

.section-text {{
  margin: 0;           /* NO large margin-top */
  line-height: 1.7;
  font-size: 0.98rem;
}}

.section + .section {{
  margin-top: 32px;    /* consistent spacing between sections */
}}

- Do NOT add extra padding-top or big margin-top on the first paragraph.
- Do NOT indent paragraphs with large left padding or text-indent.

############################################
## HERO SECTION
############################################
Centered hero with:
- Circular profile image (140px mobile → 170px desktop) with purple glow.
- Name in bold.
- Short dating-style tagline.
- 2–3 line highlight summary in a <p class="section-text">.

############################################
## BASIC DETAILS AS MINI CARDS
############################################
Use:

.details-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
  margin-top: 12px;
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
- Job Role ONLY IF Job Role Present is "yes". Otherwise omit that card.

############################################
## DYNAMIC AGE (JS)
############################################
In the HTML body (near bottom), include:

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
## ABOUT ME SECTION
############################################
Must follow this structure, with tight spacing:

<section class="section">
  <h2 class="section-title">About Me</h2>
  <p class="section-text">...</p>
  <!-- optional second <p class="section-text">...</p> -->
</section>

- NO extra wrapper between h2 and first paragraph.
- No large vertical gap between the heading and the text.

############################################
## INTERESTS & HOBBIES (MANDATORY HEADER)
############################################
Immediately after About Me, create a dedicated section:

<section class="section">
  <h2 class="section-title">Interests &amp; Hobbies</h2>
  <div class="badge-list">
    <!-- badges here -->
  </div>
</section>

- The heading “Interests &amp; Hobbies” is **mandatory**.
- It must appear directly above the badges (no huge gap, no missing heading).
- Use badges extracted from ABOUT ME text:

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

############################################
## PARTNER PREFERENCES SECTION
############################################
Follow the same spacing pattern:

<section class="section">
  <h2 class="section-title">Partner Preferences</h2>
  <p class="section-text">...</p>
  <!-- optional second paragraph -->
</section>

NO huge gap between heading and text.

############################################
## SOCIAL PROFILES 💜 (ROBUST)
############################################
You are given: Social Handles Raw Text (already HTML-escaped).

- If “Social Handles Present” is "no" or raw text is "(none provided)":
  → Do NOT render the Social Profiles section.

- Otherwise, render:

<section class="section">
  <h2 class="section-title">Social Profiles 💜</h2>
  <ul class="social-list">
    <!-- one <li> per handle -->
  </ul>
</section>

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

.social-link {{
  color: #7a35d2;
  text-decoration: none;
  font-weight: 500;
}}
.social-link:hover {{
  text-decoration: underline;
}}

Parsing rules (must be SAFE):
- Raw text may be anything (Instagram, LinkedIn, Snapchat, TikTok, messy commas, etc.).
- Treat it as plain text, never as HTML.
- Split on commas/newlines → trim whitespace → skip empty pieces.
- Detect platform by keyword (instagram, linkedin, facebook, snapchat, tiktok).
- If something looks like a URL (starts with http://, https://, or www. and has no spaces/quotes):
    wrap just that URL in <a class="social-link">, otherwise keep plain text.
- If parsing is confusing, fallback to ONE <li>:
    <li><span class="social-label">Social:</span><span class="social-text">FULL_RAW_TEXT</span></li>

This way, the HTML CANNOT break no matter what the user typed.

############################################
## FOOTER
############################################
At the end of the card:

<div class="section footer-note">
  Share this profile with someone special 💜
</div>

############################################
## HTML SHELL
############################################
Return a full HTML5 document:

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_name} - Biodata</title>
  <style>
    /* all CSS from above + hero styles, etc. */
  </style>
</head>
<body>
  <div class="card">
    <!-- hero, basic details, sections -->
  </div>
  <!-- age script -->
</body>
</html>

RULES:
- ONLY output raw HTML (no Markdown, no ```).
- Do NOT invent job role or socials if marked "(not provided)".
- Maintain tight, consistent vertical spacing: small gap between h2 and first paragraph.
- Always include the “Interests &amp; Hobbies” heading above badges if badges exist.
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

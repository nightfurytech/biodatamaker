# supabase_client.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()  # loads .env into os.environ

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
BUCKET_NAME = "biodata-images"


def upload_html(unique_id: str, html: str) -> str:
    path = f"biodatafiles/{unique_id}.html"  # same path as placeholder, will overwrite
    supabase.storage.from_(BUCKET_NAME).upload(
        path=path,
        file=html.encode("utf-8"),
        file_options={"content-type": "text/html", "upsert": "true"},
    )
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)
    return public_url

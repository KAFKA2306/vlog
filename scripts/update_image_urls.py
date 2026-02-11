import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(url, key)
photos_dir = Path("frontend/reader/public/photos")
infographics_dir = Path("frontend/reader/public/infographics")
for photo in photos_dir.glob("*.png"):
    date = photo.stem.replace(" copy", "")
    if "_" in date:
        continue
    image_url = f"/photos/{photo.name}"
    supabase.table("novels").update({"image_url": image_url}).eq("date", date).execute()
    print(f"novels: {date} -> {image_url}")
for infographic in infographics_dir.glob("*_summary.png"):
    date = infographic.stem.replace("_summary", "")
    image_url = f"/infographics/{infographic.name}"
    supabase.table("daily_entries").update({"image_url": image_url}).eq(
        "date", date
    ).execute()
    print(f"daily_entries: {date} -> {image_url}")

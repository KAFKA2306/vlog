from pathlib import Path

from supabase import create_client
from vlog_capture.infrastructure.settings import settings

if not settings.supabase_url or not settings.supabase_service_role_key:
    raise RuntimeError("Supabase configuration is required")

supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)

photos_dir = Path("apps/reader/public/photos")
infographics_dir = Path("apps/reader/public/infographics")

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

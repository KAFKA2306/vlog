import logging
import sys
from pathlib import Path

# Add project root to sys.path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.infrastructure.ai import ImageGenerator, Novelizer  # noqa: E402
from src.infrastructure.repositories import SupabaseRepository  # noqa: E402
from src.infrastructure.settings import settings  # noqa: E402
from src.use_cases.build_novel import BuildNovelUseCase  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting check for missing content...")

    # Ensure directories exist
    settings.summary_dir.mkdir(parents=True, exist_ok=True)
    settings.novel_out_dir.mkdir(parents=True, exist_ok=True)
    settings.photo_dir.mkdir(parents=True, exist_ok=True)

    # Initialize use cases and services
    # Note: We need to instantiate the concrete classes for the use case
    novelizer = Novelizer()
    image_generator = ImageGenerator()
    build_novel_use_case = BuildNovelUseCase(novelizer, image_generator)
    supabase_repo = SupabaseRepository()

    # Get all summary dates
    summary_files = list(settings.summary_dir.glob("*_summary.txt"))
    logger.info(f"Found {len(summary_files)} summary files.")

    dates_to_process = []

    for summary_file in summary_files:
        # Expected format: YYYYMMDD_summary.txt
        parts = summary_file.stem.split("_")
        if len(parts) < 1 or not parts[0].isdigit() or len(parts[0]) != 8:
            continue

        date_str = parts[0]

        # Check specific daily summary format (YYYYMMDD_summary.txt).
        # Ignore session summaries like 20251120_205733_summary.txt.
        # Repositories sync only allows exact YYYYMMDD_summary.txt.

        normalized_stem = summary_file.stem.replace("_summary", "")
        if "_" in normalized_stem:
            # e.g. 20251120_205733
            continue

        dates_to_process.append(date_str)

    import traceback

    dates_to_process.sort()
    logger.info(f"Found {len(dates_to_process)} valid daily summary dates.")

    for date_str in dates_to_process:
        novel_path = settings.novel_out_dir / f"{date_str}.md"
        photo_path = settings.photo_dir / f"{date_str}.png"

        novel_exists = novel_path.exists()
        photo_exists = photo_path.exists()

        if novel_exists and photo_exists:
            continue

        logger.info(
            f"Processing {date_str}: Novel={novel_exists}, Photo={photo_exists}"
        )

        if not novel_exists:
            logger.info(f"Generating Novel and Image for {date_str}...")
            # BuildNovelUseCase generates both Novel AND Image
            try:
                build_novel_use_case.execute(date=date_str)
                logger.info(f"Successfully generated content for {date_str}")
            except Exception as e:
                logger.error(f"Failed to generate content for {date_str}: {e}")
                logger.error(traceback.format_exc())

        elif not photo_exists:
            logger.info(
                f"Novel exists but Image missing for {date_str}. Generating Image..."
            )
            try:
                # We can use ImageGenerator directly if we have the novel text
                novel_text = novel_path.read_text(encoding="utf-8")
                # Use the whole text as context for the prompt generator.
                image_generator.generate_from_novel(novel_text, photo_path)
                logger.info(f"Successfully generated image for {date_str}")
            except Exception as e:
                logger.error(f"Failed to generate image for {date_str}: {e}")
                logger.error(traceback.format_exc())

    logger.info("Syncing to Supabase...")
    try:
        supabase_repo.sync()
        logger.info("Sync complete.")
    except Exception as e:
        logger.error(f"Sync failed: {e}")

    logger.info("Done.")


if __name__ == "__main__":
    main()

import logging

from vlog_capture.infrastructure.ai import ImageGenerator, Novelizer
from vlog_capture.infrastructure.graph_storage import GraphStorage
from vlog_capture.infrastructure.repositories import SupabaseRepository
from vlog_capture.infrastructure.settings import settings
from vlog_capture.portability import runtime_directories
from vlog_capture.use_cases.build_novel import BuildNovelUseCase

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting check for missing content...")

    settings.summary_dir.mkdir(parents=True, exist_ok=True)
    settings.novel_out_dir.mkdir(parents=True, exist_ok=True)
    settings.photo_dir.mkdir(parents=True, exist_ok=True)

    graph_path = runtime_directories().cache / "graph" / "graph.jsonl"
    novelizer = Novelizer()
    image_generator = ImageGenerator()
    graph_storage = GraphStorage(graph_path)
    build_novel_use_case = BuildNovelUseCase(novelizer, image_generator, graph_storage)
    supabase_repo = SupabaseRepository()

    summary_files = list(settings.summary_dir.glob("*_summary.txt"))
    logger.info("Found %d summary files.", len(summary_files))

    dates_to_process: list[str] = []
    for summary_file in summary_files:
        parts = summary_file.stem.split("_")
        if not parts or not parts[0].isdigit() or len(parts[0]) != 8:
            continue

        date_str = parts[0]
        normalized_stem = summary_file.stem.replace("_summary", "")
        if "_" in normalized_stem:
            continue
        dates_to_process.append(date_str)

    dates_to_process.sort()
    logger.info("Found %d valid daily summary dates.", len(dates_to_process))

    for date_str in dates_to_process:
        novel_path = settings.novel_out_dir / f"{date_str}.md"
        photo_path = settings.photo_dir / f"{date_str}.png"

        novel_exists = novel_path.exists()
        photo_exists = photo_path.exists()
        if novel_exists and photo_exists:
            continue

        logger.info(
            "Processing %s: Novel=%s, Photo=%s",
            date_str,
            novel_exists,
            photo_exists,
        )

        if not novel_exists:
            logger.info("Generating Novel and Image for %s...", date_str)
            build_novel_use_case.execute(date=date_str)
            logger.info("Successfully generated content for %s", date_str)
        elif not photo_exists:
            logger.info(
                "Novel exists but Image missing for %s. Generating Image...", date_str
            )
            novel_text = novel_path.read_text(encoding="utf-8")
            image_generator.generate_from_novel(novel_text, photo_path)
            logger.info("Successfully generated image for %s", date_str)

    logger.info("Syncing to Supabase...")
    supabase_repo.sync()
    logger.info("Sync complete.")
    logger.info("Done.")


if __name__ == "__main__":
    main()

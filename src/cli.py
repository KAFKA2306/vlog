import argparse

from src.infrastructure.file_repository import FileRepository
from src.infrastructure.preprocessor import TranscriptPreprocessor
from src.infrastructure.summarizer import Summarizer
from src.infrastructure.supabase_repository import SupabaseRepository
from src.infrastructure.transcriber import Transcriber
from src.use_cases.process_recording import ProcessRecordingUseCase


def cmd_process(args):
    use_case = ProcessRecordingUseCase(
        transcriber=Transcriber(),
        preprocessor=TranscriptPreprocessor(),
        summarizer=Summarizer(),
        storage=SupabaseRepository(),
        file_repository=FileRepository(),
    )
    use_case.execute(args.file)


def cmd_novel(args):
    from src.infrastructure.image_generator import ImageGenerator
    from src.infrastructure.novelizer import Novelizer
    from src.use_cases.build_novel import BuildNovelUseCase

    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator())
    novel_path = use_case.execute(args.date)

    if novel_path:
        print(f"章を追加: {novel_path}")
        SupabaseRepository().sync()
    else:
        print("Novel Builder is disabled")


def cmd_sync(args):
    SupabaseRepository().sync()
    print("Synced with Supabase")


def cmd_image_generate(args):
    from pathlib import Path

    from src.infrastructure.image_generator import ImageGenerator

    novel_path = Path(args.novel_file)
    if not novel_path.exists():
        print(f"Error: Novel file not found at {novel_path}")
        return

    novel_content = novel_path.read_text(encoding="utf-8")

    output_path = (
        Path(args.output_file)
        if args.output_file
        else novel_path.parent / (novel_path.stem + ".png")
    )

    print(f"Generating image for {novel_path} to {output_path}...")
    image_generator = ImageGenerator()
    image_generator.generate_from_novel(novel_content, output_path)
    print(f"Image generated successfully to {output_path}")


def main():
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    p_process = subparsers.add_parser("process", help="Process audio file")
    p_process.add_argument("--file", help="Path to audio file")

    p_novel = subparsers.add_parser("novel", help="Generate novel chapter")
    p_novel.add_argument("--date", help="Target date (YYYYMMDD)")
    p_novel.add_argument("--out", help="Output filename (unused)")

    subparsers.add_parser("sync", help="Sync data to Supabase")

    p_image_generate = subparsers.add_parser(
        "image-generate", help="Generate an image from a novel file"
    )
    p_image_generate.add_argument(
        "--novel-file", required=True, help="Path to the novel markdown file"
    )
    p_image_generate.add_argument(
        "--output-file", help="Path to the output image file (optional)"
    )

    args = parser.parse_args()

    if args.command == "process":
        cmd_process(args)
    elif args.command == "novel":
        cmd_novel(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "image-generate":
        cmd_image_generate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

import argparse

from src.infrastructure.ai import (
    ImageGenerator,
    JulesClient,
    Novelizer,
    Summarizer,
)
from src.infrastructure.repositories import (
    FileRepository,
    SupabaseRepository,
)
from src.infrastructure.system import Transcriber, TranscriptPreprocessor
from src.use_cases.build_novel import BuildNovelUseCase
from src.use_cases.process_recording import ProcessRecordingUseCase


def cmd_process(args):
    use_case = ProcessRecordingUseCase(
        transcriber=Transcriber(),
        preprocessor=TranscriptPreprocessor(),
        summarizer=Summarizer(),
        storage=SupabaseRepository(),
        file_repository=FileRepository(),
        novelizer=Novelizer(),
        image_generator=ImageGenerator(),
    )
    use_case.execute(args.file)


def cmd_novel(args):
    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator())
    novel_path = use_case.execute(args.date)

    if novel_path:
        print(f"章を追加: {novel_path}")
        SupabaseRepository().sync()
    else:
        print("要約ファイルが見つかりません")


def cmd_sync(args):
    SupabaseRepository().sync()
    print("Synced with Supabase")


def cmd_image_generate(args):
    from pathlib import Path

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

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating image for {novel_path} to {output_path}...")
    image_generator = ImageGenerator()
    image_generator.generate_from_novel(novel_content, output_path)
    print(f"Image generated successfully to {output_path}")


def cmd_jules(args):
    from src.infrastructure.repositories import TaskRepository

    repo = TaskRepository()

    if args.action == "add":
        if not args.content:
            print("Error: content is required for 'add'")
            return

        print(f"Jules is thinking about: {args.content}...")
        try:
            client = JulesClient()
            task_data = client.parse_task(args.content)
        except ValueError as e:
            print(f"Configuration Error: {e}")
            return
        except Exception as e:
            print(f"AI Error: {e}")
            task_data = {"title": args.content, "priority": "medium", "tags": []}

        new_task = repo.add(task_data)
        print(
            f"Task added: [{new_task['priority'].upper()}] {new_task['title']} "
            f"(ID: {new_task['id'][:8]})"
        )

    elif args.action == "list":
        tasks = repo.list_pending()
        if not tasks:
            print("No pending tasks.")
            return
        print(f"Found {len(tasks)} pending tasks:")
        for t in tasks:
            print(f"- [{t['id'][:8]}] {t['title']} ({t.get('priority', 'normal')})")

    elif args.action == "done":
        if not args.task_id:
            print("Error: task_id is required for 'done'")
            return
        completed = repo.complete(args.task_id)
        if completed:
            print(f"Completed: {completed['title']}")
        else:
            print("Task not found.")


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

    p_jules = subparsers.add_parser("jules", help="Manage mini-tasks with Jules AI")
    p_jules.add_argument(
        "action", choices=["add", "list", "done"], help="Action to perform"
    )
    p_jules.add_argument(
        "content", nargs="?", help="Task content (for add) or Task ID (for done)"
    )

    args = parser.parse_args()
    if args.command == "jules":
        if args.action == "done":
            args.task_id = args.content
        cmd_jules(args)
    elif args.command == "process":
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

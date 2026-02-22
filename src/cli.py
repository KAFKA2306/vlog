import argparse
import re
import shutil
import torch
import logging
from pathlib import Path
from src.infrastructure.ai import ImageGenerator, Summarizer
from src.infrastructure.repositories import (
    FileRepository,
    SupabaseRepository,
    TaskRepository,
)
from src.infrastructure.system import Transcriber, TranscriptPreprocessor
from src.use_cases.build_novel import BuildNovelUseCase
from src.use_cases.process_recording import ProcessRecordingUseCase
from src.models import RecordingSession

logger = logging.getLogger(__name__)

def cmd_process(args):
    from datetime import datetime
    path = Path(args.file)
    match = re.search(r"(\d{8}_\d{6})", path.name)
    start_time = (
        datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
        if match
        else datetime.now()
    )
    use_case = ProcessRecordingUseCase(
        transcriber=Transcriber(),
        preprocessor=TranscriptPreprocessor(),
        summarizer=Summarizer(),
        storage=SupabaseRepository(),
        file_repository=FileRepository(),
        diarizer=None,
    )
    use_case.execute_session(
        RecordingSession(start_time=start_time, file_paths=(str(path),))
    )

def cmd_novel(args):
    use_case = BuildNovelUseCase(Summarizer(), ImageGenerator())
    use_case.execute(args.date)
    SupabaseRepository().sync()

def cmd_sync(args):
    SupabaseRepository().sync()

def cmd_image_generate(args):
    novel_path = Path(args.novel_file)
    content = novel_path.read_text(encoding="utf-8")
    output_path = (
        Path(args.output_file)
        if args.output_file
        else novel_path.parent / (novel_path.stem + ".png")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ImageGenerator().generate_from_novel(content, output_path)

def cmd_transcribe(args):
    Transcriber().transcribe_and_save(args.file)

def cmd_summarize(args):
    file_repo = FileRepository()
    summarizer = Summarizer()
    if args.date:
        transcript_dir = Path("data/transcripts")
        files = sorted(
            list(transcript_dir.glob(f"cleaned_{args.date}_*.txt"))
        ) or sorted(list(transcript_dir.glob(f"{args.date}_*.txt")))
        combined_text = "\n\n".join(file_repo.read(str(f)) for f in files)
        file_repo.save_summary(
            summarizer.generate_novel(combined_text, args.date), args.date
        )
    elif args.file:
        text = file_repo.read(args.file)
        date_str = Path(args.file).stem[:8]
        file_repo.save_summary(summarizer.generate_novel(text, date_str), date_str)

def cmd_pending(args):
    transcript_dir, summary_dir, novel_dir, recording_dir = (
        Path("data/transcripts"),
        Path("data/summaries"),
        Path("data/novels"),
        Path("data/recordings"),
    )
    file_repo = FileRepository()
    for f in recording_dir.glob("*"):
        if (
            f.suffix.lower() in [".wav", ".flac", ".mp3"]
            and not (transcript_dir / f"{f.stem}.txt").exists()
        ):
            t, p = Transcriber().transcribe_and_save(str(f))
            file_repo.save_text(
                str(Path(p).with_name(f"cleaned_{Path(p).name}")),
                TranscriptPreprocessor().process(t),
            )

    dates = sorted(
        {
            match.group(1)
            for f in transcript_dir.glob("*.txt")
            if (match := re.search(r"(\d{8})", f.stem))
        }
    )
    summarizer = Summarizer()
    for d in dates:
        if not (summary_dir / f"{d}_summary.txt").exists():
            files = sorted(list(transcript_dir.glob(f"cleaned_{d}_*.txt"))) or sorted(
                list(transcript_dir.glob(f"{d}_*.txt"))
            )
            file_repo.save_summary(
                summarizer.generate_novel(
                    "\n\n".join(file_repo.read(str(f)) for f in files), d
                ),
                d,
            )
        if not (novel_dir / f"{d}.md").exists():
            BuildNovelUseCase(Summarizer(), ImageGenerator()).execute(d)
    SupabaseRepository().sync()

def cmd_repair(args):
    from src.infrastructure.agents.pipeline_repair import PipelineRepairAgent
    PipelineRepairAgent().run()

def cmd_doctor(args):
    import shutil
    import torch
    import os
    print("■ System Dependency Check")
    for cmd in ["ffmpeg", "sqlite3"]:
        path = shutil.which(cmd)
        print(f"- {cmd}: {'OK (' + path + ')' if path else 'MISSING'}")
    
    print("\n■ Hardware Check")
    cuda = torch.cuda.is_available()
    print(f"- CUDA Available: {cuda}")
    if cuda:
        from pathlib import Path
        print(f"- Device: {torch.cuda.get_device_name(0)}")
        print(f"- VRAM: {torch.cuda.get_device_properties(0).total_memory // (1024**2)} MiB")
        
        base = Path(__file__).resolve().parent.parent.parent
        cudnn_paths = list((base / ".venv").rglob("nvidia/cudnn/lib"))
        if cudnn_paths:
            print(f"- cuDNN Lib Path: {cudnn_paths[0]}")
    
    print(f"\n- LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'NOT SET')}")

def cmd_setup(args):
    for d in ["data/recordings", "data/transcripts", "data/summaries", "data/novels", "data/photos", "data/logs"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("Directories initialized.")

def cmd_curator(args):
    from src.use_cases.evaluate import EvaluateDailyContentUseCase
    EvaluateDailyContentUseCase().execute(args.date)

def cmd_dashboard(args):
    from src.infrastructure.dashboard import Dashboard
    Dashboard().render()

def main():
    from src.main import setup_logging
    setup_logging()

    parser = argparse.ArgumentParser(description="VLog CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    subparsers.add_parser("process").add_argument("--file")
    subparsers.add_parser("novel").add_argument("--date")
    subparsers.add_parser("sync")
    p_img = subparsers.add_parser("image-generate")
    p_img.add_argument("--novel-file", required=True)
    p_img.add_argument("--output-file")
    subparsers.add_parser("transcribe").add_argument("--file", required=True)
    p_sum = subparsers.add_parser("summarize")
    p_sum.add_argument("--file")
    p_sum.add_argument("--date")
    subparsers.add_parser("pending")
    subparsers.add_parser("repair")
    subparsers.add_parser("doctor")
    subparsers.add_parser("setup")
    p_cur = subparsers.add_parser("curator")
    p_cur.add_argument("action", choices=["eval"])
    p_cur.add_argument("--date")
    subparsers.add_parser("dashboard")

    args = parser.parse_args()
    
    cmds = {
        "process": cmd_process,
        "novel": cmd_novel,
        "sync": cmd_sync,
        "image-generate": cmd_image_generate,
        "transcribe": cmd_transcribe,
        "summarize": cmd_summarize,
        "pending": cmd_pending,
        "repair": cmd_repair,
        "doctor": cmd_doctor,
        "setup": cmd_setup,
        "curator": cmd_curator,
        "dashboard": cmd_dashboard,
    }
    
    if args.command in cmds:
        cmds[args.command](args)

if __name__ == "__main__":
    main()

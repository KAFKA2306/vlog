import shutil
import subprocess
from pathlib import Path
from typing import Tuple

import psutil
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class Dashboard:
    def __init__(self):
        self.console = Console()
        self.data_dir = Path("data")

    def render(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )

        layout["header"].update(self._make_header())
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        layout["left"].split_column(
            Layout(name="services"),
            Layout(name="system"),
        )
        layout["right"].split_column(
            Layout(name="pipeline"),
            Layout(name="recent"),
        )

        layout["services"].update(self._make_services_panel())
        layout["system"].update(self._make_system_panel())
        layout["pipeline"].update(self._make_pipeline_panel())
        layout["recent"].update(self._make_recent_panel())
        layout["footer"].update(self._make_footer())

        self.console.print(layout)

    def _make_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row("[b]VLog Management Dashboard[/b]")
        return Panel(grid, style="white on blue")

    def _make_footer(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row("Press [b]Ctrl+C[/b] to exit")
        return Panel(grid, style="white on blue")

    def _get_service_status(self, service_name: str) -> Tuple[str, str]:
        if not shutil.which("systemctl"):
            return "Unknown", "red"

        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", service_name],
                capture_output=True,
                text=True,
            )
            status = result.stdout.strip()
            if status == "active":
                return "Active", "green"
            elif status == "inactive":
                return "Inactive", "yellow"
            elif status == "failed":
                return "Failed", "red"
            else:
                return status, "white"
        except Exception:
            return "Error", "red"

    def _make_services_panel(self) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Service")
        table.add_column("Status")

        services = ["vlog.service", "vlog-daily.timer"]
        for service in services:
            status, color = self._get_service_status(service)
            table.add_row(service, Text(status, style=color))

        return Panel(table, title="Systemd Services", border_style="blue")

    def _make_system_panel(self) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Metric")
        table.add_column("Value")

        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        table.add_row("CPU Usage", f"{cpu}%")
        table.add_row("Memory Usage", f"{memory}%")
        table.add_row("Disk Usage", f"{disk}%")

        return Panel(table, title="System Metrics", border_style="blue")

    def _count_files(self, subdir: str, pattern: str) -> int:
        path = self.data_dir / subdir
        if not path.exists():
            return 0
        return len(list(path.glob(pattern)))

    def _make_pipeline_panel(self) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Stage")
        table.add_column("Count")

        recordings = self._count_files("recordings", "*")
        transcripts = self._count_files("transcripts", "*.txt")
        summaries = self._count_files("summaries", "*_summary.txt")
        novels = self._count_files("novels", "*.md")
        photos = self._count_files("photos", "*.png")

        table.add_row("Recordings", str(recordings))
        table.add_row("Transcripts", str(transcripts))
        table.add_row("Summaries", str(summaries))
        table.add_row("Novels", str(novels))
        table.add_row("Photos", str(photos))

        return Panel(table, title="Pipeline Health", border_style="green")

    def _make_recent_panel(self) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Date")
        table.add_column("Novel")
        table.add_column("Photo")

        # Gather last 10 days from filenames in novels or photos
        dates = set()

        novel_dir = self.data_dir / "novels"
        if novel_dir.exists():
            for f in novel_dir.glob("*.md"):
                if f.stem.isdigit() and len(f.stem) == 8:
                    dates.add(f.stem)

        photo_dir = self.data_dir / "photos"
        if photo_dir.exists():
            for f in photo_dir.glob("*.png"):
                if f.stem.isdigit() and len(f.stem) == 8:
                    dates.add(f.stem)

        sorted_dates = sorted(list(dates), reverse=True)[:10]

        if not sorted_dates:
            return Panel(
                "No content found",
                title="Daily Content Status",
                border_style="green",
            )

        for date_str in sorted_dates:
            novel_path = self.data_dir / "novels" / f"{date_str}.md"
            photo_path = self.data_dir / "photos" / f"{date_str}.png"

            novel_status = "✅" if novel_path.exists() else "❌"
            photo_status = "✅" if photo_path.exists() else "❌"

            # Format date for readability (YYYYMMDD -> YYYY-MM-DD)
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

            table.add_row(formatted_date, novel_status, photo_status)

        return Panel(table, title="Daily Content Status", border_style="green")

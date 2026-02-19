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
        layout["left"].split_column(Layout(name="services"), Layout(name="system"))
        layout["right"].split_column(Layout(name="pipeline"), Layout(name="recent"))
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
        result = subprocess.run(
            ["systemctl", "--user", "is-active", service_name],
            capture_output=True,
            text=True,
        )
        status = result.stdout.strip()
        color = (
            "green"
            if status == "active"
            else "yellow"
            if status == "inactive"
            else "red"
            if status == "failed"
            else "white"
        )
        return status.capitalize(), color

    def _make_services_panel(self) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Service")
        table.add_column("Status")
        for service in ["vlog.service", "vlog-daily.timer"]:
            status, color = self._get_service_status(service)
            table.add_row(service, Text(status, style=color))
        return Panel(table, title="Systemd Services", border_style="blue")

    def _make_system_panel(self) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Metric")
        table.add_column("Value")
        table.add_row("CPU Usage", f"{psutil.cpu_percent()}%")
        table.add_row("Memory Usage", f"{psutil.virtual_memory().percent}%")
        table.add_row("Disk Usage", f"{psutil.disk_usage('/').percent}%")
        return Panel(table, title="System Metrics", border_style="blue")

    def _count_files(self, subdir: str, pattern: str) -> int:
        path = self.data_dir / subdir
        return len(list(path.glob(pattern))) if path.exists() else 0

    def _make_pipeline_panel(self) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Stage")
        table.add_column("Count")
        table.add_row("Recordings", str(self._count_files("recordings", "*")))
        table.add_row("Transcripts", str(self._count_files("transcripts", "*.txt")))
        table.add_row("Summaries", str(self._count_files("summaries", "*_summary.txt")))
        table.add_row("Novels", str(self._count_files("novels", "*.md")))
        table.add_row("Photos", str(self._count_files("photos", "*.png")))
        return Panel(table, title="Pipeline Health", border_style="green")

    def _make_recent_panel(self) -> Panel:
        dates = set()
        for d in ["novels", "photos"]:
            p = self.data_dir / d
            if p.exists():
                for f in p.glob("*"):
                    if f.stem.isdigit() and len(f.stem) == 8:
                        dates.add(f.stem)

        sorted_dates = sorted(list(dates), reverse=True)[:10]
        if not sorted_dates:
            return Panel(
                "No content found", title="Daily Content Status", border_style="green"
            )

        table = Table(expand=True, box=None)
        table.add_column("Date")
        table.add_column("Novel")
        table.add_column("Photo")
        for d in sorted_dates:
            novel_ok = (self.data_dir / "novels" / f"{d}.md").exists()
            photo_ok = (self.data_dir / "photos" / f"{d}.png").exists()
            table.add_row(
                f"{d[:4]}-{d[4:6]}-{d[6:]}",
                "✅" if novel_ok else "❌",
                "✅" if photo_ok else "❌",
            )
        return Panel(table, title="Daily Content Status", border_style="green")

#!/usr/bin/env python3
"""Import signed-off Tiny Tapeout tiles into projects/ for the UofA CI2609 chip."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/Users/jeffdi/Projects/nydesign/_uofa_ci2609_src")
CI2605 = Path("/Users/jeffdi/Projects/nydesign/nydesign-ci2605")
KLAYOUT = "/Applications/klayout.app/Contents/MacOS/klayout"
SOURCE_REPO = "https://github.com/parsamrf/AI-HDL-Tape-out-Chipfoundry"
SOURCE_COMMIT = "a02bebb84456e48a6f411218cd36dfa155a9385a"

DESIGNS = [
    {
        "folder": "uofa-traffic",
        "macro": "tt_um_uofa_traffic",
        "gds": "gds/tt_um_uofa_traffic.gds",
        "sort_id": 1779555000001,
        "title": "Maestros WiFi Smart Traffic-Light Controller",
    },
    {
        "folder": "itims-spi",
        "macro": "tt_um_itims_spi",
        "gds": "gds/tt_um_itims_spi.gds",
        "sort_id": 1779555000002,
        "title": "ITIMS Secure Autonomous SPI Master",
    },
    {
        "folder": "necrl-aes128",
        "macro": "tt_um_necrl_aes128",
        "gds": "gds/tt_um_necrl_aes128.gds",
        "sort_id": 1779555000003,
        "title": "NeCRL AES-128 Encryption Peripheral",
    },
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def write_powered_blackbox(path: Path, macro: str) -> None:
    path.write_text(
        f"""module {macro} (
    input clk,
    input ena,
    input rst_n,
    inout VPWR,
    inout VGND,
    input [7:0] ui_in,
    input [7:0] uio_in,
    output [7:0] uio_oe,
    output [7:0] uio_out,
    output [7:0] uo_out
);
endmodule
"""
    )


def metrics_to_csv(metrics_json: Path, out_csv: Path) -> dict:
    data = json.loads(metrics_json.read_text())
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Metric", "Value"])
        for key, value in data.items():
            writer.writerow([key, value])
    return data


def write_synth_stats(path: Path, macro: str, cell_count: int, area: float) -> None:
    path.write_text(
        f"""=== {macro} ===

Number of cells:            {cell_count}

       Chip area for module '\\{macro}': {area:.6f}
"""
    )


def write_docs(path: Path, title: str, description: str, author: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""## How it works

{description}

## How to test

See the pinout in `info.yaml`. This tile was imported from the signed-off
University of Arizona / AI-HDL collection and uses the standard Tiny Tapeout
clock, reset, and `ui`/`uo`/`uio` harness.

## Author

{author}
"""
    )


def import_tt_design(design: dict) -> None:
    src = SRC / design["folder"]
    macro = design["macro"]
    dest = ROOT / "projects" / macro
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    shutil.copy2(src / "info.yaml", dest / "info.yaml")
    license_src = src / "LICENSE"
    if license_src.exists():
        shutil.copy2(license_src, dest / "LICENSE")
    else:
        shutil.copy2(ROOT / "LICENSE", dest / "LICENSE")

    gds_src = src / design["gds"]
    gds_dst = dest / f"{macro}.gds"
    shutil.copy2(gds_src, gds_dst)

    lef_dst = dest / f"{macro}.lef"
    run(
        [
            KLAYOUT,
            "-b",
            "-r",
            str(ROOT / "scripts/gds_to_lef.py"),
            "-rd",
            f"gds={gds_dst}",
            "-rd",
            f"lef={lef_dst}",
            "-rd",
            f"macro={macro}",
        ]
    )
    run(
        [
            KLAYOUT,
            "-b",
            "-r",
            str(ROOT / "scripts/gds_to_oas.py"),
            "-rd",
            f"gds={gds_dst}",
            "-rd",
            f"oas={dest / f'{macro}.oas'}",
        ]
    )

    write_powered_blackbox(dest / f"{macro}.v", macro)

    info = (src / "info.yaml").read_text()
    # Pull author/description from YAML without requiring PyYAML here.
    author = "unknown"
    description = design["title"]
    for line in info.splitlines():
        if line.strip().startswith("author:"):
            author = line.split(":", 1)[1].strip().strip('"')
        if line.strip().startswith("description:"):
            description = line.split(":", 1)[1].strip().strip('"')
    write_docs(dest / "docs/info.md", design["title"], description, author)

    metrics = metrics_to_csv(src / "signoff/metrics.json", dest / "stats/metrics.csv")
    write_synth_stats(
        dest / "stats/synthesis-stats.txt",
        macro,
        int(metrics.get("design__instance__count", 0)),
        float(metrics.get("design__instance__area", 0) or 0),
    )

    (dest / "commit_id.json").write_text(
        json.dumps(
            {
                "app": "uofa-ci2609 import",
                "repo": SOURCE_REPO,
                "commit": SOURCE_COMMIT,
                "workflow_url": None,
                "sort_id": design["sort_id"],
                "flow_version": "LibreLane 3.0.5",
                "source_folder": design["folder"],
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Imported {macro}")


def copy_system_tile(name: str) -> None:
    src = CI2605 / "projects" / name
    dest = ROOT / "projects" / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"Copied system tile {name}")


def main() -> int:
    projects = ROOT / "projects"
    if projects.exists():
        shutil.rmtree(projects)
    projects.mkdir()

    copy_system_tile("tt_um_chip_rom")
    copy_system_tile("tt_um_factory_test")

    factory_commit = ROOT / "projects/tt_um_factory_test/commit_id.json"
    data = json.loads(factory_commit.read_text())
    data["repo"] = "https://github.com/TinyTapeout/ttsky26c-factory-test"
    factory_commit.write_text(json.dumps(data, indent=2) + "\n")

    for design in DESIGNS:
        import_tt_design(design)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Per-cyclone fAPAR zonal-loss statistics.

Run command:

    python scripts\\fapar_zonal_stats.py remal
    python scripts\\fapar_zonal_stats.py sitrang
    python scripts\\fapar_zonal_stats.py midhili
    python scripts\\fapar_zonal_stats.py --all

Reads the before/after fAPAR GeoTIFFs from
data/sample/faapar/<cyclone>/{before,after}/*.tif (one .tif expected in each
subfolder), computes mean fAPAR per Upazila before and after landfall, and
writes fapar_loss_by_upazila.csv / .xlsx to outputs/<cyclone>/FAPAR/.

This reuses the raster preprocessing and zonal-statistics logic in
fapar_processing.py (same scale factor / nodata / valid-range handling) —
it does not duplicate that logic, only adds a per-cyclone CLI and routes
output to outputs/ instead of data/, keeping data/ input-only.
"""

import argparse
import sys
from pathlib import Path

import yaml

# Reuse the existing raster + zonal-stats implementation rather than
# duplicating it — fapar_processing.py already handles scaling, nodata,
# CRS alignment, and the output table.
from fapar_processing import (
    PROJECT_ROOT,
    PARENT_DIR,
    SHAPEFILE,
    process_event_folder,
)


CYCLONES = [
    "remal",
    "sitrang",
    "midhili",
]


def header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def fail(message):
    print(f"\nERROR: {message}")
    sys.exit(1)


def resolve_event_folder(cyclone_key):
    """
    data/sample/faapar/<cyclone>/ is used by default. If the cyclone's
    config file (configs/<cyclone>.yaml) defines a `fapar.directory`
    override, that takes precedence.
    """

    event_folder = PARENT_DIR / cyclone_key

    config_file = (
        PROJECT_ROOT
        / "configs"
        / f"{cyclone_key}.yaml"
    )

    if config_file.is_file():

        with config_file.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        fapar_cfg = cfg.get("fapar", {})
        override = fapar_cfg.get("directory")

        if override:
            event_folder = PROJECT_ROOT / override

    return event_folder


def run_one(cyclone_key):

    cyclone_key = cyclone_key.lower()

    if cyclone_key not in CYCLONES:
        fail(
            f"Unknown cyclone: {cyclone_key}\n"
            f"Available cyclones: {', '.join(CYCLONES)}"
        )

    event_folder = resolve_event_folder(cyclone_key)

    output_dir = (
        PROJECT_ROOT
        / "outputs"
        / cyclone_key
        / "FAPAR"
    )

    header(f"FAPAR ZONAL LOSS — {cyclone_key.upper()}")

    print(f"Repository root : {PROJECT_ROOT}")
    print(f"Event folder    : {event_folder}")
    print(f"ADM3 boundary   : {SHAPEFILE}")
    print(f"Output folder   : {output_dir}")

    if not event_folder.is_dir():
        fail(
            f"fAPAR folder not found for '{cyclone_key}':\n"
            f"{event_folder}\n"
            f"Expected before/ and after/ subfolders with one .tif each."
        )

    if not SHAPEFILE.is_file():
        fail(f"ADM3 shapefile not found:\n{SHAPEFILE}")

    process_event_folder(
        event_folder,
        output_dir=output_dir,
    )

    print()
    print(f"Done. Results written to: {output_dir}")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Compute per-Upazila fAPAR loss (before vs. after landfall) "
            "for a cyclone."
        )
    )

    parser.add_argument(
        "cyclone",
        nargs="?",
        choices=CYCLONES,
        help="Cyclone name: remal, sitrang, or midhili",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run every cyclone with a fAPAR data folder.",
    )

    args = parser.parse_args()

    if args.all:

        header("BATCH FAPAR ZONAL LOSS — ALL CYCLONES")

        for cyclone_key in CYCLONES:

            event_folder = resolve_event_folder(cyclone_key)

            if not event_folder.is_dir():
                print(
                    f"Skipping {cyclone_key}: "
                    f"no fAPAR folder at {event_folder}"
                )
                continue

            run_one(cyclone_key)

        return

    if args.cyclone is None:
        parser.error(
            "Cyclone is required.\n\n"
            "Example:\n"
            "  python scripts\\fapar_zonal_stats.py remal\n\n"
            "Or run every cyclone with fAPAR data available:\n"
            "  python scripts\\fapar_zonal_stats.py --all"
        )

    run_one(args.cyclone)


if __name__ == "__main__":
    main()

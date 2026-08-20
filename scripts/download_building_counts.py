"""
Download district-level building counts from Google Earth Engine for a
given country.

Run command:

    python scripts\\download_building_counts.py "Bangladesh"
    python scripts\\download_building_counts.py "Bangladesh" --export-drive

Replaces the manual "Upzila Based Building Count Download" Earth Engine
Code Editor script (JavaScript, single country, required a manually
uploaded boundary asset) with a parameterized command-line workflow:

  1. Loads the country + district boundary from FAO GAUL (already a public
     Earth Engine asset covering every country - nothing to upload).
  2. Counts building footprints (default: Google Open Buildings V3
     polygons) that fall inside each district.
  3. Pulls the resulting table directly into this machine and saves it as
     CSV/XLSX under outputs/<country>/BuildingCounts/ - no manual Google
     Drive export/download step needed for typical country sizes.

One-time setup (see configs/earth_engine.yaml for details):
  1. Set `project` in configs/earth_engine.yaml to a Google Cloud project
     with the Earth Engine API enabled.
  2. Run `earthengine authenticate` once (or use a service account - see
     the config file).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "earth_engine.yaml"


def header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def fail(message):
    print(f"\nERROR: {message}")
    sys.exit(1)


def load_config(config_path):

    if not config_path.is_file():
        fail(f"Config file not found:\n{config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    required = ["project", "buildings_asset", "boundary_asset"]
    missing = [k for k in required if not cfg.get(k)]

    if missing:
        fail(
            f"Missing required setting(s) in {config_path.name}: "
            f"{', '.join(missing)}"
        )

    if cfg["project"] == "REPLACE_WITH_YOUR_GCP_PROJECT_ID":
        fail(
            f"Set 'project' in {config_path} to your Google Cloud "
            f"project ID before running this script."
        )

    return cfg


def init_earth_engine(cfg):

    try:
        import ee
    except ImportError:
        fail(
            "The 'earthengine-api' package is not installed.\n"
            "Install it with: pip install earthengine-api"
        )

    service_account = cfg.get("service_account") or ""
    key_file = cfg.get("key_file") or ""

    try:

        if service_account and key_file:

            credentials = ee.ServiceAccountCredentials(
                service_account, key_file
            )

            ee.Initialize(
                credentials,
                project=cfg["project"],
            )

        else:

            ee.Initialize(project=cfg["project"])

    except Exception as exc:

        fail(
            "Could not initialize Earth Engine.\n"
            f"{exc}\n\n"
            "If this is your first time running this script, "
            "authenticate first:\n"
            "  earthengine authenticate\n"
            "and make sure 'project' in "
            f"{DEFAULT_CONFIG.name} is a Cloud project with the "
            "Earth Engine API enabled and accessible to your account."
        )

    return ee


def find_country(ee, cfg, country_name):
    """
    Filter the boundary collection to the requested country. If no exact
    (case-insensitive) match is found, suggest close matches instead of
    failing silently with an empty result.
    """

    boundaries = ee.FeatureCollection(cfg["boundary_asset"])
    country_prop = cfg["boundary_country_property"]

    exact = boundaries.filter(
        ee.Filter.eq(country_prop, country_name)
    )

    if exact.size().getInfo() > 0:
        return exact

    # Case-insensitive retry
    all_names = boundaries.aggregate_array(country_prop).distinct()
    all_names = all_names.getInfo()

    lowered = {n.lower(): n for n in all_names if n}
    if country_name.lower() in lowered:
        matched_name = lowered[country_name.lower()]
        return boundaries.filter(
            ee.Filter.eq(country_prop, matched_name)
        )

    suggestions = sorted(
        n for n in all_names
        if n and country_name.lower() in n.lower()
    )

    if suggestions:
        fail(
            f"Country '{country_name}' not found in "
            f"{cfg['boundary_asset']}.\n"
            f"Did you mean: {', '.join(suggestions[:10])}?"
        )
    else:
        fail(
            f"Country '{country_name}' not found in "
            f"{cfg['boundary_asset']}.\n"
            "Check the spelling matches the UN country name used by "
            "FAO GAUL (e.g. 'Bangladesh', 'Philippines', "
            "'United Republic of Tanzania')."
        )


def build_output_table(ee, cfg, districts):

    buildings = ee.FeatureCollection(cfg["buildings_asset"])

    admin0 = cfg["boundary_country_property"]
    admin1 = cfg["boundary_admin1_property"]
    admin2 = cfg["boundary_admin2_property"]

    def count_buildings(district):

        count = (
            buildings
            .filterBounds(district.geometry())
            .size()
        )

        return district.set("building_count", count)

    counted = districts.map(count_buildings)

    def clean(f):

        return ee.Feature(None, {
            "country": f.get(admin0),
            "division_or_state": f.get(admin1),
            "district": f.get(admin2),
            "admin1_code": f.get("ADM1_CODE"),
            "admin2_code": f.get("ADM2_CODE"),
            "building_count": f.get("building_count"),
        })

    return counted.map(clean)


def export_to_drive(ee, output_clean, country_name):

    description = (
        f"{country_name.replace(' ', '_')}_District_Building_Count"
    )

    task = ee.batch.Export.table.toDrive(
        collection=output_clean,
        description=description,
        fileNamePrefix=description,
        fileFormat="CSV",
    )

    task.start()

    print(
        f"Export task started: '{description}'\n"
        f"Task ID: {task.id}\n"
        "Check progress at https://code.earthengine.google.com/tasks "
        "or with `earthengine task info <task id>`.\n"
        "The CSV will appear in your Google Drive once the task "
        "completes."
    )


def save_locally(ee, output_clean, country_name, cfg):

    header("PULLING RESULTS")

    features = output_clean.getInfo()["features"]

    if not features:
        fail(
            f"No districts returned for '{country_name}'. "
            "The boundary query matched the country but returned no "
            "district-level features - check boundary_asset in "
            "configs/earth_engine.yaml."
        )

    rows = [f["properties"] for f in features]
    df = pd.DataFrame(rows)

    df = df.sort_values(
        "building_count", ascending=False
    ).reset_index(drop=True)

    country_slug = country_name.strip().lower().replace(" ", "_")

    output_dir = (
        PROJECT_ROOT
        / cfg.get("output_root", "outputs")
        / country_slug
        / "BuildingCounts"
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / "building_counts_by_district.csv"
    output_excel = output_dir / "building_counts_by_district.xlsx"

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Building_Counts")
        ws = writer.sheets["Building_Counts"]
        for col in ws.columns:
            max_len = max(
                len(str(cell.value if cell.value is not None else ""))
                for cell in col
            )
            ws.column_dimensions[col[0].column_letter].width = max_len + 3

    print(f"Districts             : {len(df)}")
    print(f"Saved CSV              : {output_csv}")
    print(f"Saved Excel            : {output_excel}")

    print("\nTop 10 districts by building count:")
    cols = [c for c in ["district", "division_or_state", "building_count"] if c in df.columns]
    print(df[cols].head(10).to_string(index=False))


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download district-level building counts from Google Earth "
            "Engine for a country."
        )
    )

    parser.add_argument(
        "country",
        help='Country name, e.g. "Bangladesh" (matched against FAO GAUL '
             "country names).",
    )

    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to the Earth Engine config YAML "
             "(default: configs/earth_engine.yaml).",
    )

    parser.add_argument(
        "--export-drive",
        action="store_true",
        help="Export to Google Drive as an async batch task instead of "
             "downloading directly (use this for very large countries "
             "where a direct pull may be slow or time out).",
    )

    args = parser.parse_args()

    header(f"BUILDING COUNT DOWNLOAD — {args.country.upper()}")

    config_path = Path(args.config)
    cfg = load_config(config_path)

    print(f"Repository root   : {PROJECT_ROOT}")
    print(f"Config file       : {config_path}")
    print(f"GCP project       : {cfg['project']}")
    print(f"Buildings asset   : {cfg['buildings_asset']}")
    print(f"Boundary asset    : {cfg['boundary_asset']}")

    ee = init_earth_engine(cfg)

    header("LOCATING COUNTRY")

    districts = find_country(ee, cfg, args.country)

    n_districts = districts.size().getInfo()
    print(f"Districts found   : {n_districts}")

    header("COUNTING BUILDINGS PER DISTRICT")

    print(
        "Running server-side filterBounds + size() per district "
        "(this can take a while for large countries)..."
    )

    output_clean = build_output_table(ee, cfg, districts)

    if args.export_drive:
        export_to_drive(ee, output_clean, args.country)
    else:
        save_locally(ee, output_clean, args.country, cfg)

    print("\nDone.")


if __name__ == "__main__":
    main()

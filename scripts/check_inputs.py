from pathlib import Path
import argparse
import sys

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def header(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def fail(message):
    print(f"\nERROR: {message}")
    sys.exit(1)


def require_file(path, label):
    print(f"{label:<22}: {path}")

    if not path.is_file():
        fail(f"{label} not found:\n{path}")

    print(f"{'':<22}  [OK]")


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cyclone",
        default="remal",
        choices=["remal", "sitrang", "midhili"],
    )

    parser.add_argument(
        "--lead",
        default="1dlt",
        choices=["1dlt", "2dlt", "3dlt"],
    )

    args = parser.parse_args()

    cyclone_key = args.cyclone.lower()
    lead_time = args.lead.lower()

    config_file = (
        PROJECT_ROOT
        / "configs"
        / f"{cyclone_key}.yaml"
    )

    header("IBF REPOSITORY PRE-RUN CHECK")

    print(f"Repository root      : {PROJECT_ROOT}")
    print(f"Cyclone key          : {cyclone_key}")
    print(f"Lead time            : {lead_time}")

    # ========================================================
    # CONFIGURATION
    # ========================================================

    header("1. CONFIGURATION")

    require_file(
        config_file,
        "Configuration file",
    )

    with config_file.open(
        "r",
        encoding="utf-8",
    ) as f:

        cfg = yaml.safe_load(f)

    try:

        cyclone = cfg["cyclone"]["name"]

        forecast_relative = (
            cfg["data"]["forecasts"][lead_time]
        )

        observed_relative = (
            cfg["data"]["observed"]
        )

        boundary_relative = (
            cfg["data"]["adm3_boundary"]
        )

        output_relative = (
            cfg["output"]["directory"]
        )

        forecast_sheet = (
            cfg["sheets"]["forecast"]
        )

        house_sheet = (
            cfg["sheets"]["house"]
        )

        agri_sheet = (
            cfg["sheets"]["agriculture"]
        )

    except KeyError as exc:

        fail(
            f"Missing required key in "
            f"{config_file.name}: {exc}"
        )

    forecast_file = (
        PROJECT_ROOT
        / forecast_relative
    )

    ddm_file = (
        PROJECT_ROOT
        / observed_relative
    )

    adm3_file = (
        PROJECT_ROOT
        / boundary_relative
    )

    output_dir = (
        PROJECT_ROOT
        / output_relative
        / lead_time
    )

    print(f"Cyclone               : {cyclone}")
    print(f"Lead time             : {lead_time}")
    print(f"Forecast              : {forecast_file}")
    print(f"Observed DDM          : {ddm_file}")
    print(f"Output                : {output_dir}")

    # ========================================================
    # FORECAST
    # ========================================================

    header("2. FORECAST WORKBOOK")

    require_file(
        forecast_file,
        "Forecast workbook",
    )

    xls = pd.ExcelFile(
        forecast_file
    )

    print(
        f"Sheet names           : "
        f"{xls.sheet_names}"
    )

    if forecast_sheet not in xls.sheet_names:

        fail(
            f"Forecast sheet "
            f"'{forecast_sheet}' not found."
        )

    df = pd.read_excel(
        forecast_file,
        sheet_name=forecast_sheet,
    )

    df.columns = [
        str(c).strip()
        for c in df.columns
    ]

    required_columns = [
        "ADM3_PCODE",
        "District",
        "Upazila",
        "Norm_Impact_House",
        "Norm_Impact_fAPAR",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    print(
        f"Shape                 : "
        f"{df.shape}"
    )

    if missing:

        fail(
            "Missing forecast columns:\n  - "
            + "\n  - ".join(missing)
        )

    print(
        "Required columns      : [OK]"
    )

    # ========================================================
    # DDM
    # ========================================================

    header("3. DDM WORKBOOK")

    require_file(
        ddm_file,
        "DDM workbook",
    )

    ddm_xls = pd.ExcelFile(
        ddm_file
    )

    print(
        f"Sheet names           : "
        f"{ddm_xls.sheet_names}"
    )

    for sheet in [
        house_sheet,
        agri_sheet,
    ]:

        if sheet not in ddm_xls.sheet_names:

            fail(
                f"Required DDM sheet "
                f"'{sheet}' not found."
            )

    house_raw = pd.read_excel(
        ddm_file,
        sheet_name=house_sheet,
        header=None,
    )

    agri_raw = pd.read_excel(
        ddm_file,
        sheet_name=agri_sheet,
        header=None,
    )

    print(
        f"House raw shape       : "
        f"{house_raw.shape}"
    )

    print(
        f"Agriculture raw shape : "
        f"{agri_raw.shape}"
    )

    if (
        house_raw.shape[0] < 3
        or house_raw.shape[1] < 10
    ):

        fail(
            "House sheet requires at least "
            "3 rows and 10 columns."
        )

    if (
        agri_raw.shape[0] < 3
        or agri_raw.shape[1] < 8
    ):

        fail(
            "Agriculture sheet requires at "
            "least 3 rows and 8 columns."
        )

    print(
        "DDM workbook structure: [OK]"
    )

    # ========================================================
    # SHAPEFILE
    # ========================================================

    header("4. ADM3 BOUNDARY")

    require_file(
        adm3_file,
        "ADM3 shapefile",
    )

    for ext in [
        ".dbf",
        ".shx",
        ".prj",
    ]:

        sidecar = (
            adm3_file.with_suffix(ext)
        )

        if not sidecar.is_file():

            fail(
                f"Missing shapefile component:\n"
                f"{sidecar}"
            )

    print(
        "Shapefile components  : [OK]"
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    header("5. OUTPUT DIRECTORY")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"Output directory      : "
        f"{output_dir}"
    )

    print(
        "Output directory      : [OK]"
    )

    # ========================================================

    header("PRE-RUN CHECK PASSED")

    print(
        f"{cyclone} {lead_time} "
        f"is ready for analysis."
    )


if __name__ == "__main__":
    main()
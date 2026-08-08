import os
import glob
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# 1. REPOSITORY PATHS
# ─────────────────────────────────────────────

CURRENT_DIR = Path.cwd().resolve()

PROJECT_ROOT = None

for folder in [CURRENT_DIR, *CURRENT_DIR.parents]:
    if (folder / "data").is_dir():
        PROJECT_ROOT = folder
        break

if PROJECT_ROOT is None:
    raise RuntimeError(
        "Could not locate IBF-Analysis repository root."
    )


# Parent folder containing cyclone/event folders
PARENT_DIR = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "faapar"
)


# Bangladesh ADM3 shapefile
SHAPEFILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "bangladesh_adm3"
    / "bgd_admbnda_adm3_bbs_20201113.shp"
)


# Folder names inside each cyclone/event folder
BEFORE_SUBDIR = "before"
AFTER_SUBDIR = "after"


# ─────────────────────────────────────────────
# 2. FIXED PRODUCT SETTINGS
# ─────────────────────────────────────────────

# TIFF source:
# valid raw values = 0–200
# scale factor     = 0.005
# nodata           = 255

RAW_VALID_MIN = 0
RAW_VALID_MAX = 200
RAW_NODATA = 255

SCALE_FACTOR = 0.005
OUT_NODATA = -9999.0


# ─────────────────────────────────────────────
# 3. SHAPEFILE ATTRIBUTE COLUMNS
# ─────────────────────────────────────────────

UPAZILA_NAME_COL = "ADM3_EN"
DISTRICT_NAME_COL = "ADM2_EN"
DIVISION_NAME_COL = "ADM1_EN"


# ─────────────────────────────────────────────
# 4. HELPERS
# ─────────────────────────────────────────────

def check_file(path, label):

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"{label} not found:\n{path}"
        )


def get_single_tif(folder):

    tif_files = sorted(
        glob.glob(
            os.path.join(
                str(folder),
                "*.tif"
            )
        )
    )

    if len(tif_files) == 0:

        raise FileNotFoundError(
            f"No .tif file found in:\n{folder}"
        )

    if len(tif_files) > 1:

        raise ValueError(
            f"More than one .tif file found in:\n"
            f"{folder}\n"
            f"Found: {len(tif_files)}"
        )

    return tif_files[0]


# ─────────────────────────────────────────────
# 5. PREPROCESS FAPAR RASTER
# ─────────────────────────────────────────────

def preprocess_fapar_raster(
    input_tif,
    output_tif,
    valid_min=0,
    valid_max=200,
    raw_nodata=255,
    scale_factor=0.005,
    out_nodata=-9999.0
):

    """
    Create cleaned float32 FAPAR raster.

    - keep raw values between valid_min and valid_max
    - exclude raw nodata
    - apply scale factor
    - write invalid pixels as output nodata
    """

    with rasterio.open(input_tif) as src:

        profile = src.profile.copy()

        profile.update(
            dtype="float32",
            count=1,
            nodata=out_nodata,
            compress="lzw"
        )

        with rasterio.open(
            output_tif,
            "w",
            **profile
        ) as dst:

            for _, window in src.block_windows(1):

                arr = src.read(
                    1,
                    window=window
                )

                valid = (
                    np.isfinite(arr)
                    &
                    (arr != raw_nodata)
                    &
                    (arr >= valid_min)
                    &
                    (arr <= valid_max)
                )

                out = np.full(
                    arr.shape,
                    out_nodata,
                    dtype=np.float32
                )

                out[valid] = (
                    arr[valid].astype(np.float32)
                    * scale_factor
                )

                dst.write(
                    out,
                    1,
                    window=window
                )


# ─────────────────────────────────────────────
# 6. ZONAL STATISTICS
# ─────────────────────────────────────────────

def compute_zonal_mean(
    clean_tif,
    gdf,
    nodata=-9999.0
):

    stats = zonal_stats(
        vectors=gdf,
        raster=clean_tif,
        stats=[
            "mean",
            "count"
        ],
        nodata=nodata,
        all_touched=False,
        geojson_out=False
    )

    means = []
    counts = []

    for s in stats:

        means.append(
            np.nan
            if s["mean"] is None
            else float(s["mean"])
        )

        counts.append(
            int(s["count"])
            if s["count"] is not None
            else 0
        )

    return means, counts


# ─────────────────────────────────────────────
# 7. LOAD ADM3 SHAPEFILE
# ─────────────────────────────────────────────

def load_and_prepare_gdf(
    shapefile,
    sample_raster
):

    gdf = gpd.read_file(
        shapefile
    )

    with rasterio.open(
        sample_raster
    ) as src:

        raster_crs = src.crs

    if raster_crs is None:

        raise ValueError(
            f"Raster CRS is missing:\n{sample_raster}"
        )

    if gdf.crs is None:

        raise ValueError(
            f"Shapefile CRS is missing:\n{shapefile}"
        )

    if gdf.crs != raster_crs:

        gdf = gdf.to_crs(
            raster_crs
        )

    return gdf


# ─────────────────────────────────────────────
# 8. STATUS CLASSIFICATION
# ─────────────────────────────────────────────

def classify_status(x):

    if pd.isna(x):
        return "No Data"

    elif x > 0:
        return "Loss"

    elif x < 0:
        return "Gain"

    else:
        return "No Change"


# ─────────────────────────────────────────────
# 9. PROCESS ONE CYCLONE / EVENT
# ─────────────────────────────────────────────

def process_event_folder(
    event_folder
):

    event_folder = Path(
        event_folder
    )

    event_name = (
        event_folder.name
    )

    before_dir = (
        event_folder
        / BEFORE_SUBDIR
    )

    after_dir = (
        event_folder
        / AFTER_SUBDIR
    )


    print()
    print("=" * 70)
    print(
        f"Processing: {event_name}"
    )
    print("=" * 70)


    if not before_dir.is_dir():

        print(
            f"Skipped: before folder not found -> "
            f"{before_dir}"
        )

        return


    if not after_dir.is_dir():

        print(
            f"Skipped: after folder not found -> "
            f"{after_dir}"
        )

        return


    before_tif = get_single_tif(
        before_dir
    )

    after_tif = get_single_tif(
        after_dir
    )


    print(
        f"Before TIFF : {before_tif}"
    )

    print(
        f"After TIFF  : {after_tif}"
    )


    # Load ADM3 boundary and match raster CRS
    gdf = load_and_prepare_gdf(
        SHAPEFILE,
        before_tif
    )


    # ─────────────────────────────────────────
    # TEMPORARY CLEANED RASTERS
    # ─────────────────────────────────────────

    with tempfile.TemporaryDirectory() as tmpdir:

        before_clean = os.path.join(
            tmpdir,
            "before_clean.tif"
        )

        after_clean = os.path.join(
            tmpdir,
            "after_clean.tif"
        )


        print(
            "Preprocessing before raster ..."
        )

        preprocess_fapar_raster(
            before_tif,
            before_clean,
            valid_min=RAW_VALID_MIN,
            valid_max=RAW_VALID_MAX,
            raw_nodata=RAW_NODATA,
            scale_factor=SCALE_FACTOR,
            out_nodata=OUT_NODATA
        )


        print(
            "Preprocessing after raster ..."
        )

        preprocess_fapar_raster(
            after_tif,
            after_clean,
            valid_min=RAW_VALID_MIN,
            valid_max=RAW_VALID_MAX,
            raw_nodata=RAW_NODATA,
            scale_factor=SCALE_FACTOR,
            out_nodata=OUT_NODATA
        )


        print(
            "Computing zonal statistics ..."
        )


        before_mean, before_count = (
            compute_zonal_mean(
                before_clean,
                gdf,
                nodata=OUT_NODATA
            )
        )


        after_mean, after_count = (
            compute_zonal_mean(
                after_clean,
                gdf,
                nodata=OUT_NODATA
            )
        )


    # ─────────────────────────────────────────
    # BUILD RESULT TABLE
    # ─────────────────────────────────────────

    result = pd.DataFrame()


    for col in [
        DIVISION_NAME_COL,
        DISTRICT_NAME_COL,
        UPAZILA_NAME_COL
    ]:

        if col in gdf.columns:

            result[col] = (
                gdf[col].values
            )


    # Include ADM3 P-Code if available
    if "ADM3_PCODE" in gdf.columns:

        result["ADM3_PCODE"] = (
            gdf["ADM3_PCODE"].values
        )


    result[
        "ValidPix_Before"
    ] = before_count


    result[
        "ValidPix_After"
    ] = after_count


    result[
        "FAPAR_Before"
    ] = np.round(
        before_mean,
        4
    )


    result[
        "FAPAR_After"
    ] = np.round(
        after_mean,
        4
    )


    # Positive value = FAPAR loss
    result[
        "FAPAR_Loss"
    ] = np.round(

        result[
            "FAPAR_Before"
        ]
        -
        result[
            "FAPAR_After"
        ],

        4
    )


    result[
        "FAPAR_Loss_Pct"
    ] = np.where(

        result[
            "FAPAR_Before"
        ] > 0,

        np.round(
            (
                result[
                    "FAPAR_Loss"
                ]
                /
                result[
                    "FAPAR_Before"
                ]
            )
            * 100,
            2
        ),

        np.nan
    )


    result[
        "Status"
    ] = (
        result[
            "FAPAR_Loss"
        ]
        .apply(
            classify_status
        )
    )


    result[
        "QA_Flag"
    ] = np.where(

        (
            result[
                "ValidPix_Before"
            ] == 0
        )
        |
        (
            result[
                "ValidPix_After"
            ] == 0
        ),

        "Check",

        "OK"
    )


    result = (
        result
        .sort_values(
            by="FAPAR_Loss",
            ascending=False,
            na_position="last"
        )
        .reset_index(
            drop=True
        )
    )


    # ─────────────────────────────────────────
    # SAVE OUTPUT
    # ─────────────────────────────────────────

    output_csv = (
        event_folder
        / "fapar_loss_by_upazila.csv"
    )

    output_excel = (
        event_folder
        / "fapar_loss_by_upazila.xlsx"
    )


    result.to_csv(
        output_csv,
        index=False,
        encoding="utf-8-sig"
    )


    with pd.ExcelWriter(
        output_excel,
        engine="openpyxl"
    ) as writer:

        result.to_excel(
            writer,
            index=False,
            sheet_name="FAPAR_Loss"
        )

        ws = writer.sheets[
            "FAPAR_Loss"
        ]

        for col in ws.columns:

            max_len = max(
                len(
                    str(
                        cell.value
                        if cell.value is not None
                        else ""
                    )
                )
                for cell in col
            )

            ws.column_dimensions[
                col[0].column_letter
            ].width = max_len + 3


    print(
        f"Saved CSV   : {output_csv}"
    )

    print(
        f"Saved Excel : {output_excel}"
    )


    # ─────────────────────────────────────────
    # TOP 10
    # ─────────────────────────────────────────

    print()
    print(
        "Top 10 affected upazilas:"
    )


    cols_to_show = [

        c

        for c in [

            UPAZILA_NAME_COL,

            DISTRICT_NAME_COL,

            "FAPAR_Before",

            "FAPAR_After",

            "FAPAR_Loss",

            "FAPAR_Loss_Pct",

            "Status"

        ]

        if c in result.columns
    ]


    print(
        result[
            cols_to_show
        ]
        .head(10)
        .to_string(
            index=False
        )
    )


# ─────────────────────────────────────────────
# 10. MAIN
# ─────────────────────────────────────────────

def main():

    print("=" * 70)
    print("Batch FAPAR Loss Analysis")
    print("=" * 70)

    print(
        f"Repository root : {PROJECT_ROOT}"
    )

    print(
        f"FAPAR data root : {PARENT_DIR}"
    )

    print(
        f"ADM3 boundary   : {SHAPEFILE}"
    )


    check_file(
        SHAPEFILE,
        "SHAPEFILE"
    )


    if not PARENT_DIR.is_dir():

        raise NotADirectoryError(
            f"FAPAR parent folder not found:\n"
            f"{PARENT_DIR}"
        )


    event_folders = sorted([

        folder

        for folder
        in PARENT_DIR.iterdir()

        if folder.is_dir()
    ])


    if len(event_folders) == 0:

        print(
            "No cyclone/event folders found."
        )

        return


    print(
        f"Total event folders found: "
        f"{len(event_folders)}"
    )


    for event_folder in event_folders:

        try:

            process_event_folder(
                event_folder
            )

        except Exception as e:

            print()
            print(
                f"Error in folder: "
                f"{event_folder.name}"
            )

            print(
                str(e)
            )


    print()
    print("=" * 70)
    print("All folders processed.")
    print("=" * 70)


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    main()
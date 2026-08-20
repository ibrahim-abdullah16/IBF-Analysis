# IBF-Analysis Data Dictionary

This document describes the input data required to reproduce the Impact-Based
Forecasting (IBF) validation analysis.

## 1. Forecast Impact Data

Files (one per lead time, per cyclone):

```text
data/sample/<cyclone>/Forecasted_Impact_1dlt.xlsx
data/sample/<cyclone>/Forecasted_Impact_2dlt.xlsx
data/sample/<cyclone>/Forecasted_Impact_3dlt.xlsx
```

Sheet: the cyclone name (e.g. `Remal`, `Sitrang`, `Midhili`), set per-cyclone
in `configs/<cyclone>.yaml` under `sheets.forecast`.

### Required administrative columns

| Column | Description |
|---|---|
| ADM3_PCODE | Administrative Level 3 / Sub-National P-Code |
| District | District name |
| Upazila | Sub-National unit name |

### Main forecast impact variables

| Column | Description |
|---|---|
| Norm_Impact_House | Normalized forecast impact score for housing |
| Norm_Impact_fAPAR | Normalized forecast impact score for agriculture/fAPAR |

Both impact variables are expected to be numeric and normally bounded between
0 and 1.

Additional hazard, vulnerability, exposure, and impact-class columns may also
be present in this workbook.

## 2. Observed Impact Data

Files:

```text
data/sample/remal/Cyclone_Remal_Observed_Damage_Data.xlsx
data/sample/sitrang/Cyclone_Sitrang_Observed_Damage_Data.xlsx
data/sample/midhili/Cyclone_Midhili_Observed_Damage_Data.xlsx
```

Observed post-cyclone impact data were obtained from the Department of
Disaster Management (DDM). The workbook contains separate sheets for housing
and agricultural impacts.

### 2.1 House Sheet

Sheet: `House`

Expected structure:

| Excel Column | Variable | Description |
|---|---|---|
| A | District | District name |
| B | Upazila | Sub-National unit name |
| C | No_Brick | Number of affected brick houses |
| D | No_HalfBrick | Number of affected semi-pucca/half-brick houses |
| E | No_Raw | Number of affected raw/kutcha houses |
| F | No_Total | Total number of affected houses |
| G | Amt_Brick | Estimated monetary loss for brick houses |
| H | Amt_HalfBrick | Estimated monetary loss for half-brick houses |
| I | Amt_Raw | Estimated monetary loss for raw houses |
| J | Amt_Total | Total estimated housing loss |

The first two rows of the sheet contain metadata/header information and are
skipped during processing.

### 2.2 Agriculture Sheet

Sheet: `Agriculture`

Expected structure:

| Excel Column | Variable | Description |
|---|---|---|
| A | District | District name |
| B | Upazila | Sub-National unit name |
| C | Fully_Land | Fully damaged agricultural land |
| D | Fully_Amt | Estimated loss from fully damaged crops |
| E | Partial_Land | Partially damaged agricultural land |
| F | Partial_Amt | Estimated loss from partially damaged crops |
| G | Total_Loss_Land | Total affected agricultural land |
| H | Total_Loss_Amt | Total estimated agricultural loss |

The first two rows of the sheet contain metadata/header information and are
skipped during processing.

## 3. Administrative Matching

Forecast and observed datasets are matched at Sub-National level.

Preferred identifier: `ADM3_PCODE`

Where P-Code is unavailable in the observed dataset, matching is performed
using `District + Upazila`. District and Sub-National unit names are cleaned
before matching by removing leading and trailing whitespace.

## 4. Missing Data

Missing DDM observations are not interpreted automatically as zero damage.
Records without valid paired forecast and observed values are excluded from
statistical analyses requiring complete pairs. Observed zero values represent
reported no-impact cases where appropriate.

## 5. Expected Value Types

| Variable type | Expected format |
|---|---|
| ADM3_PCODE | Text/string |
| District | Text/string |
| Upazila | Text/string |
| Forecast impact scores | Numeric |
| House damage counts | Numeric |
| Monetary losses | Numeric |
| Agricultural losses | Numeric |

## 6. Spatial Boundary Data

Administrative Level 3 boundary data are required for mapping.

Expected location: `data/reference/bangladesh_adm3/`

The boundary dataset must contain `ADM3_PCODE`, which is used to join
forecast impact information with Sub-National unit polygons.

## 7. fAPAR Before/After Rasters (optional preprocessing input)

Files:

```text
data/sample/faapar/<cyclone>/before/*.tif   # one .tif, pre-landfall
data/sample/faapar/<cyclone>/after/*.tif    # one .tif, post-landfall
```

Raw single-band GeoTIFFs, valid range 0-200, nodata 255, scale factor 0.005
(applied on read). Processed by `scripts/fapar_zonal_stats.py <cyclone>` into
per-Sub-National-unit fAPAR loss, written to `outputs/<cyclone>/FAPAR/`. This is a
preprocessing input, not required to run the validation workflow itself if
`Norm_Impact_fAPAR` is already populated in the forecast workbook.

## 8. Building Counts (optional preprocessing input)

Not stored under `data/` - downloaded on demand from Google Earth Engine by
`scripts/download_building_counts.py <country>` and written to
`outputs/<country>/BuildingCounts/`. See `configs/earth_engine.yaml` for the
boundary/building-dataset sources and one-time authentication setup. Produces
district-level (not Sub-National-level) counts; joining into the Sub-National-level
workflow used here would require an additional spatial join, not performed
by this script.

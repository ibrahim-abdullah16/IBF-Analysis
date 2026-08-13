# IBF-Analysis

A reproducible Python workflow for evaluating cyclone **Impact-Based Forecasting (IBF)** products against observed post-event impacts at the Upazila level in Bangladesh.

The repository supports three cyclone case studies—**Remal, Sitrang, and Midhili**—at **1-day, 2-day, and 3-day lead times**. A parameterized validation notebook is used across cyclone–lead combinations through YAML configuration files.

## Supported cases

| Cyclone | 1-day lead | 2-day lead | 3-day lead |
|---|---:|---:|---:|
| Remal | ✓ | ✓ | ✓ |
| Sitrang | ✓ | ✓ | ✓ |
| Midhili | ✓ | ✓ | ✓ |

Lead-time identifiers used in the repository:

- `1dlt` — 1-day lead time
- `2dlt` — 2-day lead time
- `3dlt` — 3-day lead time

## Analysis components

The current workflow includes:

- ROC curve and Area Under the Curve (AUC)
- Ordinary Least Squares (OLS) regression
- Pearson correlation and R²
- Spearman rank correlation
- Kendall rank correlation
- one-sided Mann–Whitney U test
- Hit / Miss / False Alarm / Correct Negative verification
- Probability of Detection (POD)
- False Alarm Ratio (FAR)
- Critical Success Index (CSI)
- Frequency Bias
- Accuracy
- No-Impact threshold optimization
- class-based damage diagnostics
- cyclone-specific DDM severity categorization
- Quadratic-Weighted Cohen's Kappa
- Exact / Adjacent / Off-category agreement
- Upazila-level spatial verification using ADM3 P-Codes

RMSE and NSE are not reported in the current workflow.

## Repository structure

```text
IBF-Analysis/
│
├── configs/
│   ├── remal.yaml
│   ├── sitrang.yaml
│   └── midhili.yaml
│
├── data/
│   ├── reference/
│   │   └── bangladesh_adm3/
│   │       └── bgd_admbnda_adm3_bbs_20201113.*
│   │
│   └── sample/
│       ├── remal/
│       │   ├── Forecasted_Impact_1dlt.xlsx
│       │   ├── Forecasted_Impact_2dlt.xlsx
│       │   ├── Forecasted_Impact_3dlt.xlsx
│       │   └── Remal_ddm.xlsx
│       │
│       ├── sitrang/
│       │   ├── Forecasted_Impact_1dlt.xlsx
│       │   ├── Forecasted_Impact_2dlt.xlsx
│       │   ├── Forecasted_Impact_3dlt.xlsx
│       │   └── Sitrang_ddm.xlsx
│       │
│       ├── midhili/
│       │   ├── Forecasted_Impact_1dlt.xlsx
│       │   ├── Forecasted_Impact_2dlt.xlsx
│       │   ├── Forecasted_Impact_3dlt.xlsx
│       │   └── Midhili_ddm.xlsx
│       │
│       └── faapar/
│           ├── remal/
│           ├── sitrang/
│           └── midhili/
│
├── docs/
│   └── data_dictionary.md
│
├── notebooks/
│   └── 01_remal_validation.ipynb
│
├── scripts/
│   ├── check_inputs.py
│   ├── run_analysis.py
│   └── fapar_processing.py
│
├── outputs/
│   ├── remal/
│   ├── sitrang/
│   └── midhili/
│
├── .gitignore
├── requirements.txt
└── README.md
```

The notebook name is retained for compatibility, but the workflow is parameterized for all supported cyclone and lead-time combinations.

## Input data

### Forecast impact workbooks

Each cyclone uses three forecast workbooks:

```text
Forecasted_Impact_1dlt.xlsx
Forecasted_Impact_2dlt.xlsx
Forecasted_Impact_3dlt.xlsx
```

The workflow uses the administrative and impact fields required by the validation notebook, including:

```text
ADM3_PCODE
District
Upazila
Norm_Impact_House
Norm_Impact_fAPAR
```

The current workbook structure also uses:

| Excel column | Variable |
|---|---|
| W | `Norm_Impact_fAPAR` |
| X | Agriculture/fAPAR forecast severity class |
| AF | `Norm_Impact_House` |
| AG | Household forecast severity class |

### Observed DDM data

Each cyclone uses one Department of Disaster Management (DDM) workbook:

```text
Remal_ddm.xlsx
Sitrang_ddm.xlsx
Midhili_ddm.xlsx
```

Expected sheets:

```text
House
Agriculture
```

The same DDM workbook is used for all three lead times of a cyclone.

### Administrative boundary

Spatial validation uses the Bangladesh ADM3 boundary shapefile:

```text
data/reference/bangladesh_adm3/bgd_admbnda_adm3_bbs_20201113.shp
```

Forecast and DDM records are matched using administrative names, while spatial outputs use normalized `ADM3_PCODE` for the ADM3 join.

## Configuration

Each cyclone has a YAML configuration file under `configs/`.

Example:

```yaml
cyclone:
  name: Remal

data:
  forecasts:
    1dlt: data/sample/remal/Forecasted_Impact_1dlt.xlsx
    2dlt: data/sample/remal/Forecasted_Impact_2dlt.xlsx
    3dlt: data/sample/remal/Forecasted_Impact_3dlt.xlsx

  observed: data/sample/remal/Remal_ddm.xlsx
  adm3_boundary: data/reference/bangladesh_adm3/bgd_admbnda_adm3_bbs_20201113.shp

sheets:
  forecast: Remal
  house: House
  agriculture: Agriculture

output:
  directory: outputs/remal
```

Paths are resolved relative to the repository root, allowing the workflow to run without machine-specific absolute paths.

## Methodology

### Continuous association

Continuous forecast impact scores are compared with positive observed DDM damage values.

The notebook reports:

- OLS slope and intercept
- Pearson correlation coefficient and p-value
- R²
- Spearman rank correlation and p-value
- Kendall rank correlation and p-value
- observed-data skewness

Analyses are produced for both raw observed damage and `log1p`-transformed observed damage.

### Binary verification

Observed impact is defined as:

```text
Impact     : DDM value > 0
No Impact  : DDM value = 0
```

Binary forecast performance is summarized using:

```text
Hit
Miss
False Alarm
Correct Negative
POD
FAR
CSI
Bias
Accuracy
```

A separate class-based diagnostic also compares forecast impact classes with observed damage occurrence.

### No-Impact threshold optimization

The validation workflow evaluates normalized forecast thresholds and calculates:

```text
Decision Score = CSI - FAR - |Bias - 1|
```

The main threshold search evaluates values from `0.00` to `1.00` at `0.01` intervals and identifies a balanced candidate using Bias and FAR constraints.

A separate percentile-based diagnostic evaluates empirical forecast-score percentiles from `P5` to `P50` for household and agriculture/fAPAR impact scores.

These procedures are calibration diagnostics rather than independent out-of-sample validation.

### ROC / AUC

ROC curves evaluate how well continuous forecast impact scores discriminate between damaged and undamaged Upazilas.

AUC is calculated for:

- household impact vs number of damaged households
- household impact vs household repair amount
- agriculture/fAPAR impact vs damaged agricultural area
- agriculture/fAPAR impact vs agricultural monetary loss

The ROC/AUC calculation is implemented directly with NumPy.

### Mann–Whitney U test

A one-sided Mann–Whitney U test compares forecast impact scores between damaged and non-damaged Upazilas.

The alternative hypothesis is that forecast impact scores are higher in locations where observed DDM damage occurred.

### Cyclone-specific DDM severity categorization

DDM records contain continuous damage values and do not provide predefined categorical severity levels.

For categorical comparison, observed damage is converted to:

```text
No Impact
Low
Medium
High
```

using:

```text
DDM = 0          -> No Impact
0 < DDM <= C1    -> Low
C1 < DDM <= C2   -> Medium
DDM > C2         -> High
```

For each cyclone and damage variable, one pair of DDM cut-points is selected jointly from the `1dlt`, `2dlt`, and `3dlt` forecasts.

For each candidate pair:

1. DDM severity classes are generated.
2. Quadratic-Weighted Kappa is calculated separately for each lead time.
3. The three Kappa values are averaged.
4. The pair with the highest mean Kappa is selected.
5. The selected cut-points are held fixed across all three lead times of that cyclone.

The maximum observed positive DDM value is excluded as a candidate high cut so that the High category remains populated.

The output workbook retains the leading candidate threshold combinations for sensitivity assessment.

The resulting DDM classes are interpreted as **event-relative observed severity categories**, not universal operational damage thresholds across different cyclone events.

### Categorical severity agreement

Forecast classes:

```text
No Impact
Low
Moderate
High
```

are compared with observed DDM classes:

```text
No Impact
Low
Medium
High
```

Agreement is summarized as:

- **Exact** — forecast and observed severity are the same
- **Adjacent** — one-category difference
- **Off** — two- or three-category difference

Quadratic-Weighted Cohen's Kappa is used as the ordinal agreement statistic.

### Spatial verification

Upazila-level spatial outputs are generated for four forecast–damage comparisons:

- household impact vs damaged-house count
- household impact vs repair amount
- agriculture/fAPAR impact vs damaged agricultural land
- agriculture/fAPAR impact vs agricultural monetary loss

Spatial outputs classify locations as:

```text
Hit
Miss
False Alarm
True Negative
```

The current spatial block uses:

```python
HOUSE_THRESHOLD = 0.0
AGRI_THRESHOLD = 0.0
```

and therefore represents impact occurrence using positive normalized forecast impact rather than the separately optimized No-Impact thresholds.

## Installation

Python 3.10 or newer is recommended.

Clone the repository:

```bash
git clone https://github.com/ibrahim-abdullah16/IBF-Analysis.git
cd IBF-Analysis
```

Create and activate a virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running the workflow

### Check inputs

```powershell
python scripts\check_inputs.py --cyclone remal --lead 1dlt
```

Examples:

```powershell
python scripts\check_inputs.py --cyclone sitrang --lead 2dlt
python scripts\check_inputs.py --cyclone midhili --lead 3dlt
```

### Run one cyclone and lead time

```powershell
python scripts\run_analysis.py remal 1dlt
```

Examples:

```powershell
python scripts\run_analysis.py sitrang 2dlt
python scripts\run_analysis.py midhili 3dlt
```

### Run all configured cases

```powershell
python scripts\run_analysis.py --all
```

### Run interactively

```powershell
python -m jupyter notebook notebooks\01_remal_validation.ipynb
```

## Outputs

Results are written to:

```text
outputs/<cyclone>/<lead>/
```

Typical output folders include:

```text
AUC/
Validation/
No_Impact_Threshold_Optimization/
DDM_Categorization/
Hit_Map/
```

Generated products include:

- ROC/AUC figures
- OLS and correlation diagnostics
- validation summary workbooks
- threshold-optimization figures
- DDM severity-classification workbooks
- categorical agreement heatmaps
- spatial Hit / Miss / False Alarm / True Negative outputs
- CSV summaries
- executed notebooks

## Optional fAPAR preprocessing

The repository includes:

```text
scripts/fapar_processing.py
```

for processing before/after fAPAR raster data and generating Upazila-level agricultural vegetation-loss summaries.

Prepared forecast workbooks can be used directly without rerunning the raster preprocessing step.

## Reproducibility

The workflow uses configuration-based paths and produces separate outputs for each cyclone and lead time. Generated analysis products are stored under `outputs/`, while source scripts, configuration files, notebooks, and input data remain separate.

Data-driven threshold and severity-calibration components are reported as calibration and categorical-concordance analyses rather than independent predictive validation.

## Data sources

The analysis uses cyclone impact forecasts, post-event DDM damage records, Bangladesh ADM3 administrative boundaries, and fAPAR-derived agricultural impact information.

Data remain subject to the terms and conditions of their respective source organizations.

## Citation

When using this repository for research or technical reporting, cite the repository version or Git commit used for the analysis.

## Status

This repository contains a research workflow for cyclone impact-based forecast validation in Bangladesh.

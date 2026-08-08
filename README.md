# IBF-Analysis

A reproducible Python workflow for validating **Impact-Based Forecasting (IBF)** products against observed post-disaster impact data.

The repository supports multiple tropical cyclones and multiple forecast lead times using one common validation workflow.

## Current analysis cases

| Cyclone | 1-day lead | 2-day lead | 3-day lead |
|---|---:|---:|---:|
| Remal | ✓ | ✓ | ✓ |
| Sitrang | ✓ | ✓ | ✓ |
| Midhili | ✓ | ✓ | ✓ |

Lead-time identifiers:

- `1dlt` — 1-day lead time
- `2dlt` — 2-day lead time
- `3dlt` — 3-day lead time

## Purpose

The workflow compares forecast impact indicators with observed post-cyclone DDM impact data and evaluates:

- continuous forecast–observation agreement
- binary impact/no-impact performance
- optimized no-impact thresholds
- ROC/AUC discrimination
- DDM severity calibration using quadratic-weighted Kappa
- exact, adjacent, and off-category severity agreement
- spatial patterns of hits, misses, false alarms, and correct negatives

The same scientific workflow is applied across all cyclone and lead-time combinations.

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
│   │       └── bgd_admbnda_adm3_bbs_20201113.shp
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
│       └── midhili/
│           ├── Forecasted_Impact_1dlt.xlsx
│           ├── Forecasted_Impact_2dlt.xlsx
│           ├── Forecasted_Impact_3dlt.xlsx
│           └── Midhili_ddm.xlsx
│
├── docs/
│   └── data_dictionary.md
│
├── notebooks/
│   └── 01_remal_validation.ipynb
│
├── outputs/
│   ├── remal/
│   ├── sitrang/
│   └── midhili/
│
├── scripts/
│   ├── check_inputs.py
│   └── run_analysis.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

> The notebook name is retained for compatibility, but the analysis is parameterized and used for all supported cyclones and lead times.

## Input data

Each cyclone requires:

1. three forecast impact workbooks
2. one observed DDM workbook
3. Bangladesh ADM3 administrative boundaries

### Forecast workbook

Expected forecast files:

```text
Forecasted_Impact_1dlt.xlsx
Forecasted_Impact_2dlt.xlsx
Forecasted_Impact_3dlt.xlsx
```

Required forecast fields include:

```text
ADM3_PCODE
District
Upazila
Norm_Impact_House
Norm_Impact_fAPAR
```

The current workbook layout uses:

| Excel column | Purpose |
|---|---|
| W | `Norm_Impact_fAPAR` |
| X | Agriculture/fAPAR severity class |
| AF | `Norm_Impact_House` |
| AG | House severity class |

If the workbook layout changes, the corresponding notebook column mapping must be updated.

### Observed DDM workbook

Each cyclone uses one observed workbook:

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

The same observed DDM workbook is used for all lead-time experiments of a cyclone.

## Configuration

Each cyclone has its own YAML configuration.

Example `configs/remal.yaml`:

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

Equivalent configuration files are used for Sitrang and Midhili.

Forecast severity thresholds are **not manually stored in YAML**. They are derived automatically from the selected forecast workbook.

# Methodology

## 1. Forecast severity thresholds

Forecast severity thresholds are derived independently for every cyclone and forecast lead time.

### House impact

For `Norm_Impact_House`, using the forecast severity class in Excel column `AG`:

```text
Low threshold
= maximum Norm_Impact_House where AG = "No Impact"

Moderate threshold
= maximum Norm_Impact_House where AG = "Low"

High threshold
= maximum Norm_Impact_House where AG = "Moderate"
```

### Agriculture/fAPAR impact

For `Norm_Impact_fAPAR`, using the forecast severity class in Excel column `X`:

```text
Low threshold
= maximum Norm_Impact_fAPAR where X = "No Impact"

Moderate threshold
= maximum Norm_Impact_fAPAR where X = "Low"

High threshold
= maximum Norm_Impact_fAPAR where X = "Moderate"
```

Derived thresholds are rounded to **five decimal places** before classification.

Forecast severity is reconstructed as:

```text
impact <= Low threshold
    → No Impact

Low threshold < impact <= Moderate threshold
    → Low

Moderate threshold < impact <= High threshold
    → Moderate

impact > High threshold
    → High
```

This ensures that each forecast file provides its own severity boundaries.

## 2. DDM severity calibration

Observed DDM impact values are classified as:

```text
No Impact
Low
Medium
High
```

Zero observed impact is assigned to `No Impact`.

For positive observed values, the workflow performs an exhaustive search over valid pairs of unique observed damage values:

```text
Low Cut
High Cut
```

For each candidate pair:

```text
value <= 0                  → No Impact
0 < value <= Low Cut        → Low
Low Cut < value <= High Cut → Medium
value > High Cut            → High
```

The optimal DDM cut pair is selected by maximizing **quadratic-weighted Kappa** against the fixed forecast severity classes.

## 3. Tertile benchmark

A benchmark classification is also calculated from non-zero observed DDM values:

```text
P33.33 → Low/Medium boundary
P66.67 → Medium/High boundary
```

The workflow reports:

- calibrated Kappa
- tertile Kappa
- Kappa improvement

## 4. Binary categorical verification

Forecast and observed impacts are converted to impact/no-impact outcomes.

| Forecast | Observed | Category |
|---|---|---|
| Impact | Impact | Hit |
| No Impact | Impact | Miss |
| Impact | No Impact | False Alarm |
| No Impact | No Impact | Correct Negative / True Negative |

Metrics include:

- Probability of Detection (POD)
- False Alarm Ratio (FAR)
- Critical Success Index (CSI)
- Frequency Bias
- Accuracy

## 5. No-impact threshold optimization

Candidate forecast thresholds are evaluated across percentile levels approximately from P5 to P50.

The decision score is:

```text
Decision Score = CSI - FAR - |Bias - 1|
```

The selected threshold balances detection skill, false alarms, and forecast frequency bias.

## 6. Continuous validation

Continuous validation includes:

- Pearson correlation
- Spearman rank correlation
- Kendall rank correlation
- coefficient of determination (R²)
- root mean square error (RMSE)
- Nash-Sutcliffe Efficiency (NSE)

## 7. ROC/AUC

Receiver Operating Characteristic analysis evaluates the ability of forecast impact values to discriminate observed impact from no-impact cases.

Outputs include ROC curves and Area Under the Curve (AUC).

## 8. Severity agreement

Four-level forecast and DDM severity classes are compared using quadratic-weighted Kappa.

Severity agreement is also summarized as:

```text
Exact
    Forecast and observed severity are identical.

Adjacent
    Forecast and observed severity differ by one class.

Off
    Forecast and observed severity differ by two or more classes.
```

## 9. Spatial validation

ADM3 boundaries are used to map categorical performance, including:

- Hit
- Miss
- False Alarm
- Correct Negative / True Negative

# Installation

## 1. Clone the repository

```bash
git clone <repository-url>
cd IBF-Analysis
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Recommended dependencies:

```text
numpy
pandas
scipy
matplotlib
openpyxl
geopandas
PyYAML
scikit-learn
jupyter
nbconvert
ipykernel
```

# Running the analysis

## Check inputs

```powershell
python scripts\check_inputs.py --cyclone remal --lead 1dlt
```

Examples:

```powershell
python scripts\check_inputs.py --cyclone sitrang --lead 2dlt
python scripts\check_inputs.py --cyclone midhili --lead 3dlt
```

The input checker validates the configuration, selected forecast workbook, required sheets and columns, DDM workbook, ADM3 boundary files, and output directory.

## Run one analysis

Syntax:

```powershell
python scripts\run_analysis.py <cyclone> <lead>
```

Examples:

```powershell
python scripts\run_analysis.py remal 1dlt
python scripts\run_analysis.py sitrang 2dlt
python scripts\run_analysis.py midhili 3dlt
```

Valid cyclone identifiers:

```text
remal
sitrang
midhili
```

Valid lead-time identifiers:

```text
1dlt
2dlt
3dlt
```

## Run all experiments

```powershell
python scripts\run_analysis.py --all
```

This runs all nine cyclone/lead-time combinations.

# Output structure

Each experiment is stored independently:

```text
outputs/
├── remal/
│   ├── 1dlt/
│   ├── 2dlt/
│   └── 3dlt/
├── sitrang/
│   ├── 1dlt/
│   ├── 2dlt/
│   └── 3dlt/
└── midhili/
    ├── 1dlt/
    ├── 2dlt/
    └── 3dlt/
```

A typical run contains:

```text
outputs/sitrang/2dlt/
├── AUC/
├── Validation/
├── No_Impact_Threshold_Optimization/
├── DDM_Categorization/
├── Hit_Map/
└── sitrang_2dlt_validation_executed.ipynb
```

## DDM categorization outputs

Example:

```text
outputs/sitrang/2dlt/DDM_Categorization/
├── Sitrang_2dlt_DDM_KappaCalibrated.xlsx
└── Sitrang_2dlt_Hit_Performance_Heatmap.png
```

The calibrated workbook contains:

- summary statistics
- House damaged-household classification
- House monetary-damage classification
- Agriculture land-loss classification
- Agriculture monetary-loss classification
- calibrated-versus-tertile contingency tables
- top Kappa calibration combinations

# Reproducibility

One parameterized validation notebook is used for all experiments.

The runner controls:

```text
Cyclone
Forecast lead time
Forecast workbook
Observed DDM workbook
Forecast worksheet
Output directory
```

This keeps the scientific workflow constant while changing only the cyclone, lead time, and corresponding inputs.

For reproducible analysis:

1. keep original input files unchanged
2. keep YAML configuration files under version control
3. record package versions
4. retain the executed notebook generated for each run
5. do not manually alter automatically derived forecast thresholds

# Data quality considerations

Before interpreting results, verify:

- administrative-name consistency
- ADM3 P-Code consistency
- duplicate Upazila records
- missing forecast or observed values
- forecast severity-class labels
- expected Excel column positions
- consistent units for observed impacts

The automatic threshold derivation requires valid `No Impact`, `Low`, and `Moderate` forecast classes in columns `AG` and `X`.

# Data and licensing

Before publishing this repository publicly, verify redistribution rights for:

- DDM post-disaster impact data
- Bangladesh administrative boundary data
- forecast impact datasets
- externally derived hazard, exposure, and vulnerability datasets

If redistribution is restricted, publish sample/template data and instructions for obtaining authorized source data rather than committing restricted datasets.

# Citation

If this repository is used in research or operational analysis, cite the repository release/version used.

A formal citation can be added once the repository has a DOI, archived release, or associated publication.

# License

Add an appropriate open-source software license before public release, such as:

- MIT License
- BSD 3-Clause License
- Apache License 2.0

The software license does not automatically grant redistribution rights for input datasets.

# Notes

The current workflow is structured around the forecast and DDM workbook formats used for Cyclones Remal, Sitrang, and Midhili.

If future datasets use different sheet names, Excel column positions, administrative naming conventions, observed-impact fields, or forecast-class labels, update the configuration and data-loading logic while preserving the validation methodology.

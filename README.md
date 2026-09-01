# IBF-Analysis

**A multi-sector impact-forecasting and validation framework for anticipatory action against tropical cyclones in Bangladesh**

Anticipatory action against tropical cyclones requires impact forecasts that can identify where damage is most likely before landfall. This repository accompanies research developed by Raihanul Haque Khan, Asif Bin Noor, Md. Ibrahim Abdullah, and Raisa Binte Ahmed at **RIMES** (Regional Integrated Multi-Hazard Early Warning System for Africa and Asia).

The framework integrates forecast hazards, baseline vulnerability, and sector-specific exposure into normalized housing and agricultural impact scores at ADM3/Upazila level in Bangladesh. Forecasts at 24-hour, 48-hour, and 72-hour lead times are evaluated against post-event damage records from the Department of Disaster Management (DDM) for Cyclones Remal, Midhili, and Sitrang.

The repository now contains three connected parts:

1. **Forecast impact preparation** from hazard, vulnerability, and exposure inputs.
2. **Impact forecast validation and calibration** against observed DDM damage.
3. **Standalone predictor comparison (ablation)** to test whether the full composite provides information beyond hazard alone or vulnerability alone.

![Framework overview: vulnerability, forecast hazard, and exposure combine into a composite impact score, which is validated through discrimination, threshold optimization, severity calibration, and spatial verification against DDM damage records](docs/images/framework_overview.png)

## What this framework does

The operational impact forecast combines three groups of information:

- **Baseline vulnerability:** INFORM Subnational Risk Index for Bangladesh.
- **Forecast hazard:** wind gust, rainfall, and storm surge.
- **Sector exposure:** building counts for housing and fAPAR-based agricultural exposure.

These inputs are used to produce normalized sector-specific impact scores:

- `Norm_Impact_House`
- `Norm_Impact_fAPAR`

The validation workflow then compares those forecast scores with observed DDM damage using continuous, binary, ordinal, and spatial verification methods.

Hazard-component weights in the operational impact formulation are event dependent, as described in the manuscript methodology. The separate hazard-only ablation analysis described below is a diagnostic comparison and uses its own fixed weighted hazard baseline.

## Supported cyclone cases

| Cyclone | Landfall | 1-day lead | 2-day lead | 3-day lead |
|---|---|---:|---:|---:|
| Remal | 26 May 2024 | ✓ | ✓ | ✓ |
| Sitrang | 24 Oct 2022 | ✓ | ✓ | ✓ |
| Midhili | 17 Nov 2023 | ✓ | ✓ | ✓ |

Repository lead-time identifiers are `1dlt`, `2dlt`, and `3dlt`.

## Workflow

```text
Hazard forecasts
    + Vulnerability
    + Sector exposure
            |
            v
forecasted_impact_engine.py
            |
            v
Forecast impact workbook
            |
            v
Validation and calibration
    - Continuous association
    - ROC/AUC
    - Mann-Whitney U
    - No-Impact threshold optimization
    - Quadratic-weighted Kappa calibration
    - Exact / Adjacent / Off-category agreement
    - Spatial Hit / Miss / False Alarm / True Negative verification
            |
            v
Standalone predictor comparison
    Composite vs Vulnerability-only vs Hazard-only
```

## Forecasted Impact Engine

`scripts/forecasted_impact_engine.py` prepares the forecast impact workbook by matching hazard, vulnerability, and exposure inputs using ADM3 P-Codes.

### Inputs

The sample inputs are stored under:

```text
data/sample/impact forecast data sample/
├── Forecasted_Impact_Dummy.xlsx
├── building_count.xlsx
├── faapar.xlsx
├── rainfall.xlsx
├── stormsurge.xlsx
├── vulnerability.xlsx
└── windgust.xlsx
```

The script processes:

- **Wind gust:** maximum forecast value across the selected forecast records, converted from m/s to km/h.
- **Rainfall:** accumulated rainfall difference from the specified forecast rows, converted to mm.
- **Storm surge:** matched directly by ADM3 P-Code.
- **Vulnerability:** matched by ADM3 P-Code.
- **fAPAR:** matched by ADM3 P-Code.
- **Building exposure:** matched by ADM3 P-Code.

The values are written into `Forecasted_Impact_Dummy.xlsx`, preserving the impact-template structure, and saved as:

```text
outputs/Forecasted_Impact.xlsx
```

Run from the repository root:

```bash
python scripts/forecasted_impact_engine.py
```

The script prints the number of input records and successful ADM3 P-Code matches before saving the output.

## Validation suite

Forecast impact scores are evaluated against DDM post-event damage records using complementary methods.

### Continuous association

Continuous forecast scores are compared with observed damage for complete positive forecast-observation pairs using:

- Ordinary least squares
- Pearson correlation
- Spearman rank correlation
- Kendall rank correlation
- `log1p` transformation of observed damage where applied in the analysis

### Threshold-independent discrimination

- ROC curves
- Area under the ROC curve (AUC)
- One-sided Mann-Whitney U test

These analyses test whether the continuous forecast signal discriminates impacted from non-impacted locations without fixing a single decision threshold.

### No-Impact threshold optimization

Candidate percentile thresholds are evaluated using:

```text
Decision Score = CSI - FAR - |Bias - 1|
```

The selected threshold defines the calibrated No-Impact decision boundary for the evaluated event, sector, and lead time.

Because the same DDM observations are used for threshold selection and threshold-dependent verification, POD, FAR, CSI, Frequency Bias, and Accuracy at the selected threshold are interpreted as **calibration diagnostics**, not independent out-of-sample skill estimates.

### Severity calibration

Observed DDM damage is converted into ordered severity classes:

```text
No Impact
Low
Moderate
High
```

For each damage variable, one fixed DDM Low/High cut pair is selected for a cyclone by maximizing the **mean quadratic-weighted Kappa across 1dlt, 2dlt, and 3dlt**.

The same DDM cut pair is then applied unchanged to all three lead times.

Agreement is summarized using:

- Quadratic-weighted Kappa
- Exact-category agreement
- Adjacent-category agreement
- Off-category error

### Spatial verification

Forecast and observed categories are matched at ADM3/Upazila level and classified as:

- Hit
- Miss
- False Alarm
- True Negative

Spatial outputs use the Bangladesh ADM3 boundary data included under `data/reference/bangladesh_adm3/`.


## Standalone Vulnerability Categorization

For the vulnerability-only ablation, vulnerability is treated as a **static pre-event condition** and is evaluated independently from the operational impact model. Therefore, vulnerability categories are not recalibrated separately for different forecast lead times or cyclone events.

The normalized vulnerability index (`Norm_Vul`) is converted into four ordinal vulnerability categories using fixed percentile-based thresholds derived from the vulnerability distribution.

The workflow is implemented in:

```text
scripts/vulnerability_categorization.py
```

The workflow is:

```text
Norm_Vul values
        |
        v
Calculate fixed percentile thresholds
        |
        v
Generate vulnerability categories
        |
        v
Apply the same categories across all lead times
        |
        v
Standalone vulnerability Kappa evaluation
```

The generated vulnerability classes represent:

| Vulnerability category | Description |
|---|---|
| No Impact proxy | Lowest vulnerability group based on the selected percentile threshold |
| Low | Lower vulnerability group |
| Moderate | Intermediate vulnerability group |
| High | Highest vulnerability group |

The generated outputs are stored under:

```text
outputs/vulnerability_categories/

├── Remal_Vulnerability_Categories.xlsx
├── Midhili_Vulnerability_Categories.xlsx
└── Sitrang_Vulnerability_Categories.xlsx
```

Each output contains:

```text
P Code
ADM3_PCODE
District
Upazila
Norm_Vul
Vulnerability_Category
Vulnerability_Class
```

These vulnerability classes are used in:

```text
scripts/ablation_kappa_comparison_all_cyclones.py
```

for standalone comparison against:

- Composite IBF impact forecast
- Weighted hazard-only predictor

This separation ensures that vulnerability-only performance represents the contribution of baseline susceptibility alone and is not influenced by cyclone-specific hazard calibration or forecast lead time.


## Standalone Predictor Comparison (Ablation)

The repository also includes an ablation workflow to determine whether the full composite impact forecast adds information beyond hazard alone or vulnerability alone.

The script is:

```text
scripts/ablation_kappa_comparison_all_cyclones.py
```

It processes **Remal, Midhili, and Sitrang in one run** and compares three predictors:

| Predictor | Definition |
|---|---|
| Composite | Existing sector-specific IBF composite score |
| Vulnerability alone | `Norm_Vul` |
| Hazard-only (weighted) | `0.35 × Norm_Wind Gust + 0.35 × Norm_Rainfall + 0.30 × Norm_Storm Surge` |

Two separate classifications enter this comparison and they are handled differently.

**Observation side.** For each predictor and damage variable, the DDM Low/High cut pair is calibrated using the same three-lead quadratic-weighted Kappa search used in the main severity-calibration workflow. The search is run independently for each predictor, so every predictor is scored at the DDM class boundaries that maximize its own agreement rather than at boundaries tuned to the Composite.

**Forecast side.** The Composite retains the optimized Kappa calibration used throughout the main validation workflow. Both reduced predictors are instead classified independently of the operational impact model: because neither carries the exposure term that the operational calibration is built around, lead-time-specific calibration is avoided for both, and each is converted into four ordinal categories using fixed percentile-based thresholds derived from its own score distribution.

Because both the vulnerability index and its thresholds are static, vulnerability-only Kappa is identical at `1dlt`, `2dlt` and `3dlt` for every cyclone and damage variable, and it therefore acts as a lead-time-invariant reference. The hazard-only score varies across lead times because the hazard field itself changes, not because its class boundaries move.

Run:

```bash
python scripts/ablation_kappa_comparison_all_cyclones.py
```

The script creates **Excel outputs only**:

```text
outputs/remal/Ablation_Kappa_Comparison/
└── Remal_Ablation_Kappa_Comparison.xlsx

outputs/midhili/Ablation_Kappa_Comparison/
└── Midhili_Ablation_Kappa_Comparison.xlsx

outputs/sitrang/Ablation_Kappa_Comparison/
└── Sitrang_Ablation_Kappa_Comparison.xlsx
```

Each workbook contains:

```text
All_Comparisons
Housing_NoTotal
Housing_Amt
Agri_Land
Agri_Amt
Audit
Method
```

The comparison tables report:

```text
Predictor
Lead
n
DDM cut-points (Low / High)
Kappa
Exact %
Adjacent %
Off-Cat. %
```

### Threshold-independent (AUC) component comparison

The component comparison is run on two metrics, because they measure different things and do not agree. AUC scores the rank ordering of the raw predictor score against the binary damaged/undamaged outcome and is independent of any decision threshold. Quadratic-weighted Kappa scores the four-class assignment after event-specific cut-point calibration. A predictor can rank poorly but bin well, so both are reported.

| Cyclone | Lead | Sector | Composite AUC | Vulnerability alone AUC | Hazard-only AUC | Composite > hazard-only? |
|---|---|---|---:|---:|---:|---|
| Remal | 1dlt | Housing | 0.827 | 0.812 | 0.866 | No |
| Remal | 1dlt | Agriculture | 0.649 | 0.559 | 0.634 | Yes |
| Remal | 2dlt | Housing | 0.815 | 0.805 | 0.888 | No |
| Remal | 2dlt | Agriculture | 0.683 | 0.552 | 0.709 | No |
| Remal | 3dlt | Housing | 0.742 | 0.812 | 0.846 | No |
| Remal | 3dlt | Agriculture | 0.634 | 0.559 | 0.653 | No |
| Midhili | 1dlt | Housing | 0.580 | 0.566 | 0.764 | No |
| Midhili | 1dlt | Agriculture | 0.730 | 0.647 | 0.727 | Yes |
| Midhili | 2dlt | Housing | 0.582 | 0.566 | 0.752 | No |
| Midhili | 2dlt | Agriculture | 0.725 | 0.647 | 0.746 | No |
| Midhili | 3dlt | Housing | 0.531 | 0.566 | 0.652 | No |
| Midhili | 3dlt | Agriculture | 0.603 | 0.647 | 0.534 | Yes |
| Sitrang | 1dlt | Housing | 0.492 | 0.600 | 0.663 | No |
| Sitrang | 1dlt | Agriculture | 0.617 | 0.585 | 0.694 | No |
| Sitrang | 2dlt | Housing | 0.503 | 0.600 | 0.665 | No |
| Sitrang | 2dlt | Agriculture | 0.582 | 0.585 | 0.621 | No |
| Sitrang | 3dlt | Housing | 0.495 | 0.600 | 0.661 | No |
| Sitrang | 3dlt | Agriculture | 0.519 | 0.585 | 0.516 | Yes |

On AUC the picture is less favourable to the Composite than on Kappa. Weighted hazard alone exceeds the Composite in **all nine** housing combinations. In agriculture the Composite exceeds hazard alone in 4 of 9 combinations and is the highest of the three predictors in 2 of 9.

The two metrics disagree because the Composite's multiplication by vulnerability and exposure compresses the score distribution, which can help four-class assignment after calibration while hurting the raw rank ordering that AUC measures.

### Cross-cyclone Kappa ablation summary

Using the current three-cyclone sample outputs:

Averaged across all 36 cyclone-sector-lead-variable combinations, and across the 18 housing and 18 agricultural combinations separately:

| Predictor | Overall mean Kappa | Housing mean Kappa | Agriculture mean Kappa | Mean Off-Cat. % |
|---|---:|---:|---:|---:|
| Composite | **0.3411** | 0.2828 | **0.3995** | **14.07%** |
| Vulnerability alone | 0.2926 | 0.2935 | 0.2917 | 30.67% |
| Hazard-only (weighted) | 0.2913 | **0.3235** | 0.2591 | 18.30% |

By cyclone, averaged across the 12 combinations for each event:

| Cyclone | Composite | Vulnerability alone | Hazard-only (weighted) | Highest mean Kappa |
|---|---:|---:|---:|---|
| Remal | 0.5151 | 0.4097 | **0.5394** | Hazard-only |
| Midhili | **0.3536** | 0.2174 | 0.2230 | Composite |
| Sitrang | 0.1546 | **0.2507** | 0.1115 | Vulnerability alone |

The ablation result supports a **sector-specific and event-dependent interpretation**. The Composite has the highest overall mean Kappa and the strongest agricultural performance across the three cyclones, and is the best of the three predictors in 14 of the 18 agricultural combinations. Weighted hazard alone has the highest cross-cyclone housing mean Kappa and wins Remal outright. Vulnerability alone is the strongest predictor for Sitrang in both sectors, and across the full sample it is statistically indistinguishable from weighted hazard alone, the two being separated by 0.0013.

Accordingly, the analysis should not be interpreted as evidence that the Composite universally outperforms every simpler predictor. Its clearest added value is for agricultural impact severity and in the aggregate cross-cyclone comparison, and neither standalone predictor is superior across all events and sectors.

Margins between predictors are small in several cells. Differences below roughly 0.01 in mean Kappa should not be treated as meaningful, and no confidence intervals or tests of difference are computed.

## Example outputs

The figures below are examples generated from the repository sample data.

**Discrimination skill, Cyclone Remal, 24-hour lead:**

![ROC curves for Remal damage variables](docs/images/example_roc_auc.png)

**No-Impact threshold optimization, Cyclone Remal, housing, 24-hour lead:**

![Threshold optimization example](docs/images/example_threshold_optimization.png)

**Severity calibration, Cyclone Remal, 24-hour lead:**

![Severity calibration confusion matrices](docs/images/example_severity_calibration.png)

**Spatial verification across the three cyclones:**

![Spatial impact verification for Remal, Midhili, and Sitrang](docs/images/impact_hitmap.jpeg)

## Results at a glance

The table below illustrates the calibrated categorical comparison for Cyclone Remal.

| Cyclone | Lead Time | Variable | n | Exact Match (n) | Exact Match (%) | Adjacent (n) | Within-1-Class (n) | Within-1-Class (%) | Off-Category Error (%) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Remal | 24h | House: No. Damaged Households | 154 | 96 | 62.3% | 52 | 148 | 96.1% | 3.9% |
| Remal | 24h | House: Repair Amount (BDT) | 154 | 89 | 57.8% | 56 | 145 | 94.2% | 5.8% |
| Remal | 24h | Agriculture: Land Loss (ha) | 154 | 38 | 24.7% | 98 | 136 | 88.3% | 11.7% |
| Remal | 24h | Agriculture: Loss Amount (BDT) | 154 | 51 | 33.1% | 92 | 143 | 92.9% | 7.1% |
| Remal | 48h | House: No. Damaged Households | 154 | 106 | 68.8% | 46 | 152 | 98.7% | 1.3% |
| Remal | 48h | House: Repair Amount (BDT) | 154 | 101 | 65.6% | 48 | 149 | 96.8% | 3.2% |
| Remal | 48h | Agriculture: Land Loss (ha) | 154 | 56 | 36.4% | 82 | 138 | 89.6% | 10.4% |
| Remal | 48h | Agriculture: Loss Amount (BDT) | 154 | 59 | 38.3% | 81 | 140 | 90.9% | 9.1% |
| Remal | 72h | House: No. Damaged Households | 154 | 91 | 59.1% | 53 | 144 | 93.5% | 6.5% |
| Remal | 72h | House: Repair Amount (BDT) | 154 | 88 | 57.1% | 56 | 144 | 93.5% | 6.5% |
| Remal | 72h | Agriculture: Land Loss (ha) | 154 | 53 | 34.4% | 77 | 130 | 84.4% | 15.6% |
| Remal | 72h | Agriculture: Loss Amount (BDT) | 154 | 57 | 37.0% | 75 | 132 | 85.7% | 14.3% |

Within-1-Class agreement is the sum of Exact and Adjacent agreement. Off-category error represents a forecast-observation severity difference of two or more classes.

## Repository structure

```text
IBF-Analysis/
├── configs/
│   ├── earth_engine.yaml
│   ├── midhili.yaml
│   ├── remal.yaml
│   └── sitrang.yaml
│
├── data/
│   ├── reference/
│   │   └── bangladesh_adm3/
│   │       └── BBS ADM3 boundary shapefile components
│   │
│   └── sample/
│       ├── impact forecast data sample/
│       │   ├── Forecasted_Impact_Dummy.xlsx
│       │   ├── building_count.xlsx
│       │   ├── faapar.xlsx
│       │   ├── rainfall.xlsx
│       │   ├── stormsurge.xlsx
│       │   ├── vulnerability.xlsx
│       │   └── windgust.xlsx
│       │
│       ├── midhili/
│       │   ├── Cyclone_Midhili_Observed_Damage_Data.xlsx
│       │   ├── Forecasted_Impact_1dlt.xlsx
│       │   ├── Forecasted_Impact_2dlt.xlsx
│       │   └── Forecasted_Impact_3dlt.xlsx
│       │
│       ├── remal/
│       │   ├── Cyclone_Remal_Observed_Damage_Data.xlsx
│       │   ├── Forecasted_Impact_1dlt.xlsx
│       │   ├── Forecasted_Impact_2dlt.xlsx
│       │   └── Forecasted_Impact_3dlt.xlsx
│       │
│       └── sitrang/
│           ├── Cyclone_Sitrang_Observed_Damage_Data.xlsx
│           ├── Forecasted_Impact_1dlt.xlsx
│           ├── Forecasted_Impact_2dlt.xlsx
│           └── Forecasted_Impact_3dlt.xlsx
│
├── docs/
│   ├── data_dictionary.md
│   ├── transformation_methods.md
│   └── images/
│       ├── framework_overview.png
│       ├── example_roc_auc.png
│       ├── example_threshold_optimization.png
│       ├── example_severity_calibration.png
│       └── impact_hitmap.jpeg
│
├── notebooks/
│   └── 01_remal_validation.ipynb
│
├── scripts/
│   ├── ablation_kappa_comparison_all_cyclones.py
│   ├── check_inputs.py
│   ├── download_building_counts.py
│   ├── fapar_processing.py
│   ├── fapar_zonal_stats.py
│   ├── forecasted_impact_engine.py
│   ├── run_analysis.py
│   ├── transformation_comparison.py
│   └── legacy/
│       ├── IBF-Analysis-original.ipynb
│       └── upazila_building_count_download.js
│
├── outputs/
│   └── generated validation, calibration, spatial, and ablation products
│
├── CITATION.cff
├── LICENSE
├── README.md
├── requirements.txt
├── requirements-lock.txt
└── run_command.txt
```

The tree above focuses on the main analysis files and intentionally summarizes shapefile components and generated outputs.

## Running the workflow

### Check inputs

```bash
python scripts/check_inputs.py --cyclone remal --lead 1dlt
```

### Run one cyclone and lead time

```bash
python scripts/run_analysis.py remal 1dlt
```

### Run all cyclone/lead-time combinations

```bash
python scripts/run_analysis.py --all
```

### Prepare a forecast impact workbook

```bash
python scripts/forecasted_impact_engine.py
```

### Run the standalone predictor comparison for all three cyclones

```bash
python scripts/ablation_kappa_comparison_all_cyclones.py
```

### Run the validation notebook interactively

```bash
python -m jupyter notebook notebooks/01_remal_validation.ipynb
```

Validation outputs are written under `outputs/<cyclone>/<lead>/`. Ablation outputs are written under `outputs/<cyclone>/Ablation_Kappa_Comparison/`.

## Optional preprocessing utilities

### fAPAR zonal processing

```bash
python scripts/fapar_zonal_stats.py remal
python scripts/fapar_zonal_stats.py --all
```

The workflow derives fAPAR-based zonal agricultural exposure/loss information from before/after raster inputs.

### Building-count processing

```bash
python scripts/download_building_counts.py "Bangladesh"
```

This utility provides a scripted route for preparing building-count exposure information.

## Reproducibility scope

This repository includes code and sample data for:

- Preparing the forecast impact input workbook from hazard, vulnerability, and exposure data.
- Running the statistical validation reported in the manuscript.
- Optimizing No-Impact decision thresholds.
- Calibrating DDM severity classes with cyclone-wide fixed thresholds across three lead times.
- Producing spatial verification outputs.
- Comparing the full Composite against standalone vulnerability and weighted hazard predictors for all three cyclones, on both quadratic-weighted Kappa and AUC.

The component comparison tables in this README correspond to Tables S4, S5 and S6 of the manuscript. The calibrated categorical results correspond to Tables 4a and 4b.

The forecast impact engine populates the supplied impact template with matched hazard, vulnerability, and exposure values. The operational composite formula, normalization structure, and event-specific hazard weighting should be interpreted together with the methodology described in the manuscript and the formulas retained in the supplied forecast-impact template.

The ablation workflow is a comparative calibration analysis. Because its DDM cut-points are optimized using the same observed cyclone data against which Kappa is calculated, the resulting Kappa values should be interpreted as **in-sample comparative calibration diagnostics**, not independent out-of-sample estimates of predictive skill.

## Data sources

- **Observed damage:** Department of Disaster Management (DDM), Bangladesh.
- **Administrative boundaries:** Bangladesh Bureau of Statistics ADM3 boundaries.
- **Vulnerability:** INFORM Subnational Risk Index, Bangladesh.
- **Wind and rainfall forecasts:** ECMWF IFS-HRES.
- **Storm surge:** INCOIS ADCIRC+SWAN products.
- **Building exposure:** Google-Microsoft Open Buildings / associated building-count workflow.
- **Agricultural exposure:** fAPAR-based vegetation information.

Third-party datasets remain subject to the terms of their source organizations.

## Citation

See [`CITATION.cff`](CITATION.cff). If you use this repository, cite the associated manuscript once published and the archived software release when available.

## License

Source code is released under the [MIT License](LICENSE). Third-party data remain subject to their respective source terms.

## Status

Manuscript under review at *npj Natural Hazards*. The repository is intended to reflect the code and sample-data workflow used for the submitted and revised analyses.

\# IBF-Analysis Data Dictionary



This document describes the input data required to reproduce the

Impact-Based Forecasting (IBF) validation analysis.



\## 1. Forecast Impact Data



File:



data/sample/remal/Forecasted\_Impact.xlsx



Sheet:



Remal



\### Required administrative columns



| Column | Description |

|---|---|

| ADM3\_PCODE | Administrative Level 3 / Upazila P-Code |

| District | District name |

| Upazila | Upazila name |



\### Main forecast impact variables



| Column | Description |

|---|---|

| Norm\_Impact\_House | Normalized forecast impact score for housing |

| Norm\_Impact\_fAPAR | Normalized forecast impact score for agriculture/fAPAR |



Both impact variables are expected to be numeric and normally bounded

between 0 and 1.



Additional hazard, vulnerability, exposure, and impact-class columns may

also be present in this workbook.





\## 2. Observed Impact Data



File:



data/sample/remal/Remal\_ddm.xlsx



Observed post-cyclone impact data were obtained from the Department of

Disaster Management (DDM).



The workbook contains separate sheets for housing and agricultural impacts.





\## 2.1 House Sheet



Sheet:



House



Expected structure:



| Excel Column | Variable | Description |

|---|---|---|

| A | District | District name |

| B | Upazila | Upazila name |

| C | No\_Brick | Number of affected brick houses |

| D | No\_HalfBrick | Number of affected semi-pucca/half-brick houses |

| E | No\_Raw | Number of affected raw/kutcha houses |

| F | No\_Total | Total number of affected houses |

| G | Amt\_Brick | Estimated monetary loss for brick houses |

| H | Amt\_HalfBrick | Estimated monetary loss for half-brick houses |

| I | Amt\_Raw | Estimated monetary loss for raw houses |

| J | Amt\_Total | Total estimated housing loss |



The first two rows of the sheet contain metadata/header information and

are skipped during processing.





\## 2.2 Agriculture Sheet



Sheet:



Agriculture



Expected structure:



| Excel Column | Variable | Description |

|---|---|---|

| A | District | District name |

| B | Upazila | Upazila name |

| C | Fully\_Land | Fully damaged agricultural land |

| D | Fully\_Amt | Estimated loss from fully damaged crops |

| E | Partial\_Land | Partially damaged agricultural land |

| F | Partial\_Amt | Estimated loss from partially damaged crops |

| G | Total\_Loss\_Land | Total affected agricultural land |

| H | Total\_Loss\_Amt | Total estimated agricultural loss |



The first two rows of the sheet contain metadata/header information and

are skipped during processing.





\## 3. Administrative Matching



Forecast and observed datasets are matched at Upazila level.



Preferred identifier:



ADM3\_PCODE



Where P-Code is unavailable in the observed dataset, matching is performed

using:



District + Upazila



District and Upazila names are cleaned before matching by removing leading

and trailing whitespace.





\## 4. Missing Data



Missing DDM observations are not interpreted automatically as zero damage.



Records without valid paired forecast and observed values are excluded

from statistical analyses requiring complete pairs.



Observed zero values represent reported no-impact cases where appropriate.





\## 5. Expected Value Types



| Variable type | Expected format |

|---|---|

| ADM3\_PCODE | Text/string |

| District | Text/string |

| Upazila | Text/string |

| Forecast impact scores | Numeric |

| House damage counts | Numeric |

| Monetary losses | Numeric |

| Agricultural losses | Numeric |





\## 6. Spatial Boundary Data



Administrative Level 3 boundary data are required for mapping.



Expected location:



data/reference/bangladesh\_adm3/



The boundary dataset must contain:



ADM3\_PCODE



which is used to join forecast impact information with Upazila polygons.


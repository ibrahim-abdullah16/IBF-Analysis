# Data transformation — methodology text and supporting evidence

Numbers below are computed from `data/sample/remal/Remal_ddm.xlsx` on the
non-zero observations, which is the sample the regression analysis uses after
the `X > 0 and Y > 0` constraint. Reproduce with:

```
python scripts/transformation_comparison.py --cyclone remal --lead 1dlt
```

---

## Draft methodology text

### Distributional assessment and choice of transformation

Observed damage reported by the Department of Disaster Management is recorded
at upazila level and is extremely right-skewed. Across the four impact
variables used in this study, raw skewness ranges from 3.35 to 8.58 (mean
5.09) and excess kurtosis from 14.5 to 111.2. The largest reported value
exceeds the median by a factor of 189 for damaged houses and 1,006 for
agricultural land lost. Shapiro–Wilk tests reject normality for every variable
at p < 0.001. A small number of severely affected upazilas therefore dominate
any analysis conducted on the raw scale, and an untransformed regression would
be governed by a handful of high-leverage points rather than by the general
relationship.

Four candidate transformations were evaluated against the logarithmic
transformation.

**Z-score standardisation and Min–Max scaling** are linear rescalings. Because
skewness and kurtosis are invariant under affine transformation, both leave the
distribution shape unchanged: skewness remains 3.35 to 8.58 and the
Shapiro–Wilk results are identical to the raw data. Neither addresses the
problem, and both were excluded on that basis.

**Box–Cox** requires strictly positive input. The DDM records contain 23
upazilas with zero housing damage and 44 with zero agricultural loss, so
application would require either an arbitrary additive constant or exclusion of
all no-damage locations from the distributional assessment.

**Yeo–Johnson** accommodates zeros and negative values and achieves the lowest
residual skewness of the methods tested (mean |skewness| = 0.03). Its
transformation parameter λ is estimated from the sample, however, and therefore
differs by variable, by cyclone and by forecast lead time.

The transformation adopted is

    Y′ = log(Y + 1)

applied to the observed damage variable. The predicted impact score is a
normalised index already bounded on [0, 1] and is analysed on its original
scale; the transformation is applied to the response only, consistent with the
requirement that the distributional assumptions of least-squares regression
concern the residuals rather than the predictor.

Two considerations support this choice.

First, the logarithm is the transformation the data themselves select. Fitting
Box–Cox independently to each variable in each of the three cyclones gives
twelve estimates of λ spanning −0.037 to +0.241, with a mean absolute value of
0.088. Since Box–Cox with λ = 0 is defined as the natural logarithm, the fitted
optimum lies close to the logarithmic case throughout. The logarithm is
therefore not an approximation adopted for convenience but the limiting form
that maximum-likelihood estimation approaches for these variables.

Second, fixing λ = 0 rather than estimating it preserves comparability. A
sample-estimated λ varies across the analysis: for house repair cost it ranges
from −0.037 for Remal to +0.241 for Midhili. Regression coefficients obtained
under different λ values are expressed on different scales and cannot be
compared across cyclones or lead times, which is a requirement of a study
spanning nine cyclone and lead-time combinations. The logarithm applies one
identical, parameter-free transformation to every variable in every run.

Empirically the transformation is adequate for its purpose. Mean skewness falls
from 5.09 to −0.10, with all four variables brought within |skewness| < 0.45,
and excess kurtosis falls from a mean of 45.3 to below 1 in absolute value. The
additive constant of one preserves zero-valued observations, which is required
for the distributional summaries and the class boxplots computed on the full
sample.

Yeo–Johnson and Box–Cox achieve marginally better normality than the logarithm
on this sample (mean Shapiro–Wilk p of 0.188 and 0.205 against 0.047). The
logarithm was retained because the gain is small relative to the loss of a
single, reproducible and physically interpretable scale, on which a regression
slope represents a proportional change in reported damage per unit of predicted
impact.

Transformed distributions were inspected through histograms and Q–Q plots to
confirm reduced skewness and improved symmetry. Rank-based statistics
(Spearman ρ, Kendall τ) are invariant under any monotone transformation and are
therefore unaffected by this choice, so the monotonic association results
reported in Section X do not depend on the transformation adopted.

---

## Table X. Distribution shape before and after transformation

Cyclone Remal, non-zero observations.

| Variable | n | Raw | Z-score | Min–Max | Log(Y+1) | Yeo–Johnson | Box–Cox |
|---|---:|---:|---:|---:|---:|---:|---:|
| Damaged houses | 131 | 3.72 | 3.72 | 3.72 | 0.14 | 0.01 | 0.00 |
| House repair cost | 131 | 3.35 | 3.35 | 3.35 | 0.19 | 0.02 | 0.02 |
| Agricultural land lost | 109 | 8.58 | 8.58 | 8.58 | −0.29 | −0.04 | −0.05 |
| Agricultural loss value | 109 | 4.71 | 4.71 | 4.71 | −0.44 | −0.04 | −0.04 |
| **Mean skewness** | | **5.09** | **5.09** | **5.09** | **−0.10** | **−0.01** | **−0.02** |
| **Mean \|skewness\|** | | **5.09** | **5.09** | **5.09** | **0.26** | **0.03** | **0.03** |
| **Mean Shapiro–Wilk p** | | **0.0000** | **0.0000** | **0.0000** | **0.0471** | **0.1881** | **0.2054** |
| **Variables normal at p ≥ 0.05** | | 0 / 4 | 0 / 4 | 0 / 4 | 1 / 4 | 2 / 4 | 2 / 4 |

Values are skewness unless otherwise stated.

## Table Y. Fitted Box–Cox λ by variable and cyclone

Non-zero observations. λ = 0 corresponds to the logarithmic transformation.

| Variable | Remal | Midhili | Sitrang | Range |
|---|---:|---:|---:|---:|
| Damaged houses | −0.011 | 0.165 | 0.080 | 0.176 |
| House repair cost | −0.037 | 0.241 | 0.009 | 0.278 |
| Agricultural land lost | 0.085 | 0.166 | −0.020 | 0.186 |
| Agricultural loss value | 0.080 | 0.153 | −0.013 | 0.166 |

All twelve estimates fall within −0.037 to +0.241, mean |λ| = 0.088.

## Figures

`ddm_skewness_raw_vs_log.png`
Histograms of the four DDM damage variables before and after the log
transformation, annotated with skewness, excess kurtosis, the ratio of maximum
to median, and the count of zero-damage upazilas.

`boxcox_lambda_stability.png`
Fitted Box–Cox λ for each variable and cyclone against the λ = 0 reference.

---

## Points to check before submission

The raw skewness reported in the current draft (mean 0.44) does not match these
data. Raw skewness of the DDM damage variables is 3.35 to 8.58 on the non-zero
sample and 3.67 to 10.07 on the full sample including zeros. The higher figures
strengthen the case for transforming, so the table should be regenerated.

The current draft states the transformation as X′ = log(X+1), Y′ = log(Y+1).
The code applies it to the observed variable only, which is the appropriate
choice; the equation should show Y′ alone.

The stated justification refers to "the normality assumptions required for
correlation and regression analysis". Least-squares regression assumes
approximate normality and constant variance of the residuals, not of the
variables. Reporting Shapiro–Wilk on residuals, and a Breusch–Pagan or White
test for heteroscedasticity, before and after transformation, would support the
choice on the correct grounds.

Sub-variables with n = 14 (`No_Brick`, `Amt_Brick`) are too small to report as
results. `Amt_Brick` moves from r = 0.451 on the raw scale to r = 0.0007 on the
log scale, which indicates a single high-leverage observation.

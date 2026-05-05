# Atlanta Food System — Spatial / Variable Analysis

_Generated 2026-04-28T15:43:25 · n = 530 tracts_

## Pullnumbers
```json
{
  "n_tracts": 530,
  "n_lila": 57,
  "lila_pct": 10.8,
  "n_severe_crit": 49,
  "pop_total": 1823153,
  "no_vehicle_pop": 100265,
  "avg_mrfei": 38.0,
  "fastfood_lila_vs_nonlila": {
    "lila_mean": 0.63,
    "non_lila_mean": 1.0,
    "ratio": 0.63
  },
  "convenience_lila_vs_nonlila": {
    "lila_mean": 0.89,
    "non_lila_mean": 0.55,
    "ratio": 1.63
  },
  "supermarket_lila_vs_nonlila": {
    "lila_mean": 0.05,
    "non_lila_mean": 0.24
  },
  "no_vehicle_lila_vs_nonlila": {
    "lila_mean_pct": 7.02,
    "non_lila_mean_pct": 5.98,
    "diff_pct_pts": 1.04
  }
}
```

## Top correlations with **Food Access Gap Score**

| predictor             |   n |   pearson_r |   spearman_rho |     p_value |   r_squared |
|:----------------------|----:|------------:|---------------:|------------:|------------:|
| poverty_rate          | 528 |       0.377 |          0.414 | 2.76783e-19 |       0.142 |
| obesity_rate          | 528 |       0.369 |          0.367 | 1.65042e-18 |       0.136 |
| convenience_count     | 530 |       0.366 |          0.376 | 3.14844e-18 |       0.134 |
| food_insecurity_rate  | 528 |       0.354 |          0.385 | 4.56175e-17 |       0.126 |
| median_income         | 519 |      -0.338 |         -0.398 | 2.56088e-15 |       0.114 |
| diabetes_rate         | 528 |       0.33  |          0.374 | 7.47634e-15 |       0.109 |
| nearest_healthy_miles | 530 |       0.324 |          0.291 | 1.93682e-14 |       0.105 |
| snap_rate             | 526 |       0.295 |          0.357 | 5.45737e-12 |       0.087 |
| supermarket_count     | 530 |      -0.277 |         -0.284 | 8.17163e-11 |       0.077 |
| pct_no_vehicle        | 526 |       0.267 |          0.26  | 4.65022e-10 |       0.071 |


## Top correlations with **mRFEI**

| predictor             |   n |   pearson_r |   spearman_rho |     p_value |   r_squared |
|:----------------------|----:|------------:|---------------:|------------:|------------:|
| grocery_count         | 363 |       0.438 |          0.615 | 1.74312e-18 |       0.192 |
| convenience_count     | 363 |      -0.37  |         -0.373 | 3.08566e-13 |       0.137 |
| fastfood_count        | 363 |      -0.309 |         -0.403 | 1.88603e-09 |       0.095 |
| nearest_healthy_miles | 363 |      -0.3   |         -0.379 | 5.42702e-09 |       0.09  |
| supermarket_count     | 363 |       0.297 |          0.375 | 7.49768e-09 |       0.088 |
| farmers_market_count  | 363 |       0.186 |          0.2   | 0.000373185 |       0.035 |
| food_insecurity_rate  | 363 |       0.121 |          0.057 | 0.0212801   |       0.015 |
| poverty_rate          | 363 |       0.118 |          0.066 | 0.0241525   |       0.014 |
| pct_no_vehicle        | 363 |       0.106 |          0.068 | 0.0433938   |       0.011 |
| snap_rate             | 363 |       0.102 |          0.048 | 0.0510897   |       0.011 |


## Top correlations with **CDC food-insecurity rate**

| predictor         |   n |   pearson_r |   spearman_rho |      p_value |   r_squared |
|:------------------|----:|------------:|---------------:|-------------:|------------:|
| obesity_rate      | 528 |       0.919 |          0.922 | 9.42251e-215 |       0.845 |
| diabetes_rate     | 528 |       0.813 |          0.787 | 1.23517e-125 |       0.661 |
| snap_rate         | 526 |       0.803 |          0.839 | 5.42e-120    |       0.645 |
| poverty_rate      | 528 |       0.78  |          0.759 | 2.26646e-109 |       0.609 |
| median_income     | 519 |      -0.729 |         -0.873 | 4.03673e-87  |       0.531 |
| pct_no_vehicle    | 526 |       0.537 |          0.44  | 1.48939e-40  |       0.288 |
| unemployment_rate | 527 |       0.44  |          0.464 | 2.05711e-26  |       0.194 |
| grocery_count     | 528 |       0.212 |          0.147 | 9.35823e-07  |       0.045 |
| supermarket_count | 528 |      -0.186 |         -0.189 | 1.69296e-05  |       0.035 |
| convenience_count | 528 |       0.153 |          0.166 | 0.000435624  |       0.023 |


## ANOVA across gap_label groups

| predictor             |     F |     p_value |
|:----------------------|------:|------------:|
| nearest_healthy_miles | 23.33 | 9.00989e-18 |
| obesity_rate          | 22.36 | 4.62734e-17 |
| poverty_rate          | 21.34 | 2.52911e-16 |
| food_insecurity_rate  | 21.09 | 3.8609e-16  |
| diabetes_rate         | 19.48 | 5.94137e-15 |
| convenience_count     | 18.86 | 1.67513e-14 |
| median_income         | 17.8  | 5.28756e-11 |
| snap_rate             | 14.64 | 2.43368e-11 |
| supermarket_count     | 12.32 | 1.39647e-09 |
| pct_no_vehicle        | 11.59 | 5.04375e-09 |
| unemployment_rate     |  7    | 1.69858e-05 |
| fastfood_count        |  5.77 | 0.000150978 |
| grocery_count         |  4.15 | 0.00254085  |
| farmers_market_count  |  1.19 | 0.31613     |


## LILA vs non-LILA tract means

| predictor             |   lila_mean |   non_lila_mean |      diff |   cohen_d |      t |     p_value |   n_lila |   n_non_lila |
|:----------------------|------------:|----------------:|----------:|----------:|-------:|------------:|---------:|-------------:|
| obesity_rate          |       38.12 |           29.01 |      9.11 |     1.548 |  14.03 | 2.13477e-25 |       57 |          471 |
| nearest_healthy_miles |        1.68 |            0.77 |      0.91 |     1.475 |  10.31 | 1.40872e-15 |       57 |          473 |
| diabetes_rate         |       16.62 |           11.09 |      5.53 |     1.349 |  11.51 | 2.23327e-19 |       57 |          471 |
| median_income         |    50233.4  |       100121    | -49887.2  |    -1.295 | -16.93 | 6.15513e-48 |       55 |          464 |
| food_insecurity_rate  |       29.61 |           17.27 |     12.34 |     1.14  |   9.36 | 1.04471e-14 |       57 |          471 |
| snap_rate             |       23.29 |           11.59 |     11.71 |     0.958 |   7.54 | 7.28215e-11 |       56 |          470 |
| grocery_count         |        0.02 |            0.6  |     -0.58 |    -0.674 |  -9.95 | 1.70793e-21 |       57 |          473 |
| poverty_rate          |       19.91 |           13.03 |      6.88 |     0.614 |   4.76 | 8.67467e-06 |       57 |          471 |
| unemployment_rate     |        9.29 |            5.68 |      3.61 |     0.604 |   4.31 | 5.35366e-05 |       56 |          471 |
| supermarket_count     |        0.05 |            0.24 |     -0.19 |    -0.464 |  -4.18 | 6.27205e-05 |       57 |          473 |
| convenience_count     |        0.89 |            0.55 |      0.35 |     0.311 |   2.01 | 0.0488557   |       57 |          473 |
| fastfood_count        |        0.63 |            1    |     -0.37 |    -0.213 |  -2    | 0.0481739   |       57 |          473 |
| pct_no_vehicle        |        7.02 |            5.98 |      1.04 |     0.13  |   0.99 | 0.323169    |       56 |          470 |
| farmers_market_count  |        0.05 |            0.04 |      0.01 |     0.059 |   0.4  | 0.690641    |       57 |          473 |


## OLS — Food Access Gap regression
```json
{
  "n": 519,
  "r_squared": 0.309,
  "adj_r_squared": 0.302,
  "coefficients": {
    "(intercept)": 26.46,
    "fastfood_count": 1.437,
    "convenience_count": 4.433,
    "supermarket_count": -9.68,
    "pct_no_vehicle": 0.192,
    "median_income": -0.0
  }
}
```


## OLS — Food Insecurity regression
```json
{
  "n": 519,
  "r_squared": 0.614,
  "adj_r_squared": 0.609,
  "coefficients": {
    "(intercept)": 28.008,
    "food_access_gap": 0.085,
    "fastfood_count": -0.858,
    "convenience_count": -0.125,
    "supermarket_count": -0.801,
    "median_income": -0.0,
    "pct_no_vehicle": 0.362
  }
}
```

# Feature Experiment Report: `histgbdt_school_supplies_aug_promo_v1`

## Experiment Goal / 实验目标

验证针对 `SCHOOL AND OFFICE SUPPLIES` 的窄特征，是否能缓解 fold 3 underprediction，同时不明显伤害整体 validation。

This experiment follows the fold 3 cross-error and family focus analysis. It is intentionally narrow: only features are changed; the model stays the same.

注意：这些特征是在 fold 3 error analysis 之后设计的，所以 fold 3 改善只能说明这是一个 candidate，不等于已经证明能泛化到 Kaggle test period。

## Setup

| Item | Value |
| --- | --- |
| Experiment name | `histgbdt_school_supplies_aug_promo_v1` |
| Baseline comparison | `histgbdt_baseline` |
| Model | `hist_gbdt` |
| Feature profile | `school_supplies_aug_promo` |
| Validation scheme | 3 non-overlapping time windows, 16 days each |
| Submission generated | No |

New feature groups / 新增特征组：

- `is_school_supplies`
- `school_supplies_august`
- `school_supplies_onpromotion` and `school_supplies_onpromotion_log1p`
- `school_supplies_promo_6_plus` and `school_supplies_promo_11_50`
- `school_supplies_type_a` and `school_supplies_quito_ambato`
- interaction flags for August, high promotion, type A, and Quito/Ambato

Leakage boundary / 防泄漏边界：这些特征只使用 `date`、`family`、`onpromotion`、`store_type`、`city`，这些字段在 validation/test 预测时已知；不使用 validation/test 真实 `sales`。

## Validation Result / 验证结果

| fold_id | validation_rmsle_baseline | validation_rmsle_experiment | rmsle_delta |
| --- | --- | --- | --- |
| 1 | 0.381085 | 0.381600 | 0.000515 |
| 2 | 0.400716 | 0.400273 | -0.000443 |
| 3 | 0.423002 | 0.412684 | -0.010318 |
| mean | 0.401601 | 0.398186 | -0.003415 |

Lower RMSLE is better / RMSLE 越低越好。

- Mean RMSLE delta: `-0.003415`.
- Fold 3 target family RMSLE delta: `-0.178289`.
- Top fold 3 target segment: store `47` + promotion bin `11-50`, baseline predicted mean `33.6`, experiment predicted mean `96.8`, actual mean `538.4`.

## Target Family Fold Check / 目标 family 检查

| fold_id | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales | mean_predicted_sales_delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.434057 | 0.429204 | -0.004852 | 1.366898 | 1.274311 | 1.196978 | -0.077333 |
| 2 | 0.641590 | 0.629124 | -0.012466 | 7.063657 | 1.332382 | 1.362582 | 0.030201 |
| 3 | 0.866511 | 0.688222 | -0.178289 | 59.947917 | 18.501496 | 31.679055 | 13.177559 |

## Fold 3 Store-Promotion Check / 目标片段检查

| store_nbr | city | store_type | promotion_bin | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales | mean_predicted_sales_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 47 | Quito | A | 11-50 | 15 | 2.733045 | 1.876279 | -0.856766 | 538.400000 | 33.601619 | 96.849535 | 63.247916 |
| 44 | Quito | A | 11-50 | 15 | 2.697563 | 1.861933 | -0.835630 | 414.200000 | 26.982084 | 75.369535 | 48.387451 |
| 48 | Quito | A | 11-50 | 13 | 2.561915 | 1.723732 | -0.838183 | 464.846154 | 35.381392 | 93.635676 | 58.254285 |
| 50 | Ambato | A | 11-50 | 15 | 2.254764 | 1.517608 | -0.737156 | 416.000000 | 48.574898 | 135.249617 | 86.674719 |
| 9 | Quito | B | 6-10 | 15 | 1.501075 | 1.005018 | -0.496056 | 145.200000 | 31.893541 | 54.931831 | 23.038290 |
| 38 | Loja | D | 0 | 16 | 1.244050 | 1.241773 | -0.002277 | 4.937500 | 0.208907 | 0.213574 | 0.004667 |
| 20 | Quito | B | 6-10 | 9 | 1.243681 | 1.020937 | -0.222745 | 84.333333 | 23.288004 | 29.453717 | 6.165712 |
| 45 | Quito | A | 11-50 | 16 | 0.896901 | 0.424692 | -0.472210 | 526.375000 | 225.783110 | 410.551070 | 184.767960 |
| 51 | Guayaquil | A | 0 | 16 | 0.847989 | 1.017846 | 0.169858 | 3.875000 | 4.396971 | 5.515646 | 1.118675 |
| 8 | Quito | D | 0 | 16 | 0.733580 | 0.725549 | -0.008031 | 1.562500 | 0.403717 | 0.455907 | 0.052190 |

## Decision

Keep this feature profile as a candidate, but do not replace the default baseline yet.

保留为 candidate profile，但暂时不替换默认 baseline。

Reason:

- Mean RMSLE improves versus baseline.
- Fold 3 improves versus baseline.
- `SCHOOL AND OFFICE SUPPLIES` fold 3 improves versus baseline.
- The original underprediction in high-promotion store segments is reduced.
- 风险：该实验是根据 fold 3 问题反推设计的，存在 validation selection bias，需要 public score 或更多未参与设计的窗口验证。

Next action: generate a submission with this profile and compare Kaggle public score against the current baseline public score `0.58410`.

## Generated Tables

- `tables/validation_comparison.csv`
- `tables/target_family_fold_comparison.csv`
- `tables/target_fold_store_promotion_comparison.csv`

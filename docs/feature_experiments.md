# Store Sales 阶段 5：特征实验记录

## 阶段目标

阶段 5 的目标是用实验验证特征是否真的有用，而不是凭直觉保留特征。

每个实验都必须回答：

- 为什么做这个实验？
- 改了什么？
- 本地验证是否变好？
- fold 3 是否变好？
- 目标误差分组是否变好？
- 最后保留、修改，还是删除？

## 当前 Baseline

| 指标 | 数值 |
| --- | ---: |
| Model | `hist_gbdt` |
| Feature profile | `baseline` |
| Mean RMSLE | 0.401601 |
| Fold 1 RMSLE | 0.381085 |
| Fold 2 RMSLE | 0.400716 |
| Fold 3 RMSLE | 0.423002 |

## 实验 1：Low Demand Features v1

### 实验假设

阶段 4 发现部分高误差 family 具有低销量或高零销量特征。因此假设：如果加入 family 和 store-family 的历史低需求统计，模型可能更好识别低需求样本，从而降低相关 family 的 RMSLE。

### 改动内容

新增 `low_demand` feature profile，在 baseline 特征基础上加入：

- `family_mean_sales_hist`
- `family_zero_rate_hist`
- `family_row_count_hist`
- `family_is_low_demand`
- `store_family_mean_sales_hist`
- `store_family_zero_rate_hist`
- `store_family_row_count_hist`
- `store_family_is_low_demand`

防泄漏原则：

- 训练行只使用当前日期之前的历史统计。
- 验证和测试只使用当前训练窗口截止前的历史统计。
- 不使用验证期或测试期真实 `sales` 计算这些特征。

### 验证结果

| 指标 | Baseline | Low demand v1 | Delta |
| --- | ---: | ---: | ---: |
| Mean RMSLE | 0.401601 | 0.403019 | +0.001417 |
| Fold 1 RMSLE | 0.381085 | 0.379982 | -0.001103 |
| Fold 2 RMSLE | 0.400716 | 0.402185 | +0.001469 |
| Fold 3 RMSLE | 0.423002 | 0.426889 | +0.003886 |

### 误差分析

关键 family 对比：

| Family | Baseline RMSLE | Low demand RMSLE | Delta |
| --- | ---: | ---: | ---: |
| SCHOOL AND OFFICE SUPPLIES | 0.671040 | 0.712021 | +0.040981 |
| LINGERIE | 0.624578 | 0.621184 | -0.003393 |
| GROCERY II | 0.621563 | 0.615957 | -0.005606 |
| CELEBRATION | 0.565454 | 0.561999 | -0.003455 |
| HARDWARE | 0.529902 | 0.530040 | +0.000137 |

### 判断

这个实验不能保留为默认方案。

原因：

- 平均 RMSLE 比 baseline 更差。
- fold 3 比 baseline 更差，而 fold 3 最接近 Kaggle test period。
- `SCHOOL AND OFFICE SUPPLIES` 明显恶化，说明低需求特征把这个品类进一步压低了。
- 实验假设只被部分支持：部分 family 小幅改善，但最关键问题没有改善。

### 下一步

不要继续在同一方向上盲目加更多低需求特征。更合理的下一步是：

1. 做 fold 3 的交叉误差分析，确认 fold 3 变差来自哪些 family/store/promotion 组合。
2. 单独检查 `SCHOOL AND OFFICE SUPPLIES` 的时间规律，判断它是不是季节性或开学相关问题。
3. 如果继续做特征，应该做更窄的特征，而不是 broad low-demand profile。

## Fold 3 交叉误差分析

### 分析目标

low demand 实验失败后，下一步不是继续加特征，而是先确认 baseline 的 fold 3 变差到底集中在哪些组合上。

本次分析比较：

- fold 3
- fold 1/2 合并后的 prior folds

排序指标使用 `positive_msle_delta_contribution`，也就是某个分组在 fold 3 相比 prior folds 的 squared log error 增量贡献。这样比只看 fold 3 RMSLE 更接近“谁导致 fold 3 变差”。

### 核心结论

| 维度 | 最大变差来源 |
| --- | --- |
| family | `SCHOOL AND OFFICE SUPPLIES` |
| store | store `47`，Quito，type A |
| promotion bin | `11-50` |
| family-store | `SCHOOL AND OFFICE SUPPLIES` at store `47` |
| fold 3 新组合 | `SCHOOL AND OFFICE SUPPLIES` at stores `47/44/48/50` with promotion bin `11-50` |

### 关键数值

| 指标 | 数值 |
| --- | ---: |
| Prior folds RMSLE | 0.391024 |
| Fold 3 RMSLE | 0.423002 |
| Fold 3 delta | +0.031979 |
| `SCHOOL AND OFFICE SUPPLIES` fold 3 RMSLE | 0.866511 |
| `SCHOOL AND OFFICE SUPPLIES` prior RMSLE | 0.547742 |
| store `47` fold 3 RMSLE | 0.580428 |
| store `47` prior RMSLE | 0.325134 |
| promotion bin `11-50` fold 3 RMSLE | 0.418344 |
| promotion bin `11-50` prior RMSLE | 0.232653 |

### 解释

fold 3 变差不是平均分布在所有样本上，而是明显集中在：

- `SCHOOL AND OFFICE SUPPLIES`
- 高促销 bin `11-50`
- Quito / Ambato 的相关门店，尤其 type A 门店
- fold 3 新出现或 prior folds 很少出现的 `SCHOOL AND OFFICE SUPPLIES + 高促销 + type A/Quito-Ambato 门店` 组合

最强线索是：`SCHOOL AND OFFICE SUPPLIES` 在 fold 3 的实际销量明显高于模型预测。例如 store `47` 的该 family 在 fold 3 平均真实销量约 `538.4`，但平均预测只有约 `33.6`。这说明模型在该子集上明显低估；是否属于季节性突增，需要下一步单独检查时间规律。

### 当前判断

下一步不应该继续做 broad low-demand 特征，因为这个方向会进一步压低 `SCHOOL AND OFFICE SUPPLIES`。

更合理的下一步是单独分析 `SCHOOL AND OFFICE SUPPLIES`：

- 它是否在 7 月底到 8 月中出现季节性上升？
- 是否和 8 月时间效应、节假日或促销计划相关？“开学季”只能作为后续待验证假设。
- 是否只在 type A / Quito / Ambato 门店爆发？
- 是否需要针对该 family 做特殊特征，而不是全局低需求特征？

对应报告：

- `reports/fold3_cross_error/fold3_cross_error_report.md`
- `reports/fold3_cross_error/tables/fold3_family_store_promotion_worsening.csv`
- `reports/fold3_cross_error/tables/fold3_new_family_store_promotion_segments.csv`

## 单独分析：SCHOOL AND OFFICE SUPPLIES

### 分析目标

fold 3 交叉误差分析已经把最大问题定位到 `SCHOOL AND OFFICE SUPPLIES`。本次单独分析不训练新模型，只回答一个问题：这个 family 的错误到底像不像“低需求问题”，还是更像“特定时间 + 高促销 + type A / Quito-Ambato 门店”的问题。

### 核心发现

| 观察 | 结果 |
| --- | --- |
| 2017 年 8 月总销量 | `50169` |
| 2017 年 7 月总销量 | `8797` |
| fold 3 mean actual sales | `59.947917` |
| fold 3 mean predicted sales | `18.501496` |
| fold 3 RMSLE | `0.866511` |
| 最强错误门店 | store `47`，Quito，type A |
| 最强新组合 | store `47` + promotion bin `11-50` |
| 该组合真实均值 / 预测均值 | `538.4` / `33.6` |

### 判断

这个问题不应该继续当作 broad low-demand 问题处理。

原因：

- 2017 年 8 月该 family 销量明显高于 7 月和历史同期低位。
- fold 3 的错误主要是低估，而不是把低销量样本预测太高。
- 高错误集中在 type A 门店、Quito/Ambato 相关门店和 `11-50` 促销 bin。
- test period 中这些 type A 门店仍有较高促销，因此这个问题会影响最终提交风险。

### 下一步实验方向

下一轮不要继续增强 `low_demand`。更合理的实验方向是窄特征：

1. `SCHOOL AND OFFICE SUPPLIES` 专属的 8 月时间特征；“开学季”只能作为待验证假设，不能直接当作已证明原因。
2. `SCHOOL AND OFFICE SUPPLIES` 专属的促销响应特征，例如 family-promotion interaction。
3. type A 门店或 Quito/Ambato 相关门店的 school-supplies 高促销交互特征。
4. 实验后必须比较 mean RMSLE、fold 3 RMSLE，以及该 family 的 fold 3 store-promotion 错误是否下降。

对应报告：

- `reports/family_focus/school_office_supplies/family_focus_report.md`
- `reports/family_focus/school_office_supplies/tables/family_fold3_new_store_promotion_segments.csv`
- `reports/family_focus/school_office_supplies/tables/test_promotion_risk_overlap.csv`

## 实验 2：School Supplies August/Promotion v1

### 实验假设

`SCHOOL AND OFFICE SUPPLIES` 在 fold 3 的主要问题不是低需求，而是模型没有学好该 family 在 8 月、high promotion、type A / Quito-Ambato store 片段的 uplift。

因此本实验只做窄特征，不换模型、不加入 broad low-demand features。

### 改动内容

新增 `school_supplies_aug_promo` feature profile，在 baseline 特征基础上加入：

- `is_school_supplies`
- `school_supplies_august`
- `school_supplies_onpromotion`
- `school_supplies_onpromotion_log1p`
- `school_supplies_promo_6_plus`
- `school_supplies_promo_11_50`
- `school_supplies_type_a`
- `school_supplies_quito_ambato`
- `school_supplies_type_a_high_promo`
- `school_supplies_quito_ambato_high_promo`
- `school_supplies_august_high_promo`
- `school_supplies_august_type_a`

防泄漏原则：

- 这些特征只使用 `date/month`、`family`、`onpromotion`、`store_type`、`city`。
- 这些信息在 validation/test 预测时已知。
- 不使用 validation/test 真实 `sales`。

验证偏差风险：

- 这组特征是在 fold 3 cross-error analysis 之后设计的，因此 fold 3 改善不能单独作为“已经泛化”的证据。
- 当前结论只能说它是一个 candidate profile。
- 提交前需要用 Kaggle public score，或额外未参与特征设计的 rolling windows，继续确认是否只是贴合本地 fold 3。

### 验证结果

| 指标 | Baseline | School supplies v1 | Delta |
| --- | ---: | ---: | ---: |
| Mean RMSLE | 0.401601 | 0.398186 | -0.003415 |
| Fold 1 RMSLE | 0.381085 | 0.381600 | +0.000515 |
| Fold 2 RMSLE | 0.400716 | 0.400273 | -0.000443 |
| Fold 3 RMSLE | 0.423002 | 0.412684 | -0.010318 |
| `SCHOOL AND OFFICE SUPPLIES` fold 3 RMSLE | 0.866511 | 0.688222 | -0.178289 |

### Target segment 检查

| Segment | Baseline predicted mean | Experiment predicted mean | Actual mean | RMSLE delta |
| --- | ---: | ---: | ---: | ---: |
| store `47` + promotion bin `11-50` | 33.6 | 96.8 | 538.4 | -0.856766 |
| store `44` + promotion bin `11-50` | 27.0 | 75.4 | 414.2 | -0.835630 |
| store `48` + promotion bin `11-50` | 35.4 | 93.6 | 464.8 | -0.838183 |
| store `50` + promotion bin `11-50` | 48.6 | 135.2 | 416.0 | -0.737156 |

### 判断

提交前判断：保留为 candidate profile，但暂时不替换默认 baseline。

原因：

- mean RMSLE 比 baseline 更好。
- fold 3 明显改善，且 fold 3 最接近 Kaggle test period。
- `SCHOOL AND OFFICE SUPPLIES` fold 3 大幅改善。
- high-promotion store segments 的 underprediction 被缓解。
- 由于特征设计来自 fold 3 错误分析，存在 validation selection bias，不能只看 fold 3 改善就替换默认方案。

### Kaggle public score

| Submission | Local validation RMSLE | Kaggle public score | 对比 baseline public |
| --- | ---: | ---: | ---: |
| baseline | 0.401601 | 0.58410 | 0 |
| `school_supplies_aug_promo` | 0.398186 | 0.59096 | +0.00686 |

RMSLE 越低越好，因此这次 submission 比 baseline 更差。

最终判断：

- 不把 `school_supplies_aug_promo` 替换为 default baseline。
- 本地 mean RMSLE 和 fold 3 都变好，但 public score 变差，说明该特征很可能贴合了本地 fold 3，而没有泛化到 Kaggle public test。
- 这是 validation selection bias 的一个实际例子：根据 fold 3 error analysis 设计特征，再用 fold 3 改善证明自己，容易高估真实效果。

### 下一步

当前最佳提交仍是 baseline public score `0.58410`。

后续不继续沿 `school_supplies_aug_promo` 加强。更合理的下一步是：

- 改进验证方式，例如增加更多 rolling windows 或单独看非目标 family/fold 的副作用。
- 尝试更稳健的全局特征或模型对比，而不是继续为单个 fold 的异常片段加特征。
- 如果继续研究 `SCHOOL AND OFFICE SUPPLIES`，必须先找到能在非目标窗口也成立的证据。

对应报告：

- `reports/feature_experiments/school_supplies_aug_promo_v1/experiment_report.md`
- `reports/feature_experiments/school_supplies_aug_promo_v1/tables/validation_comparison.csv`
- `reports/feature_experiments/school_supplies_aug_promo_v1/tables/target_family_fold_comparison.csv`
- `reports/feature_experiments/school_supplies_aug_promo_v1/tables/target_fold_store_promotion_comparison.csv`

报告复现命令：

```bash
PYTHONPATH=src python3 -m store_sales.feature_experiment_report \
  --data-dir data/raw \
  --baseline-artifacts-dir artifacts/experiments/histgbdt_baseline \
  --experiment-artifacts-dir artifacts/experiments/histgbdt_school_supplies_aug_promo_v1 \
  --output-dir reports/feature_experiments/school_supplies_aug_promo_v1 \
  --baseline-name histgbdt_baseline \
  --experiment-name histgbdt_school_supplies_aug_promo_v1 \
  --feature-profile school_supplies_aug_promo \
  --baseline-public-score 0.58410 \
  --family "SCHOOL AND OFFICE SUPPLIES" \
  --target-fold 3 \
  --min-rows 4
```

## 验证体系实验：August / Pre-Test Windows

### 目的

`school_supplies_aug_promo` 的问题不是“本地没有变好”，而是“本地变好但 public 变差”。因此下一步先改进验证方式，检查历史 8 月窗口能不能筛掉这个失败实验。

本次新增显式 validation windows：

| Fold | Window | 含义 |
| --- | --- | --- |
| 1 | `2014-08-16` 到 `2014-08-31` | 历史 8 月下半月 |
| 2 | `2015-08-16` 到 `2015-08-31` | 历史 8 月下半月 |
| 3 | `2016-08-16` 到 `2016-08-31` | 历史 8 月下半月 |
| 4 | `2017-07-31` 到 `2017-08-15` | test 前最后 16 天；不是 8 月下半月，因为训练集没有 `2017-08-16` 之后真实 sales |

本次验证使用 `train_start_date=2013-01-01`，因为 2014 年窗口需要 2013 年历史数据做 lag/rolling 特征。

### 对比结果

| Run | Mean RMSLE | Worst fold RMSLE | Worst fold |
| --- | ---: | ---: | ---: |
| `histgbdt_baseline` | 0.490514 | 0.656282 | 3 |
| `histgbdt_school_supplies_aug_promo` | 0.486425 | 0.655352 | 3 |

按 August / pre-test windows 看，`school_supplies_aug_promo` 仍然比 baseline 略好：

- fold 1 delta：`-0.003885`
- fold 2 delta：`-0.004289`
- fold 3 delta：`-0.000930`
- fold 4 delta：`-0.007251`

### 判断

这个验证实验没有筛掉 `school_supplies_aug_promo`，但 Kaggle public score 已经证明它更差：

- baseline public score：`0.58410`
- `school_supplies_aug_promo` public score：`0.59096`

结论：

- 只增加历史 8 月窗口还不够。
- August windows 能检查季节位置，但不能完全模拟 Kaggle public test 的分布。
- 下一步不能只看 mean RMSLE，还要增加 public-like 稳定性检查，例如非目标 family 副作用、promotion 分布切片、store/family 分组漂移。

对应报告：

- `reports/validation/august_windows/validation_window_report.md`
- `reports/validation/august_windows/run_summary.csv`
- `reports/validation/august_windows/fold_comparison.csv`

## 稳定性切片检查：Non-Target / Promotion / Drift

### 目的

August windows 仍然认为 `school_supplies_aug_promo` 更好，但 public score 更差。因此继续拆解：

- 是否伤害了非目标 family？
- 哪些 promotion bin 变差？
- validation 和 test 的 family-promotion 分布是否不同？
- 被 test 放大的切片里，是否存在本地已经变差的 family？

### 结果

Target vs non-target：

| Group | Baseline RMSLE | Experiment RMSLE | Delta |
| --- | ---: | ---: | ---: |
| target family | 0.681330 | 0.599242 | -0.082087 |
| non-target families | 0.493954 | 0.493476 | -0.000478 |

表面上看，非目标 family 整体没有变差。但进一步拆开 family 后：

- 非目标 family 变差数量：`16`
- 非目标 family 改善数量：`16`
- 变差最大的非目标 family：`DELI`，RMSLE delta `+0.007368`
- 其他变差 family 包括 `MAGAZINES`、`CLEANING`、`BEVERAGES`、`PET SUPPLIES`、`BEAUTY`

Promotion bin：

- `0` promotion bin 变差：delta `+0.000372`
- 其他 promotion bin 大多改善，尤其 `11-50` 改善明显：delta `-0.044323`

Test distribution drift：

- test 中 `PERSONAL CARE + 11-50` 比 validation 占比更高，share delta `+0.014450`，且该切片 RMSLE 变差 `+0.003838`。
- test 中 `DAIRY + 11-50` 占比更高，share delta `+0.011162`，且该切片 RMSLE 变差 `+0.005029`。
- test 中 `BREAD/BAKERY + 11-50` 占比更高，share delta `+0.009961`，且该切片 RMSLE 变差 `+0.007607`。

### 判断

这给 public score 变差提供了更具体的解释：

- `school_supplies_aug_promo` 对目标 family 改善很大。
- 但它同时让一批非目标 family 变差。
- Kaggle test 的促销分布又放大了部分真实变差的 `family + promotion_bin` 切片。
- 所以 mean validation 变好，public 仍可能变差。

这说明后续判断 feature profile 不能只看 mean RMSLE，也不能只看 target family。必须加入：

- non-target family regression count
- promotion bin regression
- test-overweighted regression slices

对应报告：

- `reports/validation/august_windows/stability_slices/stability_slice_report.md`
- `reports/validation/august_windows/stability_slices/tables/overweighted_non_target_regressions.csv`
- `reports/validation/august_windows/stability_slices/tables/family_comparison.csv`
- `reports/validation/august_windows/stability_slices/tables/promotion_bin_comparison.csv`

## 全局模型 / 特征对比

### 目的

在确认 `school_supplies_aug_promo` 这种局部补丁不可取后，下一步检查更稳健的全局方案：

- `seasonal_naive`：时间序列下限参照
- `ridge_baseline`：线性模型参照
- `histgbdt_compact`：更少 lag/window，检查是否更稳
- `histgbdt_baseline`：当前最佳提交方案
- `histgbdt_extended`：更长 lag/window，检查全局长周期特征是否有效

LightGBM 本轮没有运行，因为当前环境没有安装 `lightgbm`。

### August / pre-test windows 结果

| Run | Mean RMSLE | Worst fold RMSLE | 判断 |
| --- | ---: | ---: | --- |
| `histgbdt_baseline` | 0.490514 | 0.656282 | 当前最稳 |
| `histgbdt_compact` | 0.492959 | 0.666164 | fold 1 好，但整体差 |
| `histgbdt_extended` | 0.500922 | 0.633934 | fold 1/3/4 好，但 fold 2 大幅变差 |
| `seasonal_naive` | 0.624068 | 0.821798 | 只作参照 |
| `ridge_baseline` | 2.892314 | 3.042849 | 不适合当前特征编码 |

### 判断

本轮没有发现比 baseline 更稳的全局模型或特征方案。

关键原因：

- `compact` 少特征后，fold 1 变好，但 2015/2016/pre-test fold 变差，说明不是更稳。
- `extended` 加长 lag/window 后，fold 2 明显变差，说明长周期特征并没有稳定收益。
- `ridge` 在 ordinal categorical encoding 下表现很差，不适合当前 pipeline。
- `seasonal_naive` 远弱于 tree baseline，但可以作为 blending 的下限参照。

下一步如果继续提高分数，应优先：

- 尝试 LightGBM，并用相同 stability checks 判断是否真的稳。
- 或尝试 baseline 与 seasonal/lag benchmark 的简单 blending，减少 tree model 在局部切片上的过激预测。

对应报告：

- `reports/validation/august_global_models/validation_window_report.md`
- `reports/validation/august_global_models/run_summary.csv`
- `reports/validation/august_global_models/fold_comparison.csv`

## Simple Blending 实验

### 目的

在全局模型对比后，尝试不改动特征、不重新训练的新方向：把两个 validation run 的 `sales_pred` 做加权平均。

LightGBM 本轮仍未运行，原因是当前环境没有安装 `lightgbm`。因此先做不依赖新包的 simple prediction blending。

本轮新增工具：

- `src/store_sales/blend_validation.py`

它不会训练模型，只读取已有 fold prediction files：

- `validation_predictions_fold_01.csv`
- `validation_predictions_fold_02.csv`
- `validation_predictions_fold_03.csv`
- `validation_predictions_fold_04.csv`

然后按权重生成 blended validation predictions、`validation_summary.csv` 和报告。

### Baseline + Seasonal Naive

结论：失败。

即使只加入 `1%` 的 `seasonal_naive`，结果也变差：

| Run | Mean RMSLE | Worst fold RMSLE | 判断 |
| --- | ---: | ---: | --- |
| `histgbdt_baseline` | 0.490514 | 0.656282 | 当前基准 |
| `blend_histgbdt_baseline_seasonal_naive_base_w990` | 0.495169 | 0.669048 | 变差 |
| `seasonal_naive` | 0.624068 | 0.821798 | 太弱 |

判断：

- `seasonal_naive` 和 baseline 的预测质量差距太大。
- 简单平均会把 baseline 拉向弱模型，不能作为提交候选。

### Baseline + Extended

结论：有局部信号，但暂不提交。

`histgbdt_extended` 单独看 mean RMSLE 更差，但它在 fold 1/3/4 比 baseline 好，只是 fold 2 大幅变差。因此尝试和 baseline blending。

最佳权重：

- `blend_histgbdt_baseline_histgbdt_extended_base_w550`
- 含义：`55% baseline + 45% extended`

结果：

| Run | Mean RMSLE | Worst fold RMSLE | 判断 |
| --- | ---: | ---: | --- |
| `histgbdt_baseline` | 0.490514 | 0.656282 | 当前 best submission 对应方案 |
| `histgbdt_extended` | 0.500922 | 0.633934 | mean 差，但 worst fold 更好 |
| `blend_histgbdt_baseline_histgbdt_extended_base_w550` | 0.486839 | 0.645720 | mean 和 worst fold 都改善 |

fold 级别：

- fold 1：改善 `-0.010417`
- fold 2：回退 `+0.009239`
- fold 3：改善 `-0.010562`
- fold 4：改善 `-0.002960`

### Stability Slice 判断

对最佳 blend `w550` 做 public-like stability checks：

- target family RMSLE：`0.681330 -> 0.681433`，略差。
- non-target families 整体 RMSLE：`0.493954 -> 0.489896`，整体改善。
- 但仍有 `7` 个非目标 family 变差。
- promotion bin 中 `2-5`、`1`、`51+`、`11-50`、`6-10` 都变差，只有 `0` bin 改善。
- test-overweighted non-target regression slices 仍有 `15` 个。

判断：

- 这个 blend 比单独 `extended` 更合理，也比 baseline 有更好的 mean/worst fold。
- 但它不是“稳定通过”的候选，因为 fold 2 回退、促销切片回退、test-overweighted 回退仍存在。
- 暂不生成 Kaggle submission。
- 如果后续要冒险提交，应明确记录它是一个带风险的 validation candidate，而不是新的默认 best model。

对应报告：

- `reports/validation/august_blending/blend_report.md`
- `reports/validation/august_blending_baseline_extended/blend_report.md`
- `reports/validation/august_blending_baseline_extended/stability_slices/stability_slice_report.md`

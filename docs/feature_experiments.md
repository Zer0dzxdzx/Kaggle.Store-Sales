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
- Quito / Ambato 的大店，尤其 type A 门店
- fold 3 新出现或 prior folds 很少出现的 `SCHOOL AND OFFICE SUPPLIES + 高促销 + 大店` 组合

最强线索是：`SCHOOL AND OFFICE SUPPLIES` 在 fold 3 的实际销量明显高于模型预测。例如 store `47` 的该 family 在 fold 3 平均真实销量约 `538.4`，但平均预测只有约 `33.6`。这说明模型在该子集上明显低估；是否属于季节性突增，需要下一步单独检查时间规律。

### 当前判断

下一步不应该继续做 broad low-demand 特征，因为这个方向会进一步压低 `SCHOOL AND OFFICE SUPPLIES`。

更合理的下一步是单独分析 `SCHOOL AND OFFICE SUPPLIES`：

- 它是否在 7 月底到 8 月中出现季节性上升？
- 是否和开学季、节假日或促销计划相关？
- 是否只在 type A / Quito / Ambato 门店爆发？
- 是否需要针对该 family 做特殊特征，而不是全局低需求特征？

对应报告：

- `reports/fold3_cross_error/fold3_cross_error_report.md`
- `reports/fold3_cross_error/tables/fold3_family_store_promotion_worsening.csv`
- `reports/fold3_cross_error/tables/fold3_new_family_store_promotion_segments.csv`

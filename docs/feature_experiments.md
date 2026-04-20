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


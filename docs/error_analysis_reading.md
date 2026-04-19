# Store Sales 误差分析阅读记录

## 阶段目标

阶段 4 的目标是定位 baseline 主要错在哪里，而不是直接调参。

本阶段只做四类分析：

- family error
- store error
- promotion bin error
- fold comparison

## 分析输入

使用现有多窗口验证预测：

- `artifacts/validation_predictions_fold_01.csv`
- `artifacts/validation_predictions_fold_02.csv`
- `artifacts/validation_predictions_fold_03.csv`
- `artifacts/validation_summary.csv`

这些文件来自本地验证，不使用 Kaggle public label。

说明：

- family error、store error、promotion bin error 是把多个 validation fold 合并后的汇总结果。
- fold comparison 只回答不同验证窗口的整体 RMSLE 趋势，不解释具体 segment 原因。
- 如果后面要判断 fold 3 为什么变差，需要另开 fold × family、fold × store 或 fold × promotion 的交叉分析。

## 输出文件

| 文件 | 作用 |
| --- | --- |
| `reports/error_analysis/error_analysis_report.md` | 阶段 4 主报告 |
| `reports/error_analysis/tables/family_error.csv` | 按 family 分组的误差 |
| `reports/error_analysis/tables/store_error.csv` | 按 store / city / state / type / cluster 分组的误差 |
| `reports/error_analysis/tables/promotion_bin_error.csv` | 按 onpromotion 分箱的误差 |
| `reports/error_analysis/tables/fold_comparison.csv` | 按 validation fold 对比的误差 |

## 为什么先做这四类

| 分析 | 对应阶段 3 假设 |
| --- | --- |
| family error | 验证高零销量 family 是否贡献主要误差 |
| store error | 检查门店、城市、类型、cluster 是否有系统性偏差 |
| promotion bin error | 检查高促销样本是否泛化更差 |
| fold comparison | 检查越靠近测试期的整体 fold 误差是否变差 |

## 你需要判断的问题

1. 最差 family 是否集中在高零销量、低销量品类？
2. 最差 store 是否集中在某些 city、state、store_type 或 cluster？
3. 高 `onpromotion` 分箱是否比低促销分箱误差更高？
4. fold 3 是否比 fold 1/2 整体变差？
5. 下一步应该增强零销量特征、促销特征、门店特征，还是继续做 fold 3 的交叉误差分析？

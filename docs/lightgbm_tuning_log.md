# LightGBM Tuning Log

## 目标

把当前 `LightGBM baseline` 从“能用的候选”推进到“经过系统比较的主模型”。

## 方法

- 固定 `baseline` 特征，不改特征组。
- 在同一组 August / pre-test 显式窗口上比较四个候选：
  - `lightgbm_baseline`
  - `lightgbm_shrinkage_es`
  - `lightgbm_regularized_es`
  - `lightgbm_conservative_es`
- 增加训练尾部 holdout early stopping。
- early stopping 只作为验证阶段的控件，不直接生成 submission。
- 关注 mean RMSLE、worst fold、target family、non-target family 和 test-like slice 副作用。

## 候选结果

| experiment | preset | mean RMSLE | std | worst fold | 结论 |
| --- | --- | ---: | ---: | ---: | --- |
| `lightgbm_baseline` | baseline | 0.486767 | 0.070236 | 0.400730 | 当前最优，保留 |
| `lightgbm_shrinkage_es` | shrinkage | 0.499285 | 0.124943 | 0.403487 | fold 1/2 改善，但 fold 3 大幅恶化 |
| `lightgbm_conservative_es` | conservative | 0.507772 | 0.120996 | 0.414622 | 整体不如 baseline |
| `lightgbm_regularized_es` | regularized | 0.519939 | 0.126331 | 0.406631 | 整体最差 |

## 关键观察

- `shrinkage_es` 不是稳定改进：fold 1/2 下降，但 fold 3 从 `0.583115` 恶化到 `0.710339`。
- stability slice 显示 `shrinkage_es` 让 `SCHOOL AND OFFICE SUPPLIES`、多个非目标 family 和若干 test-overweighted slice 一起变差。
- `regularized_es` 和 `conservative_es` 也没有压住 2016 fold 风险。
- 因此这轮的结论不是替换 baseline，而是把 LightGBM 的系统化调参边界跑清楚。

## 结论

当前主模型仍然是 `lightgbm_baseline`。

## 可复现性说明

本轮 compare 运行时实验日志记录为 `4e6271d+dirty`。dirty workspace 来自当时并行存在的 feature-ablation 侧线改动：

- `src/store_sales/cli.py`
- `src/store_sales/feature_ablation.py`
- `reports/feature_ablation/`

这些文件不属于本轮 LightGBM 参数 sweep；本轮主结论仍以 `reports/validation/lightgbm_tuning/` 下的固定 baseline 特征、固定 August / pre-test 窗口结果为准。

后续更值得做的方向是：

- 继续围绕 fold 3 / non-target family 做稳定性约束
- 再试更小范围的树结构约束，而不是继续扩大参数网格
- 保持验证协议不动，只改模型侧

## 相关产物

- [comparison report](../reports/validation/lightgbm_tuning/comparison_report.md)
- [window report](../reports/validation/lightgbm_tuning/window_report/validation_window_report.md)
- [shrinkage stability slice report](../reports/validation/lightgbm_tuning/shrinkage_vs_baseline_slices/stability_slice_report.md)

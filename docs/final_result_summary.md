# Store Sales 最终结果总结

更新日期：2026-05-08

## 这份文档的用途

这份文档是当前项目的唯一结果入口，用来回答：

- 当前最好的提交是哪一个？
- 它在本地验证和 Kaggle public leaderboard 上表现如何？
- 哪些实验失败了，为什么不保留？
- 当前结果还有哪些风险？
- 这些内容最终能怎么写进简历？

如果只想快速了解项目结果，优先看这份文档，而不是从 `project_log.md` 或多个 report 里逐条翻。

## 当前 Champion

| 项目 | 结论 |
| --- | --- |
| 当前 champion model | `lightgbm_baseline` |
| Feature profile | `baseline` |
| 主验证协议 | August / pre-test explicit windows |
| 本地 mean RMSLE | `0.486767` |
| 本地 worst fold RMSLE | `0.583115` |
| Kaggle public score | `0.50834` |
| Submission file | `artifacts/submissions/lightgbm_baseline_v1/submission.csv` |

当前选择 `lightgbm_baseline` 作为 best submission 的原因：

- 它的 Kaggle public score `0.50834` 明显优于原始 HistGBDT baseline 的 `0.58410`。
- 在当前主验证协议下，它的 mean RMSLE `0.486767` 低于 `histgbdt_baseline` 的 `0.490514`。
- 它把 worst fold 从 `0.656282` 降到 `0.583115`，对最差窗口有明显改善。
- 第一轮 LightGBM tuning 中，`shrinkage`、`regularized`、`conservative` 都没有超过 baseline。

## 主验证协议

当前正式验证协议不是随机切分，而是时间序列验证：

| Fold | Validation window | 含义 |
| ---: | --- | --- |
| 1 | `2014-08-16` 到 `2014-08-31` | 历史 8 月下半月 |
| 2 | `2015-08-16` 到 `2015-08-31` | 历史 8 月下半月 |
| 3 | `2016-08-16` 到 `2016-08-31` | 历史 8 月下半月 |
| 4 | `2017-07-31` 到 `2017-08-15` | 测试期前最后 16 天 |

核心设置：

- `train_start_date=2013-01-01`
- `validation_horizon=16`
- 递归预测
- 特征必须满足预测时点可获得性约束

这套协议的作用是模拟真实业务中的“用过去预测未来”，并降低随机切分带来的未来信息穿越风险。

## 关键结果对比

| 方案 | 本地验证口径 | Mean RMSLE | Worst fold | Kaggle public score | 决策 |
| --- | --- | ---: | ---: | ---: | --- |
| `histgbdt_baseline` | 早期三窗口 | `0.401601` | `0.423002` | `0.58410` | 首个真实 baseline |
| `school_supplies_aug_promo` | 早期三窗口 | `0.398186` | `0.412684` | `0.59096` | 不保留，本地好但 public 差 |
| `histgbdt_baseline` | August / pre-test | `0.490514` | `0.656282` | `0.58410` | 历史诊断参考 |
| `blend_histgbdt_baseline_histgbdt_extended_w550` | August / pre-test | `0.486839` | `0.645720` |  | 有信号但未提交 |
| `lightgbm_baseline` | August / pre-test | `0.486767` | `0.583115` | `0.50834` | 当前 champion |
| `lightgbm_shrinkage_es` | August / pre-test | `0.499285` | `0.710339` |  | 不替换 baseline |
| `lightgbm_conservative_es` | August / pre-test | `0.507772` | `0.711345` |  | 不替换 baseline |
| `lightgbm_regularized_es` | August / pre-test | `0.519939` | `0.717537` |  | 不替换 baseline |

重要解释：

- 早期三窗口验证和 August / pre-test 验证不是同一口径，不能直接比较 `0.401601` 和 `0.486767`。
- Kaggle public score 来自提交后的 public leaderboard 记录，当前保存在 `docs/experiment_log.csv` 和 `docs/project_log.md`。
- 没有 public score 的方案没有被提交，不能声称线上更好。

## 最有价值的失败案例

`school_supplies_aug_promo` 是当前项目中最值得讲的失败实验。

它在早期本地验证中表现更好：

- mean RMSLE：`0.401601 -> 0.398186`
- fold 3 RMSLE：`0.423002 -> 0.412684`
- `SCHOOL AND OFFICE SUPPLIES` fold 3 RMSLE：`0.866511 -> 0.688222`

但 Kaggle public score 变差：

- baseline public score：`0.58410`
- `school_supplies_aug_promo` public score：`0.59096`

最终判断：

- 不把它作为默认方案。
- 它说明“本地验证变好”不等于“线上泛化更好”。
- 后续 submission 决策必须同时看 non-target family、promotion bin 和 test-like distribution slices。

## 当前残余风险

`lightgbm_baseline` 是当前 champion，但不是无风险模型。

| 风险 | 当前证据 | 解释 |
| --- | --- | --- |
| fold 1/2 回退 | fold 1 delta `+0.048240`，fold 2 delta `+0.040950` | LightGBM 不是每个历史窗口都更稳 |
| 非目标 family 回退 | `13` 个 non-target family 变差 | overall 改善不代表所有 family 都改善 |
| `PRODUCE` 回退明显 | family-level RMSLE delta `+0.081250` | 需要继续做 family-level 稳定性检查 |
| test-overweighted regression slices | `8` 个 | 某些测试期权重更高的切片在本地已经变差 |
| gate 状态 | 更接近 `Review` 而不是无条件 `Promote` | 可以作为 best submission，但后续优化仍要谨慎 |

因此当前结论不是“LightGBM 已经完全解决问题”，而是：

> LightGBM baseline 是当前最好的已提交方案，但下一阶段要继续围绕 fold / family / promotion stability 做收口，而不是只追 public score。

## 特征消融结论

第一轮 feature ablation 使用 `lightgbm_baseline_fast300` 配置，因此它是方向性证据，不是最终特征删除判决。

| 特征组 | 消融信号 | 解释 |
| --- | --- | --- |
| `sales_rolling` | 移除后 mean delta `+0.061111` | fast300 消融下最强正向信号 |
| `promotion` | 移除后 mean delta `+0.042030` | fast300 消融下强正向信号，短期建议保留 |
| `calendar` | mean 变差但 worst fold 变好 | mixed 信号，不能直接删除 |
| `oil` | 移除后 mean delta `-0.000803` | 小幅 removal candidate，但收益太小，需要复验 |
| `sales_lags` | mean 变好但 worst fold 变差 | mixed 信号，适合重设计，不适合简单删除 |

当前最稳妥的特征结论：

- `sales_rolling` 和 `promotion` 在 fast300 消融下显示出强正向信号，短期建议保留。
- 不急着删除 `calendar`、`sales_lags` 或 `oil`。
- 后续如果要改默认特征，必须重新通过主验证协议和 submission gate。

## 可写进简历的结论

可以写：

- 构建了门店-品类粒度的零售销量预测 pipeline，覆盖多表整合、特征工程、时间序列验证、递归预测和 submission 生成。
- 使用 EDA 和分组误差分析定位 family、store、promotion 和 fold 维度的误差来源，并基于失败实验诊断线上线下分数不一致。
- 对比 HistGBDT、LightGBM、seasonal naive、ridge 和 blending 候选，将 Kaggle public RMSLE 从 `0.58410` 提升到 `0.50834`。
- 建立 validation protocol 和 submission gate，不只看平均 RMSLE，也关注 worst fold、non-target family regression 和 test-like slice 风险。

不要写：

- 不要说项目已经达到竞赛最优。
- 不要说模型已经完全稳定。
- 不要说所有特征都被最终证明有效。
- 不要把 `school_supplies_aug_promo` 写成成功实验。

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Public score 与实验记录 | `docs/experiment_log.csv` |
| 项目阶段性日志 | `docs/project_log.md` |
| 主验证协议 | `docs/validation_protocol.md` |
| Submission gate | `docs/submission_gate.md` |
| LightGBM 主验证结果 | `reports/validation/august_lightgbm/run_summary.csv` |
| LightGBM stability slice | `reports/validation/august_lightgbm/stability_slices/stability_slice_report.md` |
| LightGBM tuning 对比 | `reports/validation/lightgbm_tuning/comparison_report.md` |
| Feature ablation | `reports/feature_ablation/lightgbm_baseline_fast300/ablation_report.md` |

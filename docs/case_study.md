# Store Sales 项目案例复盘

更新日期：2026-05-09

## 1. 项目一句话

这是一个 Kaggle `Store Sales - Time Series Forecasting` 零售销量预测项目。任务是在 `date + store_nbr + family` 粒度上，预测 54 家门店、33 个商品家族在 `2017-08-16` 到 `2017-08-31` 的未来 16 天销量。

我没有把它当成一次性提交，而是按一个可复现的数据科学项目来做：先读题和读表，再做 EDA、baseline、误差分析、特征实验、验证协议修正、模型对比、submission gate，最后整理成可复盘和可面试讲述的项目。

当前最好结果：

| 项目 | 结果 |
| --- | --- |
| 当前 champion | `lightgbm_baseline` |
| Feature profile | `baseline` |
| 主验证协议 | August / pre-test explicit windows |
| 本地 mean RMSLE | `0.486767` |
| 本地 worst fold RMSLE | `0.583115` |
| Kaggle public score | `0.50834` |
| 原始 HistGBDT baseline public score | `0.58410` |

完整结果页见 `docs/final_result_summary.md`。

## 2. 业务问题和建模边界

这个比赛本质上是一个多时间序列预测问题，不是普通随机样本回归。

关键业务设定：

- 预测对象：未来日期的销量 `sales`。
- 预测粒度：每个 `date + store_nbr + family` 一行。
- 预测窗口：未来 16 天。
- 评价指标：RMSLE，越低越好。
- 合法未来信息：测试集中已知的 `date`、`store_nbr`、`family`、`onpromotion`，以及可按日期/门店范围对齐的节假日、油价、门店静态信息。
- 高风险泄漏信息：验证期或测试期真实 `sales`、未来真实 `transactions`、任何用未来目标计算出来的统计量。

因此，项目一开始就定了两个原则：

- 不使用随机切分，因为随机切分会让训练集看到更晚日期的信息。
- 验证和提交都使用递归预测，模拟真实业务里“预测第 2 天时没有第 1 天真实销量”的场景。

## 3. 数据理解

项目使用 Kaggle 提供的多张表：

| 表 | 作用 | 使用方式 |
| --- | --- | --- |
| `train.csv` | 历史销量，包含目标列 `sales` | 训练、验证、构造历史 lag / rolling 特征 |
| `test.csv` | 未来 16 天待预测样本，不包含 `sales` | 生成 submission |
| `stores.csv` | 门店 city/state/type/cluster | 静态表，可按 `store_nbr` merge |
| `oil.csv` | 日油价 | 按日期对齐并插值，作为外部变量 |
| `holidays_events.csv` | 节假日和事件 | 按 National / Regional / Local 范围构造特征 |
| `transactions.csv` | 历史门店交易量 | 只能做历史聚合，不能直接用于未来日期 |
| `sample_submission.csv` | Kaggle 提交格式 | 校验并生成 `id,sales` |

这里最重要的判断是：不是所有表都能“直接 merge”。例如 `stores.csv` 是门店静态信息，预测未来时也已知，所以可以直接按 `store_nbr` merge；但 `transactions.csv` 是真实发生后的交易量，未来测试期不可能提前知道，所以只能做历史星期/月均值这类聚合特征。

## 4. EDA 给出的建模假设

EDA 的作用不是“画图展示”，而是形成后续实验假设。

关键发现：

- 训练集约 `3,000,888` 行，测试集 `28,512` 行，对应 `54 stores * 33 families * 16 days`。
- 零销量行比例约 `31.30%`，说明零销量不是噪声，而是建模重点。
- 销售有明显日历结构，周末、月末、发薪日等特征值得保留。
- 促销和销量呈明显正相关，而且测试期 `onpromotion` 均值高于训练期。
- family 差异很大，高销量品类和低销量/高零销量品类的行为不同。
- 早期多窗口验证中，越靠近测试期 RMSLE 越高，提示存在时间漂移或分布变化风险。

这些发现引出的下一步判断是：不要先盲目调参，而是先做分组误差分析，看看模型到底错在哪些 family、store、promotion bin 和 fold 上。

## 5. Baseline 和第一轮误差诊断

早期 baseline 使用 `HistGradientBoostingRegressor`，特征包括：

- 日期和周期特征
- 门店静态信息
- 节假日和事件特征
- 油价特征
- 促销 lag / rolling 特征
- 销量 lag / rolling 特征
- 历史 transactions 聚合

早期三窗口验证中，`histgbdt_baseline` mean RMSLE 为 `0.401601`，Kaggle public score 为 `0.58410`。这个结果说明 pipeline 已经能跑通，但本地验证和线上 public 分数存在明显 gap。

误差分析按四个方向拆：

- `family error`
- `store error`
- `promotion bin error`
- `fold comparison`

主要结论：

- `SCHOOL AND OFFICE SUPPLIES` 是高误差 family，存在明显低估。
- fold 越靠近测试期，RMSLE 越高。
- 促销分箱并不是简单的“高促销一定误差最高”，无促销样本反而有较高 RMSLE。
- store 维度存在差异，但不能直接断言某个 city 或 type 一定有问题。

这一步的价值是把问题从“整体分数不好”具体化成“某些时间窗口、品类和促销组合不稳定”。

## 6. 一个重要失败实验

项目里最值得讲的失败实验是 `school_supplies_aug_promo`。

这个实验来自 fold 3 误差分析：`SCHOOL AND OFFICE SUPPLIES` 在 8 月、type A / Quito-Ambato 门店、高促销组合下被明显低估。因此我加入了针对该 family 的 8 月、促销和门店交互特征。

本地早期验证变好了：

| 指标 | baseline | targeted feature |
| --- | ---: | ---: |
| mean RMSLE | `0.401601` | `0.398186` |
| fold 3 RMSLE | `0.423002` | `0.412684` |
| `SCHOOL AND OFFICE SUPPLIES` fold 3 RMSLE | `0.866511` | `0.688222` |

但 Kaggle public score 变差：

| 方案 | Public score |
| --- | ---: |
| `histgbdt_baseline` | `0.58410` |
| `school_supplies_aug_promo` | `0.59096` |

这个失败实验带来的项目转折是：不能只看本地 mean RMSLE，也不能只因为目标切片改善就提交。一个特征可能改善某个 family，却伤害其他 family 或测试期权重更高的切片。

因此后续增加了：

- August / pre-test explicit validation windows
- non-target family regression checks
- promotion bin stability
- validation/test distribution drift checks
- submission gate

## 7. 验证协议升级

为了避免不同实验用不同验证口径导致结论漂移，项目后来固化了主验证协议。

当前正式协议：

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
- 特征必须满足预测时点可获得性

这套协议不是完美预测 leaderboard 的工具，而是项目内部的统一判断标准。它解决的是“后续实验必须在同一把尺子下比较”的问题。

## 8. 模型对比和当前最好方案

在统一验证协议下，项目比较了多个方向：

- seasonal naive
- ridge
- HistGBDT
- HistGBDT extended features
- simple blending
- LightGBM
- LightGBM tuning candidates

当前最好的已提交方案是 `lightgbm_baseline`。

| 方案 | 验证口径 | Mean RMSLE | Worst fold | Public score | 结论 |
| --- | --- | ---: | ---: | ---: | --- |
| `histgbdt_baseline` | August / pre-test | `0.490514` | `0.656282` | `0.58410` | 历史诊断参考 |
| `blend_histgbdt_baseline_histgbdt_extended_w550` | August / pre-test | `0.486839` | `0.645720` |  | 有信号但未提交 |
| `lightgbm_baseline` | August / pre-test | `0.486767` | `0.583115` | `0.50834` | 当前 champion |
| `lightgbm_shrinkage_es` | August / pre-test | `0.499285` | `0.710339` |  | 不替换 baseline |
| `lightgbm_conservative_es` | August / pre-test | `0.507772` | `0.711345` |  | 不替换 baseline |
| `lightgbm_regularized_es` | August / pre-test | `0.519939` | `0.717537` |  | 不替换 baseline |

LightGBM 的价值不只是 mean RMSLE 略好，更重要的是把 worst fold 从 `0.656282` 降到 `0.583115`。但它仍然不是无风险模型：fold 1/2 有回退，仍有 `13` 个 non-target family 变差，`PRODUCE` 的回退尤其明显。

所以当前判断是：

> `lightgbm_baseline` 是当前 best submission，但不是最终稳定解。它可以作为作品集里的当前 champion，同时要诚实说明 residual risk。

## 9. 特征消融给出的解释

第一轮 feature ablation 使用 `lightgbm_baseline_fast300`，所以它是方向性证据，不是最终删除判决。

主要信号：

| 特征组 | 消融信号 | 判断 |
| --- | --- | --- |
| `sales_rolling` | 移除后 mean delta `+0.061111` | fast300 消融下最强正向信号 |
| `promotion` | 移除后 mean delta `+0.042030` | 在 fast300 消融下显示强正向信号，短期建议保留 |
| `calendar` | mean 变差但 worst fold 变好 | mixed，不能直接删除 |
| `oil` | 移除后 mean delta `-0.000803` | 小幅 removal candidate，需要复验 |
| `sales_lags` | mean 变好但 worst fold 变差 | mixed，适合重设计 |

这说明在当前 fast300 消融设置下，历史销量滚动统计和促销信息显示出最强的正向信号。这也符合业务直觉：零售销量短期惯性强，促销是未来已知且影响销量的重要变量。后续如果要改变默认特征，仍需要回到主验证协议重新验证。

## 10. 工程化和可复现性

为了让项目不只是 notebook 结果，仓库做了几个工程化收口：

- `src/store_sales/` 下拆分为 `data.py`、`features.py`、`modeling.py`、`pipeline.py`、`cli.py` 等模块。
- `docs/reproducibility.md` 写清环境安装、数据放置、主验证命令和 submission 生成方式。
- `docs/final_result_summary.md` 作为唯一结果入口，避免分数散落在多个日志里。
- `docs/validation_protocol.md` 和 `docs/submission_gate.md` 固化验证和提交判断。
- `tests/` 下增加 11 个轻量 sanity checks，覆盖 validation windows、submission frame、lag safety 和 recursive forecast。

最近一次本地测试记录：

```text
11 passed
```

## 11. 当前结论和局限

当前可以得出的结论：

- 项目已经形成从多表读取、特征工程、时间序列验证、模型对比、误差诊断到 submission 的完整 workflow。
- LightGBM baseline 是当前 best submission，public score 从 `0.58410` 提升到 `0.50834`。
- `school_supplies_aug_promo` 是一个有价值的失败案例，说明局部特征改善不一定带来线上泛化。
- `sales_rolling` 和 `promotion` 在 fast300 消融下显示出最强正向信号，短期建议保留并继续复验。
- 统一验证协议和 stability checks 比单看一个本地分数更可靠。

当前不能夸大的地方：

- 不能说模型已经完全稳定。
- 不能说所有特征都被最终证明有效。
- 不能说当前结果达到竞赛最优。
- 不能把没有 public score 的方案说成线上更好。

当前局限：

- 还没有 private leaderboard 级别优化。
- submission gate 是基于有限历史案例校准的第一版规则。
- 测试还只是轻量 sanity checks，没有 CI 和完整端到端测试。
- LightGBM 仍存在 fold / family / promotion slice 的稳定性风险。

## 12. 对外项目摘要

这个项目可以概括为一个可复现的零售需求预测 workflow：

- 问题定义：预测 `date + store_nbr + family` 粒度下未来 16 天销量，评价指标为 RMSLE。
- 数据处理：整合销量、门店、促销、节假日、油价和历史交易量等多表信息，并区分预测时已知字段和高风险泄漏字段。
- 验证设计：使用时间序列窗口和递归预测模拟真实提交场景，不使用随机切分。
- 诊断方法：不仅看 mean RMSLE，还按 family、store、promotion bin、fold 和 test-like slices 拆解误差。
- 实验结论：`lightgbm_baseline` 是当前 best submission，Kaggle public score 从原始 HistGBDT baseline 的 `0.58410` 提升到 `0.50834`。
- 项目边界：当前结果适合作为可解释、可复现的数据科学项目，但仍存在 fold / family / promotion stability 风险，不应包装成竞赛最终最优解。

面试讲稿、岗位定制回答和更口语化的追问准备保存在本地私有材料中，不放入公开仓库。

## 13. 证据入口

| 你想看什么 | 文件 |
| --- | --- |
| 当前最终结果 | `docs/final_result_summary.md` |
| 怎么复现 | `docs/reproducibility.md` |
| 验证协议 | `docs/validation_protocol.md` |
| 提交判断规则 | `docs/submission_gate.md` |
| EDA 解读 | `docs/eda_interpretation.md` |
| 误差分析 | `docs/error_analysis_reading.md` |
| LightGBM tuning | `docs/lightgbm_tuning_log.md` |
| 项目学习进程 | `docs/project_progress_table.md` |
| 项目日志 | `docs/project_log.md` |

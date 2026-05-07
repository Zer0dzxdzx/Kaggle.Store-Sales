# Store Sales Validation Protocol

## 这份文档的用途

这份文档用于固化一个问题：

> 后续我们应该用什么验证口径判断一个实验是否真的更好？

这里的目标不是找到“唯一完美验证”，而是先统一项目内部的主判断标准，避免：

- 一次看三窗口 mean RMSLE
- 一次看 August / pre-test windows
- 一次又只看 Kaggle public score

如果验证口径不固定，后面的模型对比、特征消融和 submission 决策都会漂。

---

## 适用范围

这份 protocol 主要用于：

- 判断一个新实验是否优于当前参考方案
- 判断一个候选方案是否值得进入 submission gate
- 统一模型对比、特征实验和后续 LightGBM 调参的评估方式

这份 protocol 不用于：

- 替代 Kaggle leaderboard
- 证明某个实验一定会在 public / private leaderboard 上更好
- 阻止探索性小实验先做快速 smoke test

也就是说：

> 它是项目内部的主验证标准，不是对未来榜单的绝对预测器。

---

## 当前项目的关键经验

我们已经有 3 个非常重要的历史案例：

### 案例 1：`school_supplies_aug_promo`

- August / pre-test mean RMSLE：`0.486425`
- baseline August / pre-test mean RMSLE：`0.490514`
- 本地验证更好
- Kaggle public score：`0.59096`
- baseline public score：`0.58410`

结论：

> 历史 8 月窗口单独变好，不足以说明方案值得提交。

### 案例 2：`blend_histgbdt_baseline_histgbdt_extended_base_w550`

- mean RMSLE：`0.486839`
- baseline mean RMSLE：`0.490514`
- worst fold：`0.645720`
- baseline worst fold：`0.656282`
- 本地 mean 和 worst fold 都改善
- 但仍有较多 non-target regression slices 风险
- 最终未提交

结论：

> 只看 mean RMSLE 和 worst fold 仍然不够，必须结合 stability slices。

### 案例 3：`lightgbm_baseline`

- mean RMSLE：`0.486767`
- baseline mean RMSLE：`0.490514`
- worst fold：`0.583115`
- baseline worst fold：`0.656282`
- 仍存在 fold 1/2 回退与非目标切片风险
- Kaggle public score：`0.50834`

结论：

> 一个候选方案即使存在 residual risk，也可能在 public 上更好；因此 protocol 的作用是“统一判断 + 暴露风险”，不是机械替代提交。

---

## 当前主验证协议

从现在开始，项目的主验证协议固定为：

### 1. 数据边界

- `train_start_date=2013-01-01`
- `validation_horizon=16`
- 递归预测必须保留
- 特征必须满足预测时点可获得性约束

### 2. 主验证窗口

固定使用 4 个 explicit windows：

1. `2014-08-16:2014-08-31`
2. `2015-08-16:2015-08-31`
3. `2016-08-16:2016-08-31`
4. `2017-07-31:2017-08-15`

这个组合的含义是：

- 前 3 个窗口用于历史同期验证
- 最后 1 个窗口用于测试期前的 pre-test holdout

### 3. 主验证命令口径

所有正式候选方案都应该和当前参考方案使用同一组窗口、同一递归预测方式、同一训练起点。

允许做探索性小实验，但只要进入“是否值得提交”的讨论，就必须回到这组窗口。

---

## 当前参考方案

项目里保留两个不同用途的参考方案：

### 历史诊断参考

- `histgbdt_baseline`

作用：

- 保持和早期实验、误差分析、稳定性报告的可比性
- 用于解释项目为什么从 HistGBDT 走到 LightGBM

### 当前 submission 参考

- `lightgbm_baseline`

作用：

- 作为当前 best public submission 的主参考
- 后续所有新的提交候选，默认都先和它比较

当前参考数值：

| 方案 | mean RMSLE | worst fold | Kaggle public score |
| --- | ---: | ---: | ---: |
| `histgbdt_baseline` | 0.490514 | 0.656282 | 0.58410 |
| `lightgbm_baseline` | 0.486767 | 0.583115 | 0.50834 |

因此从现在开始的默认比较规则不是“只对一个参考”，而是分成两层：

1. 主性能比较：默认和 `lightgbm_baseline` 比  
2. 计数型稳定性阈值：当前仍锚定在 `histgbdt_baseline` 这组历史诊断控制上

原因很直接：

- 当前 `Promote / Review / Block` 的 count thresholds，是用历史 `histgbdt_baseline` 对照案例校准出来的
- 在还没有足够多的 `lightgbm_baseline` 相对案例之前，不能假装这些阈值已经自动迁移到新 baseline

所以当前阶段更准确的说法是：

> 诊断历史问题时继续用 `histgbdt_baseline`；判断一个新候选是否值得提交时，主性能默认和 `lightgbm_baseline` 比，但 count-based stability thresholds 仍使用冻结的 `histgbdt_baseline` 诊断控制口径。

---

## 冻结的诊断控制口径

为了让 count-based gate 可复现，当前项目把稳定性计数口径也冻结下来。

### 冻结参数

用于 count thresholds 的 stability slice 报告，当前固定为：

- baseline control：`histgbdt_baseline`
- validation windows：主协议的 4 个 explicit windows
- `target-family="SCHOOL AND OFFICE SUPPLIES"`
- `min-rows=30`

### 为什么要冻结

如果不冻结这组参数，同一个候选只要换一下：

- baseline control
- `target-family`
- `min-rows`

就可能让：

- `non-target families worsened`
- `promotion bin regressions`
- `overweighted non-target regressions`

这些计数发生变化，那 gate 就不再是正式规则，而只是“看起来很正式的经验总结”。

### 当前如何使用它

- count-based thresholds 只对这组冻结口径负责
- 如果未来要把这些阈值迁移到 `lightgbm_baseline` 相对口径，必须先积累足够多的新案例，再重新校准

### targeted experiment 的补充要求

如果一个实验本身是 targeted 的，例如：

- family-targeted
- promotion-targeted
- store-targeted

那么除了冻结的诊断控制口径外，还需要额外生成一份针对自身目标的专题 stability report。

这份专题报告的作用是：

- 判断它有没有真的改善自己的目标切片
- 作为 `Review` 或人工 override 的补充证据

但它不参与当前 count thresholds 的硬编码校准。

---

## 核心指标层级

### 一级指标：主判断指标

这些指标决定一个实验是否“看起来更好”。

1. `validation_rmsle_mean`
2. `validation_rmsle_max`（也就是 worst fold）

解释：

- `mean RMSLE` 代表整体平均表现
- `worst fold` 代表最差窗口表现，避免候选方案靠“均值改善”掩盖局部崩坏

### 二级指标：稳定性诊断指标

这些指标决定一个实验是否“更稳、更接近 test-like 场景”。

1. `non-target families worsened`
2. `promotion bin regressions`
3. `overweighted non-target regression slices`
4. 单个 fold 的 `rmsle_delta`
5. 关键 family 的极端 regression

解释：

- 这些指标不一定单独决定输赢
- 但它们决定一个候选是否应该进入 submission gate

### 三级指标：专题指标

这些指标只在特定实验方向下才是必须项。

例如：

- targeted family 实验必须看 target family 是否改善
- promotion-oriented 实验必须看 promotion bins 是否恶化
- store-specific 实验必须看重点门店组合是否改善

---

## 必备输出物

一个正式候选方案要进入提交讨论，最少要有下面这些输出：

### 验证运行产物

- `run_summary.csv`
- `validation_summary_long.csv`
- `validation_predictions_fold_*.csv`

### 对比产物

- 和当前参考方案在同协议下的均值 / fold 对比

### 稳定性产物

- 相对当前 submission 参考的主性能对比结果
- 冻结诊断控制口径下的 `stability_slice_report.md`
- `tables/overweighted_non_target_regressions.csv`
- `tables/family_comparison.csv`
- `tables/promotion_bin_comparison.csv`

如果是 targeted experiment，还必须补：

- 目标专题 stability report

没有这些产物的实验，默认只能算探索性实验，不能直接进入提交讨论。

---

## 当前项目的正式判断顺序

后续每个新实验都按同一顺序判断：

### 第一步：先看主协议下、相对 `lightgbm_baseline` 的 mean RMSLE

如果主协议下连均值都没有改善，就默认不进入提交候选。

### 第二步：再看相对 `lightgbm_baseline` 的 worst fold

如果 worst fold 明显恶化，说明候选方案可能通过均值掩盖了局部崩坏。

### 第三步：看冻结诊断控制口径下的 stability slices

重点看：

- non-target families worsened 数量
- weighted regression slices
- promotion bins 是否回退
- 是否出现 test-like 分布下更危险的切片

如果是 targeted experiment，再补看目标专题 stability report。

### 第四步：最后才考虑 submission

Kaggle public score 是最终补充证据，但不是进入提交候选的第一道门。

也就是说：

> 先过 protocol，再过 gate，再考虑提交。

---

## 明确不允许的比较方式

后续文档和实验结论里，下面几种比较默认不允许直接混用：

### 1. 不同验证协议的分数直接横比

比如：

- 三窗口 `0.401601`
- August / pre-test windows `0.486767`

这两个数值不能直接说谁更强，因为协议不同。

### 2. 只拿 public score 否定本地验证

public score 很重要，但样本窗口有限；它是补充证据，不是唯一标准。

### 3. 只看一个指标就做 promote / reject

任何只基于以下单指标做决定的行为都视为不合规：

- 只看 mean RMSLE
- 只看某一个 fold
- 只看某一个 target family
- 只看 public score

---

## 协议更新条件

这份 protocol 不应该频繁变化。

只有满足下面任一条件时，才考虑改主协议：

1. 已经拿到更可靠的 public / private leaderboard 证据，说明当前协议系统性误导
2. 当前协议无法区分大多数成功和失败实验
3. 新的业务/建模方向要求引入新的专题验证，但必须作为补充层，而不是随便替换主协议

如果要修改 protocol，必须同时更新：

- `docs/validation_protocol.md`
- `docs/submission_gate.md`
- `docs/project_log.md`

---

## 一句话版本

如果后面要快速复述当前 protocol，最短可以这么说：

> 从现在开始，正式实验统一使用 August / pre-test explicit windows 做主验证，先看 mean RMSLE 和 worst fold，再结合 stability slices 判断风险；只有通过协议和 gate 的候选，才进入提交讨论。

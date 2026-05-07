# Store Sales Submission Gate

## 这份文档的用途

这份文档用于回答另一个更具体的问题：

> 一个实验在什么情况下可以进入 Kaggle submission？

它不是为了替代人的判断，而是为了把“提交门槛”从模糊感觉变成统一规则。

---

## Gate 的设计原则

submission gate 的设计基于项目已经发生过的 3 类经验：

1. `school_supplies_aug_promo`  
本地均值改善，但 public score 更差，说明不能只看 mean RMSLE。

2. `baseline + extended blend`  
均值和 worst fold 都改善，但 weighted regression slices 太多，说明 stability risk 足以阻止提交。

3. `lightgbm_baseline`  
本地协议表现更好，但仍有明显 warning；说明 gate 不能只输出“绝对通过 / 绝对失败”，还要允许“带风险审查”。

因此，gate 不做二元判断，而是分成 3 档：

- `Promote`
- `Review`
- `Block`

---

## 三种结果

### Promote

可以进入提交候选。

含义：

- 主协议下表现更好
- 没有触发硬性阻断条件
- warning 数量有限

### Review

可以作为探索性候选讨论，但不能默认提交。

含义：

- 主协议下有改进
- 没有触发硬阻断
- 但仍存在多个明显风险点

这种状态适合：

- 人工复核
- 明确写清风险后再决定是否做一次探索性提交

### Block

不进入 submission。

含义：

- 已经有足够证据表明该实验不够稳
- 或者当前证据不足以支持提交

---

## 前置条件

如果下面任一条件不满足，直接 `Block`：

1. 没有使用 `validation_protocol.md` 中定义的主协议
2. 没有和当前 submission 参考方案做同协议比较
3. 没有生成 stability slice 报告
4. 没有保留关键验证输出物

也就是说：

> 没有完整证据链的实验，不进入提交讨论。

---

## Gate 里到底在比较什么

当前 gate 实际上同时使用两套参考：

### 1. 主性能参考

- `lightgbm_baseline`

用途：

- 比较 `mean RMSLE`
- 比较 `worst fold`

### 2. 冻结的诊断控制口径

- baseline control：`histgbdt_baseline`
- validation windows：主协议固定的 4 个 explicit windows
- `target-family="SCHOOL AND OFFICE SUPPLIES"`
- `min-rows=30`

用途：

- 计算 `non-target families worsened`
- 计算 `promotion bin regressions`
- 计算 `overweighted non-target regressions`

当前必须这样拆开的原因是：

- `lightgbm_baseline` 是当前 best public submission，所以新候选的主性能应该和它比
- 但 count thresholds 是基于 `histgbdt_baseline` 相对案例校准出来的，目前还没有足够多的 `lightgbm` 相对案例支持阈值迁移

所以当前 gate 的真实含义是：

> 主性能和当前 champion 比，count-based 风险和冻结的历史诊断控制口径比。

### targeted experiment 的补充说明

如果是 targeted experiment，还需要额外生成一份目标专题 stability report。

这份专题报告用于：

- 判断目标切片是否真的改善
- 支持人工复核

但它不参与当前 count thresholds 的校准。

---

## Gate 里的计数口径

为了让阈值可复现，下面这些计数都必须在冻结诊断控制口径下生成：

- `non-target families worsened`
- `promotion bin regressions`
- `overweighted non-target regressions`

当前不允许：

- 换 `baseline control`
- 换 validation windows
- 换 `target-family`
- 换 `min-rows`

之后再拿同一条阈值继续判断 `Promote / Review / Block`。

如果后续要改这些参数，就必须同时：

1. 更新 `validation_protocol.md`
2. 更新 `submission_gate.md`
3. 重新做历史案例校准

---

## 硬性阻断条件

满足任意一条，直接 `Block`。

### Block-1：主协议均值没有改善

- 条件：`validation_rmsle_mean_delta >= 0`

解释：

- 如果主协议下连均值都没有改善，就没有足够理由提交

### Block-2：worst fold 明显恶化

- 条件：`worst_fold_delta > +0.01`

解释：

- 允许轻微波动
- 但如果最差窗口明显更差，说明候选方案不稳

### Block-3：test-overweighted non-target regression slices 过多

- 条件：冻结诊断控制口径下，`overweighted_non_target_regressions > 12`

解释：

- 这是当前 gate 里最重要的阻断项之一
- 因为它直接对应“测试期权重更高的风险切片”

### Block-4：targeted 实验没有改善自己的目标切片

只对 targeted experiment 适用。

- 条件：目标专题 stability report 中，目标切片 `rmsle_delta >= 0`

解释：

- 如果一个 targeted 实验连它声称要解决的问题都没解决，就没有保留理由

---

## Warning 条件

warning 不会自动阻断，但会把状态推向 `Review`。

### Warning-1：non-target families worsened 较多

- 条件：冻结诊断控制口径下，`non_target_families_worsened > 10`

解释：

- 这通常意味着候选方案对泛化有副作用

### Warning-2：出现明显的单 family regression

- 条件：某个 non-target family `rmsle_delta > +0.05`

解释：

- 即使 overall 更好，也不能无视某个 family 的明显退化

### Warning-3：多个 promotion bins 回退

- 条件：冻结诊断控制口径下，回退的 promotion bins 数量 `>= 3`

解释：

- promotion 是这个比赛的核心驱动之一
- 多个 bin 同时回退，说明局部模式可能不稳

### Warning-4：单个 fold 出现明显正向回退

- 条件：任一 fold 的 `rmsle_delta > +0.03`

解释：

- 即使 mean 改善，也要警惕候选方案只是把问题从一个窗口挪到另一个窗口

## 人工 Override 条件

下面这些情况不计入 warning 数量，但会强制把候选从 `Promote` 提升为 `Review`，必要时直接改成 `Block`。

### Override-1：targeted 提升高度集中在单一切片

只对 targeted experiment 适用。

解释：

- 如果改善只集中在一个目标切片，但换来大量非目标副作用，说明泛化风险偏高

这个 override 需要结合人工解释，不做单个硬阈值。

---

## 最终判定规则

### Promote

满足：

- 所有前置条件通过
- 没有任何硬阻断
- 计数型 warning 数量 `<= 1`
- 且没有触发人工 override

### Review

满足：

- 所有前置条件通过
- 没有任何硬阻断
- 计数型 warning 数量 `>= 2`

或者：

- 没有硬阻断
- 但触发了人工 override

### Block

满足任意一条：

- 前置条件不完整
- 触发任一硬阻断

---

## 用历史案例校准 gate

下面这张表不是回顾历史对错，而是用已经发生过的案例校准这个 gate 是否有辨识力。

| 候选方案 | 校准参考口径 | mean delta | worst fold delta | non-target families worsened | overweighted non-target regressions | 预期状态 | 说明 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `histgbdt_school_supplies_aug_promo` | `histgbdt_baseline` 冻结诊断控制 | `-0.004089` | `-0.000930` | `16` | `21` | `Block` | 均值改善，但 weighted regressions 过多，后来 public 也更差 |
| `blend_histgbdt_baseline_histgbdt_extended_base_w550` | `histgbdt_baseline` 冻结诊断控制 | `-0.003675` | `-0.010562` | `7` | `15` | `Block` | mean / worst fold 改善，但 weighted regressions 过多，target slice 也没有改善 |
| `lightgbm_baseline` | `histgbdt_baseline` 冻结诊断控制 | `-0.003747` | `-0.073167` | `13` | `8` | `Review` | 这是历史上在 gate 正式固化前提交的强候选；按当前规则它更适合被定义为 `Review`，而不是无风险的自动 promote |

这里最重要的结论不是：

> gate 一定能提前预测 leaderboard

而是：

> gate 至少应该能稳定拦住明显高风险候选，并把带风险的强候选标成 `Review`，而不是直接放行。

---

## 当前项目的默认执行方式

从现在开始，一个新候选方案进入提交讨论时，默认流程是：

1. 跑主验证协议
2. 和当前 submission 参考方案 `lightgbm_baseline` 比较主性能
3. 用冻结诊断控制口径生成 stability slice 报告
4. 如果是 targeted experiment，再补目标专题 stability report
5. 按这份 gate 判定：
   - `Promote`
   - `Review`
   - `Block`
6. 只有 `Promote` 和少数充分说明风险的 `Review`，才考虑 submission

---

## Gate 输出模板

后续每次做提交决策，建议至少写出下面这几项：

### Candidate

- 实验名称：
- 比较参考：
- 特征方案：
- 模型方案：

### Primary Metrics

- mean RMSLE delta：
- worst fold delta：
- 主性能参考：

### Stability

- non-target families worsened：
- overweighted non-target regressions：
- promotion bin regressions：
- 最大 single-family regression：
- 冻结诊断控制口径是否一致：

### Gate Result

- 状态：`Promote / Review / Block`
- 原因：
- 是否提交：

---

## 当前版本的边界

这份 gate 不是最终定稿，它只是当前项目阶段的第一版正式规则。

后续如果出现下面情况，可以修订：

1. 多次 `Review` 候选在线上持续更好，说明 gate 过于保守
2. 多次 `Promote` 候选在线上持续更差，说明 gate 还不够严格
3. 已经积累足够多的 `lightgbm_baseline` 相对案例，可以重新校准 count thresholds
4. 新的验证协议已经替代当前主协议

但无论怎么修订，都必须保留一个原则：

> 以后不能再只因为 mean RMSLE 改善，就直接默认值得提交。

---

## 一句话版本

如果后面要快速复述当前 gate，最短可以这么说：

> 一个候选方案要先在主协议下优于当前参考，再通过 weighted regression slices、non-target side effects 和关键窗口稳定性的检查；如果风险太多就 `Block`，风险可控但仍明显存在就 `Review`，只有少量 warning 的候选才 `Promote`。

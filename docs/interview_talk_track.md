# Store Sales 面试讲述稿

更新日期：2026-05-10

## 这份文档的用途

这份文档专门服务面试现场，不是项目说明书。

目标是让你在被问到这个项目时，能做到三件事：

- 先用短版本讲清主线。
- 被追问时能解释关键判断。
- 不夸大结果，也不把项目讲成“我只是让 AI 写了代码”。

推荐阅读顺序：

1. 先看 `docs/case_study.md` 理解完整故事。
2. 再用本文练 30 秒、60 秒和追问回答。
3. 最后根据岗位要求选择偏数据分析、数据科学或机器学习的讲法。

## 面试讲述核心主线

这个项目最稳的主线是：

```text
业务问题
  -> 多表数据理解
  -> 时间序列验证和防泄漏
  -> EDA 和误差拆解
  -> 失败实验带来的验证升级
  -> 模型对比和当前结果
  -> 局限和下一步
```

不要按“我写了哪些文件”讲。面试官更关心你怎么判断问题、怎么验证结论、怎么解释结果。

## 15 秒版本

适合简历快速追问：“这个项目是做什么的？”

> 这是一个 Kaggle 零售销量预测项目，我预测门店-品类未来 16 天销量。我的重点不是单纯跑模型，而是完整做了多表清洗、EDA、时间序列验证、误差拆解和模型对比。最后用 LightGBM 把 public RMSLE 从 `0.58410` 提升到 `0.50834`，同时保留了验证协议和稳定性检查。

## 30 秒版本

适合面试刚开始让你介绍项目。

> 我做的是 Kaggle Store Sales 的连锁门店销量预测，粒度是 `date + store_nbr + family`，目标是预测未来 16 天销量。
> 我先梳理了销量、门店、促销、节假日、油价和交易量等多张表，明确哪些信息预测时已知，哪些会造成数据泄漏。
> 因为这是时间序列问题，我没有随机切分，而是用时间窗口验证和递归预测模拟真实提交场景。
> 后面我做了 EDA、分组误差分析和模型对比，最终 LightGBM 的 Kaggle public RMSLE 从原始 baseline 的 `0.58410` 提升到 `0.50834`。

## 60 秒版本

适合最常见的项目介绍。

> 我做过一个 Kaggle Store Sales 的门店销量预测项目。这个项目我没有只当成跑模型比赛，而是按完整的数据科学流程来做。
> 第一部分是多表数据理解和清洗。我把 `train/test`、`stores`、`oil`、`holidays_events` 和 `transactions` 的业务含义梳理清楚，区分哪些特征预测未来时已知，比如 `onpromotion`，哪些不能直接用，比如未来真实 `transactions`。
> 第二部分是 EDA 和误差分析。我看了销量周期、零销量比例、促销影响和门店差异，然后把误差按 family、store、promotion bin 和 fold 拆开看，避免只盯一个平均分。
> 第三部分是验证设计。因为这是时间序列预测，我没有随机切分，而是用过去窗口预测未来，并使用递归预测，防止 lag 特征偷看未来真实销量。
> 最后我对比了 HistGBDT、LightGBM、ridge、seasonal naive 和 blending。当前最好方案是 LightGBM baseline，public RMSLE 从 `0.58410` 提升到 `0.50834`。这个项目最大的收获是学会了如何做时序验证、防止数据泄漏，以及解释本地验证和线上分数不一致。

## 3 分钟版本

适合面试官说：“详细讲讲这个项目。”

> 这个项目是 Kaggle Store Sales 时间序列预测，目标是预测 2017 年 8 月下半月 54 家门店、33 个商品家族的未来 16 天销量。数据粒度是 `date + store_nbr + family`，评价指标是 RMSLE。
> 我第一步不是直接建模，而是先读题和读表。这个项目有多张表，包括历史销量、未来测试集、门店信息、油价、节假日、促销和交易量。我重点判断每张表在预测未来时是否可用。比如 `stores.csv` 是静态门店信息，可以直接 merge；`onpromotion` 在 test 里已经给出，所以是合法未来特征；但 `transactions.csv` 是真实发生后的交易量，测试期无法提前知道，所以只能做历史聚合，不能直接按未来日期 merge。
> 第二步是 EDA。我发现销量有明显日历周期，零销量比例约 `31.30%`，不同 family 差异很大，促销和销量强相关，而且测试期促销均值高于训练期。这些发现让我没有立刻盲目调参，而是先做误差拆解。
> 第三步是 baseline 和误差分析。我先跑了 HistGBDT baseline，public score 是 `0.58410`。然后我把误差按 family、store、promotion bin 和 fold 拆开，发现 late fold 更差，`SCHOOL AND OFFICE SUPPLIES` 等切片有明显问题。基于这个发现，我做过一个 targeted feature 实验，早期本地验证从 `0.401601` 改善到 `0.398186`，但 Kaggle public score 从 `0.58410` 变差到 `0.59096`。
> 这个失败实验是项目的转折点。它说明本地平均分变好，不代表线上泛化一定更好，也可能只是改善一个目标切片，同时伤害其他 family 或测试期权重更高的切片。所以我后面固定了 August / pre-test validation windows，并增加 stability slice 和 submission gate，不再只看 mean RMSLE。
> 最后我在统一验证协议下比较了 HistGBDT、LightGBM、ridge、seasonal naive 和 blending。LightGBM baseline 当前表现最好，August / pre-test mean RMSLE 是 `0.486767`，worst fold 是 `0.583115`，Kaggle public score 是 `0.50834`。不过我没有说它完全稳定，因为它还有 fold 1/2 回退和部分 non-target family regression。
> 所以这个项目最后交付的不只是一个分数，而是一套可复现的 workflow：有 README、final result summary、case study、reproducibility 文档、validation protocol、submission gate 和轻量 pytest sanity checks。

## 高频追问模板

### 1. 你怎么防止数据泄漏？

推荐回答：

> 我主要从两层防止泄漏。第一层是验证方式，不用随机切分，而是按时间窗口用过去预测未来。第二层是特征时点约束，比如 lag 和 rolling sales 都只使用预测日前的历史销量，`transactions` 不能直接使用验证期或测试期真实值，只能做历史聚合。测试和验证时也用递归预测，预测第 2 天时只能用第 1 天的预测值，而不是真实销量。

不要只说：

> 我严格按时间切分，所以没有泄漏。

这句话太泛。要补上 `transactions`、lag、rolling、recursive forecast 这些具体例子。

### 2. 为什么不能随机切分？

推荐回答：

> 因为这是预测未来销量的问题，样本有明确时间顺序。随机切分可能让训练集包含比验证集更晚的日期，相当于让模型提前看到未来分布，本地分数会虚高。真实业务场景是用历史数据预测未来，所以验证也要尽量模拟这个过程。

### 3. `train.csv` 和 `test.csv` 有什么区别？

推荐回答：

> `train.csv` 是历史数据，包含 `sales`，用于训练和本地验证；`test.csv` 是未来 16 天待预测数据，没有 `sales`，最终要生成这些行的销量预测。两者都包含 `date`、`store_nbr`、`family` 和 `onpromotion`，所以 `onpromotion` 是测试期已知的合法特征。

### 4. 为什么 `stores.csv` 可以 merge？

推荐回答：

> 因为 `stores.csv` 是门店静态信息，比如 city、state、type、cluster。它不会随预测日期泄漏未来销量，而且每个 `store_nbr` 对应一条门店属性，所以可以按 `store_nbr` 合并到训练集和测试集，让模型知道不同门店的结构差异。

### 5. 为什么 `transactions.csv` 风险更高？

推荐回答：

> `transactions` 是当天实际发生的交易次数，和销量高度相关。但测试期真实 transactions 不可能提前知道。如果在验证期直接按日期 merge 真实 transactions，就等于用了预测时不可获得的信息，本地分数会虚高。所以我只用训练窗口之前的 transactions 做历史星期均值、月份均值这类聚合。

### 6. 为什么要递归预测？

推荐回答：

> 因为模型用了 `sales_lag_1`、`sales_lag_7`、rolling sales 这类历史销量特征。预测第 1 天时可以用训练集最后一天的真实销量；但预测第 2 天时，第 1 天真实销量在真实提交场景里不可知，所以只能把第 1 天预测值写回历史，再继续预测第 2 天。这就是递归预测。

### 7. 你为什么用 RMSLE？

推荐回答：

> Kaggle 这个比赛的指标就是 RMSLE。它对相对误差更敏感，也适合非负销量预测。比如低销量品类预测偏一点，log 误差可能会比较明显，所以我在误差分析里不只看总销量大的品类，也会看低销量和高零销量 family。

### 8. EDA 里你最重要的发现是什么？

推荐回答：

> 我觉得最重要的是三点：第一，销量有明显日历周期，所以时间特征和时间验证很重要；第二，零销量比例约 `31.30%`，而且 family 差异很大，说明不能只看整体均值；第三，促销和销量相关，且测试期促销更强，所以要关注 promotion 分布变化和高促销切片的泛化。

### 9. 为什么本地分数变好，线上反而变差？

推荐回答：

> 我有一个 `school_supplies_aug_promo` 实验就是这样。它针对 `SCHOOL AND OFFICE SUPPLIES` 的 8 月和高促销场景加特征，早期本地验证从 `0.401601` 改善到 `0.398186`，但 public score 从 `0.58410` 变差到 `0.59096`。后面我分析认为，它改善了目标切片，但可能伤害了其他 family 或测试期权重更高的 promotion slice。这说明不能只看平均分，还要看切片稳定性。

### 10. 为什么最后选 LightGBM？

推荐回答：

> LightGBM 在当前主验证协议下表现最好，mean RMSLE 是 `0.486767`，worst fold 是 `0.583115`，并且 public score 从原始 HistGBDT baseline 的 `0.58410` 提升到 `0.50834`。但我不会说它已经完全稳定，因为 stability slice 里仍然有 fold 1/2 回退和部分 non-target family regression。

### 11. 你做了哪些特征？

推荐回答：

> 主要有几类：日期周期特征，比如 day of week、month、payday；门店静态特征，比如 city、state、type、cluster；节假日和事件特征，按 National、Regional、Local 区分；油价特征；促销当前值和历史 lag / rolling；销量 lag 和 rolling sales；还有 transactions 的历史聚合。所有历史类特征都要注意预测时点可获得性。

### 12. 这个项目还有什么不足？

推荐回答：

> 当前结果已经形成完整 workflow，但还不是进阶竞赛级方案。局限包括：LightGBM 仍有部分 fold 和 family 不稳定；submission gate 是基于有限历史案例校准的；测试目前是轻量 sanity checks，还没有 CI；模型层面还没做更高级的 ensemble 或 private leaderboard 级优化。所以下一步我会优先做稳定性优化和 CI，而不是盲目堆模型。

### 13. 如果继续优化，你会先做什么？

推荐回答：

> 我会优先做两个方向。第一是稳定性优化，围绕 fold 1/2 回退、`PRODUCE` 等 non-target family regression 做切片诊断。第二是工程可信度，比如加 CI，让 pytest 自动跑。建模上不会先大范围乱调参，而是根据 stability slice 决定是否重设计促销、lag 或 family-level 特征。

### 14. 这个项目最体现你能力的地方是什么？

推荐回答：

> 我觉得最体现能力的不是用了 LightGBM，而是验证和诊断。这个项目里我知道随机切分会有问题，也知道未来真实 transactions 和 sales lag 会造成泄漏；我还通过一个本地变好但 public 变差的实验，意识到要看切片稳定性，而不是只追平均分。这些更接近真实业务里的建模判断。

## 数据分析岗位版本

如果面试岗位更偏数据分析，不要把重点放在模型参数上。可以这样讲：

> 这个项目里我最核心的工作是把多张业务表转成可分析、可建模的数据，并用 EDA 和误差拆解解释销量预测问题。比如我会看不同 family 的零销量率、促销强度和销量关系、门店差异，以及模型在哪些 family/store/promotion 切片上误差更高。最终模型分数有提升，但更重要的是我能解释为什么某个实验本地变好却线上变差，并把这个经验转成后续验证规则。

强调能力：

- 多表理解和清洗
- 指标解释
- EDA 到假设
- 分组误差分析
- 业务解释和复盘

## 数据科学岗位版本

如果岗位更偏数据科学，可以这样讲：

> 我把这个项目当成一个时序预测实验系统来做。除了多表特征工程和模型对比，我重点设计了时间序列验证协议，避免随机切分和未来信息泄漏；同时用 recursive forecast 模拟真实多步预测。模型上对比了 HistGBDT、LightGBM、ridge、seasonal naive 和 blending，并且用 stability slice 检查 local validation 和 public score 的偏差。最终 LightGBM 是当前 champion，但我也保留了 residual risk 分析。

强调能力：

- 时间序列验证设计
- leakage control
- 特征工程
- 模型对比
- 泛化风险诊断

## 不能这样说

这些说法面试时要避免：

- “这个项目我主要是用 AI 生成代码。”
- “我用 LightGBM 解决了这个问题。”
- “这个模型已经很稳定。”
- “这些特征都被证明有效。”
- “我达到了比赛最优。”
- “本地验证好就说明线上一定好。”

更好的说法：

- “AI 帮我提速写重复代码和整理文档，但关键判断是我自己做的，比如验证方式、泄漏边界、特征是否保留、结果怎么解释。”
- “LightGBM 是当前 best submission，但仍有 fold 和切片稳定性风险。”
- “特征消融给出的是方向性证据，后续改默认特征仍要回到主验证协议复验。”

## 练习清单

面试前你至少要能脱稿回答这些问题：

1. 这个项目预测什么？
2. 为什么不能随机切分？
3. 哪些特征未来已知，哪些会泄漏？
4. `transactions.csv` 为什么不能直接 merge 到测试期？
5. 为什么要递归预测？
6. EDA 给了你哪 3 个建模假设？
7. `school_supplies_aug_promo` 为什么是失败实验？
8. 为什么最后选择 LightGBM？
9. 当前模型还有什么风险？
10. 如果继续做，你会先优化什么？

如果这 10 个问题能讲清楚，这个项目在数据分析 / 数据科学实习面试里就已经比较稳了。

# Store Sales 项目进程表

## 使用方式

这个表用于记录你自己主导的学习判断，而不是只记录代码改动。每进入一个新阶段，先写清楚：

- 这个阶段要理解什么
- 哪些判断必须自己做
- Codex 只是辅助做什么
- 最后能产出什么可复述的结论

## 总进程

| 阶段 | 日期 | 学习目标 | 你主导的判断 | Codex 辅助内容 | 产出 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 0. 读题 | 2026-04-16 | 搞清楚比赛预测目标、数据粒度、评价指标、验证方式和信息边界 | 判断它为什么是时间序列题，哪些字段未来可用，为什么不能随机切分，为什么需要递归预测 | 汇总题目、核对本地 CSV、解释关键概念 | 本表的“读题记录”和 5 个关键问题解释 | 完成 |
| 1. 读数据表 | 2026-04-16 | 理解每个 CSV 的业务含义和可用方式 | 判断每张表是目标、静态特征、未来已知特征，还是只能做历史聚合 | 帮忙生成表结构、缺失值、日期范围和样例行 | `docs/data_tables_reading.md` | 初读完成 |
| 2. 读 baseline | 2026-04-16 | 理解当前 pipeline 如何从原始数据生成 submission | 判断当前 baseline 是否合理、哪里可能泄漏、验证是否贴近比赛 | 解释代码路径和关键函数 | `docs/baseline_reading.md` | 初读完成 |
| 3. EDA 解读 | 2026-04-19 | 从图表形成建模假设 | 判断哪些发现值得转成特征或实验 | 汇总已有 EDA 图表和统计结果 | `docs/eda_interpretation.md` | 初读完成 |
| 4. 误差分析 | 2026-04-19 | 找出模型主要错在哪里 | 判断下一步优化方向，而不是盲目调参 | 生成 family/store/promotion/fold 分组误差报告并整理说明文档 | `docs/error_analysis_reading.md` 和 `reports/error_analysis/` | 初步完成 |
| 5. 特征实验 | 2026-04-20 | 用实验验证特征是否有用 | 决定特征保留、删除或继续修改 | 实现 feature profile、跑验证、记录实验日志 | `docs/feature_experiments.md` 和 `docs/experiment_log.csv` | 实验 2 已提交验证，不替换 baseline；August validation 已补充 |
| 6. 项目总结 | 待开始 | 把项目转成简历和面试可讲述内容 | 决定哪些结论真实、哪些不能夸大 | 整理 README 和总结初稿 | 简历项目描述与面试讲述稿 | 待开始 |

## 阶段 0：读题记录

### 题目一句话

这是一个门店-商品家族级别的多时间序列预测任务。目标是使用历史销量、促销、门店信息、油价、节假日和交易量等数据，预测 `2017-08-16` 到 `2017-08-31` 期间 54 家门店、33 个商品家族的未来销量。

### 本地数据核对

| 文件 | 行数 | 日期范围 | 作用 |
| --- | ---: | --- | --- |
| `train.csv` | 3,000,888 | 2013-01-01 到 2017-08-15 | 历史训练数据，包含目标列 `sales` |
| `test.csv` | 28,512 | 2017-08-16 到 2017-08-31 | 未来 16 天待预测数据，不包含 `sales` |
| `sample_submission.csv` | 28,512 | 无日期列 | Kaggle 提交格式，只需要 `id,sales` |
| `stores.csv` | 54 | 无日期列 | 门店静态信息 |
| `oil.csv` | 1,218 | 2013-01-01 到 2017-08-31 | 每日油价，属于外部变量 |
| `holidays_events.csv` | 350 | 2012-03-02 到 2017-12-26 | 节假日和事件信息 |
| `transactions.csv` | 83,488 | 2013-01-01 到 2017-08-15 | 历史门店交易量，只能做历史聚合 |

### 5 个关键问题

| 问题 | 当前正确解释 | 对项目的影响 |
| --- | --- | --- |
| 为什么这是时间序列问题？ | 因为目标是预测未来日期的销量，样本之间有明确时间顺序。过去销量、星期周期、节假日、促销和月末等因素会影响未来销量。它不是普通独立样本回归，而是多时间序列预测加表格特征建模。 | 验证和特征工程必须尊重时间顺序，不能把未来信息混进训练。 |
| 为什么不能随机切分训练集和验证集？ | 随机切分可能让训练集包含比验证集更晚的日期，相当于用未来预测过去，造成信息泄漏。真实比赛场景只能用 `2017-08-15` 之前的数据预测之后 16 天。 | 必须用按时间切分的 validation，当前项目使用多窗口时间验证。 |
| `onpromotion` 为什么可以用于测试期预测？ | 因为 `test.csv` 里已经公开给出了未来每一天、每个门店、每个 family 的 `onpromotion`。它是预测时已知的未来变量。 | 促销是合法且重要的特征，可以直接用于验证和提交预测。 |
| `transactions.csv` 为什么不能直接当作未来特征？ | 因为它只到训练集最后一天，测试期真实交易量未知。验证时如果直接使用验证日期的真实 transactions，就会泄漏未来客流信息。 | transactions 只能做历史聚合特征，例如门店历史均值、星期均值、月份均值。 |
| 为什么预测未来 16 天时要递归预测？ | 因为模型使用 `sales_lag_1`、`sales_lag_7` 等历史销量特征。预测第 1 天时可以用训练集最后一天的真实销量；预测第 2 天时，前一天真实销量未知，只能用第 1 天的预测值继续生成 lag。 | 验证和提交都必须模拟真实多步预测，否则本地分数会虚高。 |

### 当前你需要掌握的判断

| 判断点 | 你应该能说出的版本 |
| --- | --- |
| 预测粒度 | 每一行是 `date + store_nbr + family` 的销量预测。 |
| 预测区间 | 本地 `test.csv` 是 2017-08-16 到 2017-08-31，共 16 天。 |
| 评价指标 | RMSLE，适合非负销量预测，对低销量和零销量更敏感。 |
| 合法未来特征 | `date`、日历特征、`store_nbr`、`family`、门店静态信息、测试集中的 `onpromotion`、测试期可对齐的节假日和油价。 |
| 高风险泄漏特征 | 测试期或验证期真实 `sales`、真实 `transactions`、任何用未来目标聚合出来的统计量。 |

### 阶段 1 概念补充

阶段 1 的核心不是背字段，而是掌握两个概念：

| 概念 | 你应该能说出的版本 |
| --- | --- |
| merge | 按共同字段把其他表的信息补到 train/test 主表上，让模型能使用这些信息。例如按 `store_nbr` 把 `stores.csv` 的 `city/state/type/cluster` 合并到每一行销售样本。 |
| 数据泄漏 | 训练或验证时用了真实预测场景中不可能提前知道的信息。它会让本地验证分数虚高，导致实验结论不可信。 |
| transactions 风险 | `transactions` 是真实发生后的交易次数，和 sales 高度相关。未来当天真实 transactions 不可提前知道，所以不能直接按日期 merge，只能做历史聚合。 |
| onpromotion 分布差异 | 测试期 `onpromotion` 均值高于训练期，说明测试期促销更强。后续要检查模型在高促销样本上的误差。 |

## 下一步

阶段 1 初读已完成，详见 `docs/data_tables_reading.md`。你需要能逐张表判断：

- 这张表表达什么业务信息？
- 它在预测未来时是否已知？
- 它可以直接 merge，还是只能做历史统计？
- 它可能带来什么数据泄漏风险？

阶段 2 初读已完成，详见 `docs/baseline_reading.md`。你需要能解释：

- 数据从 `data.py` 读入后，如何进入 `features.py`
- `stores/oil/holidays/transactions` 分别在哪里 merge 或聚合
- 为什么 transactions 没有直接按未来日期 merge
- 为什么训练 lag 要用 `shift`
- 为什么预测 test 要用递归预测

阶段 3 初读已完成，详见 `docs/eda_interpretation.md`。你需要能解释：

- 哪 5 个 EDA 发现最重要
- 每个发现对应什么建模假设
- 哪些发现需要通过误差分析验证
- 为什么下一步应该先做分组误差分析，而不是直接盲目调参

阶段 3 你的当前判断：

- public score 偏高最可疑的线索是越靠近测试期的 fold RMSLE 越高，但这只是线索，需要 fold 3 分组误差分析确认。
- 高零销量 family 先做 family 级误差分析，不急着单独建模；如果确实贡献主要误差，再加零销量率、历史均值、低需求标记等特征。
- 促销特征值得检查，但应先按 `onpromotion` 分箱和 `family + promotion` 分组看误差。
- fold 3 变差优先怀疑时间漂移，但也可能和促销、节假日、family/store 分布变化有关。
- 下一步先做误差分析，不直接尝试 `extended` lag；先定位错误来源，再决定特征实验。

阶段 4 已开始，分析范围限定为：

- family error
- store error
- promotion bin error
- fold comparison

阶段 4 说明文档已补充，当前结论是：

- family 误差中，低销量和部分高零销量品类值得重点关注。
- store 误差存在差异，但还不能直接归因到某个 city、state、type 或 cluster。
- promotion bin 结果显示无促销样本 RMSLE 最高，不能简单认为高促销样本是当前最大问题。
- fold 3 整体更差，但原因还没有被定位。

下一步应在这些结论中选择一个明确方向进入阶段 5 特征实验。

阶段 5 实验 1 已完成：

- 实验方向：family/store-family low-demand history features。
- 结果：mean RMSLE 从 baseline `0.401601` 变为 `0.403019`，更差。
- fold 3 从 `0.423002` 变为 `0.426889`，更差。
- `SCHOOL AND OFFICE SUPPLIES` RMSLE 从 `0.671040` 变为 `0.712021`，明显恶化。
- 决策：不把 `low_demand` 作为默认特征方案，保留代码供后续参考。

阶段 5 fold 3 交叉误差分析已完成：

- fold 3 RMSLE `0.423002`，prior folds RMSLE `0.391024`。
- 最大 family 变差来源是 `SCHOOL AND OFFICE SUPPLIES`。
- 最大 store 变差来源是 store `47`，Quito，type A。
- 最大 promotion bin 变差来源是 `11-50`。
- fold 3 新出现的高误差组合集中在 `SCHOOL AND OFFICE SUPPLIES + 11-50 promotion + type A/Quito-Ambato 门店`。
- 下一步不应继续 broad low-demand 特征，应单独分析 `SCHOOL AND OFFICE SUPPLIES` 的时间/促销/门店规律。

阶段 5 `SCHOOL AND OFFICE SUPPLIES` 单独分析已完成：

- 2017 年 8 月该 family 总销量为 `50169`，明显高于 2017 年 7 月的 `8797`。
- fold 3 中该 family 的 mean actual sales 为 `59.947917`，mean predicted sales 为 `18.501496`，主要问题是低估。
- 最大错误集中在 type A 门店、Quito/Ambato 相关门店和 `11-50` 促销 bin，代表组合是 store `47` + `11-50`。
- 该组合 fold 3 平均真实销量约 `538.4`，平均预测约 `33.6`。
- test period 中 type A 门店仍存在高促销，因此这个问题和最终提交风险相关。
- 下一步特征实验应针对 school-supplies 的 8 月时间/促销/门店交互特征，而不是继续扩展 low-demand 特征；“开学季”只能作为待验证假设。

阶段 5 实验 2 已完成：

- 实验方向：`SCHOOL AND OFFICE SUPPLIES` targeted August / promotion / store interaction features。
- profile：`school_supplies_aug_promo`。
- mean RMSLE 从 baseline `0.401601` 降到 `0.398186`。
- fold 3 RMSLE 从 `0.423002` 降到 `0.412684`。
- `SCHOOL AND OFFICE SUPPLIES` fold 3 RMSLE 从 `0.866511` 降到 `0.688222`。
- store `47` + promotion bin `11-50` 的 predicted mean 从 `33.6` 提高到 `96.8`，actual mean 为 `538.4`，underprediction 有缓解但仍存在。
- Kaggle public score 为 `0.59096`，差于 baseline `0.58410`。
- 决策：不替换 default baseline；本地改善但 public 变差，说明该实验存在 validation selection bias，不继续沿 `school_supplies_aug_promo` 加强。

阶段 5 August / pre-test validation 已完成：

- 新增显式窗口验证能力：`--validation-window YYYY-MM-DD:YYYY-MM-DD`。
- 窗口包括 `2014/2015/2016-08-16~08-31` 和 `2017-07-31~08-15`。
- `histgbdt_baseline` mean RMSLE：`0.490514`。
- `histgbdt_school_supplies_aug_promo` mean RMSLE：`0.486425`。
- 结果：August windows 仍然认为 `school_supplies_aug_promo` 更好，但 Kaggle public score 更差。
- 决策：历史 8 月窗口只能补充验证，不能单独作为提交判断；下一步要增加非目标 family、promotion bin、store/family drift 等 public-like 稳定性检查。

阶段 5 public-like stability slice checks 已完成：

- target family RMSLE 改善：`0.681330 -> 0.599242`。
- non-target families 整体略改善：`0.493954 -> 0.493476`。
- 但有 `16` 个非目标 family 变差，包括 `DELI`、`MAGAZINES`、`CLEANING`、`BEVERAGES`。
- test 中部分真实变差的 family-promotion 切片占比更高，例如 `PERSONAL CARE + 11-50`、`DAIRY + 11-50`、`BREAD/BAKERY + 11-50`。
- 决策：后续实验保留规则要加入 non-target regression count、promotion bin regression、test-overweighted regression slices，不能只看 mean RMSLE。

# Store Sales EDA 解读记录

## 阅读目标

阶段 3 的目标不是重新画更多图，而是把已有 EDA 图表转成可以指导建模的判断：

- 图表观察到了什么
- 这个观察说明什么业务或数据规律
- 它对应什么建模假设
- 下一步应该如何验证

本阶段的关键要求：不要停留在“我看到了一个图”，而要形成“这个图让我决定做什么实验或误差分析”。

## 已有 EDA 产物

| 类型 | 路径 | 用途 |
| --- | --- | --- |
| EDA 主报告 | `reports/eda/eda_report.md` | 总览数据快照、关键观察、Top family 和图表入口 |
| 图表目录 | `reports/eda/figures/` | 存放趋势、family、促销、油价、节假日、门店和验证 fold 图 |
| 汇总表目录 | `reports/eda/tables/` | 存放 dataset、family、holiday、store cluster 汇总表 |

## 数据快照

| 指标 | 数值 | 解读 |
| --- | ---: | --- |
| 训练行数 | 3,000,888 | 数据量足够支撑全局模型 |
| 测试行数 | 28,512 | `54 stores * 33 families * 16 days` |
| 训练日期 | 2013-01-01 到 2017-08-15 | 历史跨度约 4.5 年 |
| 测试日期 | 2017-08-16 到 2017-08-31 | 固定未来 16 天预测 |
| 门店数 | 54 | 多门店面板预测 |
| family 数 | 33 | 多品类预测 |
| 零销量行比例 | 31.30% | 零销量不是噪声，是重要建模问题 |
| 训练期 `onpromotion` 均值 | 2.60 | 促销是常见但分布偏斜的特征 |

## EDA 观察到建模假设

| EDA 观察 | 证据 | 建模假设 | 下一步验证 |
| --- | --- | --- | --- |
| 销售有明显日历结构 | 每周平均销量中 Sunday 和 Saturday 高于工作日；EDA 报告也指出 sales 有 strong calendar structure | 日历特征和时间验证必须保留；随机切分不可信 | 检查 `day_of_week`、`is_weekend`、`is_payday` 对模型的重要性或误差影响 |
| 零销量比例高，且 family 差异很大 | 整体零销量比例 31.30%；`BOOKS` 零销量率约 96.96%，`BABY CARE` 约 94.13%，`SCHOOL AND OFFICE SUPPLIES` 约 74.08% | 所有 family 共用一个模型可能会低估低需求品类的零销量行为 | 做 family 级误差分析，单独检查高零销量 family 的 RMSLE |
| 高销量 family 占主导 | `GROCERY I`、`BEVERAGES`、`PRODUCE`、`CLEANING`、`DAIRY` 是 Top family | 模型整体分数可能被大品类主导，但 RMSLE 仍会惩罚低销量相对误差 | 同时看 total sales 排名和 RMSLE 排名，避免只优化大品类 |
| 促销和销量有明显关系 | 训练期 promotion bin 越高，平均 sales 越高；`51+` 促销 bin 平均 sales 约 3540，高于无促销约 158 | `onpromotion` 是重要未来已知变量，且可能需要 family 交互或非线性处理 | 按 family 和 promotion bin 做误差分析，检查高促销样本是否预测偏差更大 |
| 测试期促销强度高于训练期 | 训练期 `onpromotion` 均值约 2.60，测试期约 6.97 | 存在 train-test distribution shift，模型可能在高促销测试样本上泛化不足 | 对比训练末 90 天和测试期的 promotion 分布，并检查验证集高促销误差 |
| 门店 type/cluster 销售差异明显 | store cluster 汇总中不同 type/cluster 的 total_sales 和 mean_store_sales 差异大 | `store_type`、`cluster`、`city/state` 应保留；可能存在门店分群特征价值 | 做 store 或 cluster 级误差分析，检查是否某些门店群系统性偏差 |
| 节假日/事件不能只当作普通日期 | holidays 表中 Local、Regional、National 都存在，且 Event / Holiday / Additional 等类型不同 | 节假日特征需要保留 locale 和 type 信息，不能只有一个粗糙 `is_holiday` | 检查节假日窗口样本的误差，并区分 National / Regional / Local |
| 验证 fold 越靠后误差越高 | 三个 fold RMSLE 分别为 0.381085、0.400716、0.423002 | 模型在接近测试期的时间段表现变差，可能存在时间分布漂移或 public mismatch | 优先分析 fold 3 的错误来源，而不是只看三折均值 |

## 当前 5 条可讲述 EDA 发现

1. 销售具有明显日历周期，周末平均销售更高，所以验证必须按时间切分，日历特征应保留。
2. 零销量行比例达到 31.30%，且不同 family 差异极大，因此低需求品类不能被当作普通噪声处理。
3. 促销强度和销量呈明显正相关，且测试期促销均值高于训练期，后续要重点检查高促销样本的泛化。
4. 门店 type/cluster 的销量差异明显，门店静态信息应作为特征保留，并在误差分析中按门店分组检查。
5. 多窗口验证中越靠近测试期 RMSLE 越高，说明当前模型存在稳定性问题，下一步要重点分析 fold 3。

## 你需要自己判断的地方

| 判断问题 | 你需要给出的答案 |
| --- | --- |
| 哪个 EDA 发现最可能解释 Kaggle public score 偏高？ | 多窗口验证中越靠近测试期 RMSLE 越高，说明当前模型存在稳定性问题。下一步要重点分析 fold 3，因为它最接近 public 测试期。 |
| 高零销量 family 应该单独建模，还是先加特征？ | 先加特征。family 差异很大，所有 family 共用一个模型可能会低估低需求品类的零销量行为；但在单独建模前，应先通过特征和误差分析确认问题集中在哪些 family。 |
| 促销特征应该继续增强吗？如果增强，先做什么？ | 应该增强。促销强度和销量呈明显正相关，且测试期促销均值高于训练期。先检查高促销样本的泛化误差，再考虑加入 family 级促销响应特征。 |
| fold 3 变差更可能来自时间漂移、促销分布变化，还是节假日/事件？ | 当前判断更可能来自时间漂移，但需要用 fold 对比和特征分布检查验证，不能只凭直觉下结论。 |
| 下一步应该先做误差分析，还是直接尝试 extended lag？ | 先做误差分析。先找出错误集中在哪些 family、store、promotion bin 和 fold，再决定是否尝试 extended lag。 |

## 你的阶段 3 判断

当前你自己的判断是：

- public score 偏高最可能和 fold 越靠近测试期误差越高有关，说明模型稳定性不足。
- 高零销量 family 暂时不直接单独建模，先通过特征和误差分析确认问题。
- 促销特征值得增强，但第一步不是直接加复杂特征，而是先检查高促销样本的误差。
- fold 3 变差暂时判断为时间漂移，但需要后续用数据验证。
- 下一步先做误差分析，不直接尝试 `extended` lag。

这组判断可以作为阶段 4 的工作依据。

## 阶段 3 结论

阶段 3 的结论是：当前最值得优先进入阶段 4 误差分析的方向不是盲目换模型，而是分组看错误来源。

优先顺序：

1. 按 `family` 统计 RMSLE 和零销量率。
2. 按 `store_nbr` / `cluster` 统计 RMSLE。
3. 按 `onpromotion` 分箱统计 RMSLE。
4. 对比 fold 1、fold 2、fold 3 的错误分布。
5. 再决定是否尝试 `extended` 特征或更复杂模型。

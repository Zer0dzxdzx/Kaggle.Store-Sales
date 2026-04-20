# Store Sales 阶段 4 说明文档：误差分析

## 阶段目标

阶段 4 的目标不是继续加特征，也不是直接换模型，而是回答一个更基础的问题：

> 当前 baseline 到底错在哪里？

如果不先做误差分析，后续优化很容易变成盲目调参。比如看到 Kaggle public score 不理想，就直接换模型或加一堆 lag，这样即使分数变化，也很难解释为什么变好或变差。

本阶段只做四类分析：

- family error
- store error
- promotion bin error
- fold comparison

这四类分析对应阶段 3 的四个主要假设：family 差异、门店差异、促销分布变化、验证窗口越靠近测试期越差。

## 本阶段输入

误差分析使用已有的多窗口验证预测结果：

| 文件 | 作用 |
| --- | --- |
| `artifacts/validation_predictions_fold_01.csv` | fold 1 的验证集真实值和预测值 |
| `artifacts/validation_predictions_fold_02.csv` | fold 2 的验证集真实值和预测值 |
| `artifacts/validation_predictions_fold_03.csv` | fold 3 的验证集真实值和预测值 |
| `artifacts/validation_summary.csv` | 每个 fold 的验证日期、行数和 RMSLE |
| `data/raw/train.csv` | 补充验证样本的 `onpromotion` |
| `data/raw/stores.csv` | 补充门店的 city、state、store_type、cluster |

这些文件只来自本地验证，不使用 Kaggle public label。

## 本阶段输出

| 文件 | 作用 |
| --- | --- |
| `reports/error_analysis/error_analysis_report.md` | 阶段 4 主报告，汇总最重要发现 |
| `reports/error_analysis/tables/family_error.csv` | 按 family 分组的误差表 |
| `reports/error_analysis/tables/store_error.csv` | 按 store / city / state / type / cluster 分组的误差表 |
| `reports/error_analysis/tables/promotion_bin_error.csv` | 按 `onpromotion` 分箱的误差表 |
| `reports/error_analysis/tables/fold_comparison.csv` | 按 validation fold 对比的误差表 |

说明：

- family error、store error、promotion bin error 是把多个 validation fold 合并后的汇总结果。
- fold comparison 只回答不同验证窗口的整体 RMSLE 趋势，不解释具体 segment 原因。
- 如果后面要判断 fold 3 为什么变差，需要另开 fold x family、fold x store 或 fold x promotion 的交叉分析。

## 误差分析脚本做了什么

入口命令：

```bash
PYTHONPATH=src python3 -m store_sales.error_analysis \
  --data-dir data/raw \
  --artifacts-dir artifacts \
  --output-dir reports/error_analysis
```

执行链路：

```text
读取 validation_predictions_fold_*.csv
  -> 读取 validation_summary.csv
  -> 校验 fold id 和 validation rows 是否一致
  -> merge train.csv 中的 onpromotion
  -> merge stores.csv 中的门店静态信息
  -> 计算每一行预测误差
  -> 分别按 family、store、promotion bin、fold 汇总
  -> 输出 4 张 CSV 和 1 份 Markdown 报告
```

这里的 merge 只用于解释验证误差，不用于训练模型。`train.csv` 的 `onpromotion` 在验证日期是已知字段，`stores.csv` 是静态门店信息，所以这一步不会引入目标泄漏。

## 表格字段怎么读

| 字段 | 含义 | 怎么解释 |
| --- | --- | --- |
| `row_count` | 当前分组包含多少验证样本 | 样本太少的分组不宜过度解读 |
| `rmsle` | 当前分组的 RMSLE | 越高说明该组相对误差越大 |
| `mean_abs_log_error` | 平均绝对 log 误差 | 用于辅助理解 RMSLE，不是比赛主指标 |
| `actual_zero_rate` | 真实销量为 0 的比例 | 高值说明该组有大量零销量样本 |
| `predicted_zero_rate` | 预测销量为 0 的比例 | 如果真实零销量很多但预测零很少，模型可能不擅长识别零销量 |
| `mean_actual_sales` | 平均真实销量 | 用来判断该组是低销量还是高销量 |
| `mean_predicted_sales` | 平均预测销量 | 和真实均值对比可看整体偏高或偏低 |
| `mean_signed_error` | 平均预测误差，预测值减真实值 | 正数表示整体高估，负数表示整体低估 |
| `mean_onpromotion` | 平均促销数量 | 用来判断该组是否和促销强度有关 |

RMSLE 的特点是对相对误差敏感。低销量或零销量样本中，预测错一点也可能造成较大的 log 误差。因此不能只看总销量大的品类，也要看低销量和高零销量品类。

## Family Error 怎么读

当前报告中 RMSLE 最高的 family：

| family | RMSLE | 真实零销量率 | 平均真实销量 | 平均预测销量 | 初步解释 |
| --- | ---: | ---: | ---: | ---: | --- |
| SCHOOL AND OFFICE SUPPLIES | 0.671040 | 55.13% | 22.79 | 7.04 | 模型明显低估，且零销量比例高 |
| LINGERIE | 0.624578 | 10.07% | 6.96 | 5.59 | 低销量品类，相对误差容易放大 |
| GROCERY II | 0.621563 | 1.62% | 32.39 | 29.52 | 不是高零销量问题，可能是品类波动或特征不足 |
| CELEBRATION | 0.565454 | 2.12% | 13.37 | 11.47 | 低销量且可能受节日/事件影响 |
| HARDWARE | 0.529902 | 38.43% | 1.48 | 1.13 | 极低销量品类，零销量问题明显 |

这个表说明：最差 family 不完全等于最高零销量 family。

阶段 3 原本怀疑“高零销量 family 可能贡献主要误差”。阶段 4 的结果支持一部分，但不是全部。`SCHOOL AND OFFICE SUPPLIES` 和 `HARDWARE` 确实有较高零销量率，但 `GROCERY II` 的零销量率很低，仍然 RMSLE 很高。

更合理的判断是：

- 零销量问题需要处理，但不能只处理零销量。
- 低销量 family 的相对误差也很重要。
- 后续特征可以优先考虑 family 级历史均值、family 级零销量率、低需求标记。
- 暂时不应该立刻拆成很多单独模型，因为目前还没有证明所有错误都来自同一种 family 模式。

## Store Error 怎么读

当前报告中 RMSLE 最高的门店：

| store_nbr | city | state | store_type | cluster | RMSLE | 初步解释 |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 19 | Guaranda | Bolivar | C | 15 | 0.489965 | 当前最差门店，需要检查是否系统性低估 |
| 26 | Guayaquil | Guayas | D | 10 | 0.469451 | Guayas 区域门店之一 |
| 22 | Puyo | Pastaza | C | 7 | 0.461829 | type C 门店 |
| 14 | Riobamba | Chimborazo | C | 7 | 0.461811 | type C 门店 |
| 32 | Guayaquil | Guayas | C | 3 | 0.450065 | Guayas 区域、type C |

这个表的重点不是记住哪个 store 最差，而是观察错误是否集中在某些门店属性上。

当前前几名里出现了多个 `store_type = C`，也出现了多个 `Guayas` 门店，但样本还不足以直接下结论说“type C 一定有问题”或“Guayas 一定有问题”。

更合理的判断是：

- 门店静态信息应该保留，因为不同门店误差确实不同。
- 下一步可以考虑按 `store_type`、`cluster` 或 `state` 做更高层级汇总。
- 如果某些门店长期系统性高估或低估，可以考虑加入 store 级历史均值、store-family 历史均值或门店分群特征。

## Promotion Bin Error 怎么读

当前促销分箱结果：

| promotion_bin | RMSLE | 平均真实销量 | 平均预测销量 | 解读 |
| --- | ---: | ---: | ---: | --- |
| 0 | 0.451970 | 57.81 | 56.07 | 无促销样本误差最高 |
| 1 | 0.418458 | 92.14 | 89.58 | 单个促销样本误差仍偏高 |
| 2-5 | 0.367472 | 230.28 | 233.74 | 中低促销误差下降 |
| 6-10 | 0.258259 | 719.07 | 779.11 | 高促销样本整体高估 |
| 11-50 | 0.296837 | 1573.74 | 1591.09 | 高促销样本误差不算最高 |
| 51+ | 0.149562 | 3951.04 | 3864.20 | 极高促销样本 RMSLE 最低 |

这个结果很重要，因为它修正了阶段 3 的一个直觉。

阶段 3 看到测试期 `onpromotion` 均值高于训练期，所以怀疑高促销样本可能泛化更差。但阶段 4 的分箱结果显示，RMSLE 最高的是 `promotion_bin = 0`，不是高促销样本。

合理解释：

- 高促销样本平均销量更高，RMSLE 对相对误差敏感，模型反而更容易在这些稳定高销量样本上取得较低 RMSLE。
- 无促销样本数量最多，且包含大量低销量、零销量和波动样本，所以 RMSLE 更高。
- 促销仍然重要，但当前最优先的问题不一定是“高促销泛化差”。

后续判断：

- 不要马上只做高促销特征。
- 可以先做 `family x promotion_bin` 交叉误差，确认是否有某些 family 在高促销时出错。
- 可以考虑加入“无促销低需求样本”的特征，而不是只加强高促销样本。

## Fold Comparison 怎么读

当前多窗口验证结果：

| fold | 验证日期 | RMSLE | 相比上一 fold | 平均真实销量 | 平均预测销量 | 解读 |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | 2017-06-29 到 2017-07-14 | 0.381085 |  | 484.80 | 483.47 | 最早窗口，表现最好 |
| 2 | 2017-07-15 到 2017-07-30 | 0.400716 | +0.019631 | 481.76 | 466.88 | 分数变差，整体偏低估 |
| 3 | 2017-07-31 到 2017-08-15 | 0.423002 | +0.022286 | 467.14 | 494.45 | 分数继续变差，整体偏高估 |

这个表支持阶段 3 的判断：越靠近测试期，当前模型的验证 RMSLE 越差。

但它不能直接说明原因。fold 3 变差可能来自：

- 时间漂移
- 某些 family 在 fold 3 出错
- 某些 store 在 fold 3 出错
- 促销分布变化
- 节假日或特殊事件影响
- 递归预测误差在后期累积

所以当前只能下这个结论：

> fold 3 确实更差，但原因还没有被定位。阶段 4 当前版本只完成了第一层误差定位。

## 你需要自己回答的问题

| 问题 | 当前更合适的回答 |
| --- | --- |
| 最差 family 是否集中在高零销量、低销量品类？ | 部分是。`SCHOOL AND OFFICE SUPPLIES` 和 `HARDWARE` 支持这个判断，但 `GROCERY II` 说明问题不只来自高零销量。 |
| 最差 store 是否集中在某些 city、state、store_type 或 cluster？ | 有一些线索，例如多个 top error store 属于 `store_type = C` 或 `Guayas`，但还不能直接下定论。 |
| 高 `onpromotion` 分箱是否比低促销分箱误差更高？ | 没有。当前最高 RMSLE 是无促销样本，说明促销方向需要重新审视。 |
| fold 3 是否比 fold 1/2 整体变差？ | 是。RMSLE 从 0.381085 到 0.400716 再到 0.423002，呈持续上升。 |
| 下一步应该直接加 extended lag 吗？ | 不建议直接加。更合理的是先根据这四张表选择一个明确实验方向。 |

## 当前不能下的结论

以下说法目前证据不足：

- 不能说 public score 偏高一定是高促销导致的。
- 不能说所有高零销量 family 都需要单独建模。
- 不能说 type C 或 Guayas 门店一定有系统性问题。
- 不能说 fold 3 变差一定是时间漂移。
- 不能说换模型一定比做特征工程更重要。

这些结论需要后续交叉误差分析或特征实验验证。

## 阶段 4 结论

阶段 4 的第一层结论是：

- 当前 baseline 的误差不是均匀分布的，family、store、promotion bin 和 fold 都存在明显差异。
- family 误差中，低销量和部分高零销量品类值得重点关注。
- store 误差显示门店层面存在差异，但是否由 city、state、type 或 cluster 造成还需要继续验证。
- promotion bin 结果推翻了“高促销一定最差”的直觉，当前无促销样本 RMSLE 最高。
- fold comparison 证明 fold 3 整体更差，但还不能解释 fold 3 变差原因。

更稳妥的下一步是：

1. 先选一个优化方向，不要同时改太多东西。
2. 优先考虑 family 级低需求和零销量相关特征。
3. 如果继续分析 fold 3，需要做 fold x family、fold x store 或 fold x promotion 交叉误差。
4. 每次实验必须写入 `docs/experiment_log.csv`，记录验证结果和是否保留。

## 面试中可以怎么讲

可以这样描述阶段 4：

> 我没有直接堆模型，而是先用多窗口验证预测做分组误差分析。按 family、store、promotion bin 和 fold 统计 RMSLE 后发现，误差主要集中在部分低销量或高零销量品类，同时验证窗口越靠近测试期分数越差。促销分析也修正了一个初始假设：高促销样本并不是 RMSLE 最高的分组，反而无促销样本误差更高。因此后续优化应优先围绕低需求品类和时间稳定性做实验，而不是盲目增强高促销特征。

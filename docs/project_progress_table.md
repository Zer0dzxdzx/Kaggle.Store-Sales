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
| 6. 项目总结 | 2026-04-21 | 把项目转成简历和面试可讲述内容 | 决定哪些结论真实、哪些不能夸大 | 整理 README、简历摘要和面试深挖文档 | `docs/resume_project_summary.md` 和 `docs/interview_deep_dive.md` | 初版完成 |
| 7. 验证协议与 Gate | 2026-05-07 | 固化正式验证口径与 submission 决策门槛 | 判断哪些指标是主判断，哪些只是风险提示，什么情况下值得提交 | 汇总历史成败案例、整理 validation protocol 与 submission gate 文档 | `docs/validation_protocol.md` 和 `docs/submission_gate.md` | 初版完成 |
| 8. LightGBM 系统化调参 | 2026-05-07 | 在统一验证协议下比较 LightGBM 参数候选 | 判断是否替换当前 `lightgbm_baseline`，以及 broad tuning 是否继续 | 跑 baseline/shrinkage/regularized/conservative 对比并整理报告 | `docs/lightgbm_tuning_log.md` 和 `reports/validation/lightgbm_tuning/` | 第一轮完成，baseline 继续保留 |
| 9. 特征消融 | 2026-05-07 | 用移除实验判断哪些特征组真正贡献稳定收益 | 判断哪些特征应保留、哪些只是候选删除或重设计 | 实现 ablation 工具、输出各组移除后的多窗口结果 | `src/store_sales/feature_ablation.py` 和 `reports/feature_ablation/lightgbm_baseline_fast300/` | 第一轮完成，作为方向证据 |
| 10. 作品集化：可复现性 | 2026-05-09 | 让别人能按文档从环境、数据到验证和 submission 重新跑通项目 | 判断哪些结果可以本地复现，哪些只能作为 Kaggle 外部评测记录 | 整理环境安装、数据放置、主验证命令、submission 生成和检查方式 | `docs/reproducibility.md` | 初版完成 |
| 11. 作品集化：轻量测试 | 2026-05-09 | 用自动化 sanity checks 保护验证、lag、递归预测和 submission 格式 | 判断哪些测试最能防止项目关键逻辑回归，而不是追求形式化覆盖率 | 编写 pytest 小样本测试并同步 README / 复现文档 | `tests/` 和 `pyproject.toml` | 初版完成，11 个测试通过 |
| 12. 作品集化：case study | 2026-05-09 | 把实验过程整理成可复述的项目故事 | 判断哪些内容最能体现数据科学能力，哪些结果不能夸大 | 整理业务问题、验证、实验转折、结果和面试讲述版本 | `docs/case_study.md` | 初版完成 |
| 13. 作品集化：面试讲述稿 | 2026-05-10 | 把 case study 压缩成面试现场可讲的话术 | 判断不同岗位该强调数据分析、验证设计还是建模对比 | 整理 15/30/60 秒版本、高频追问、岗位版本和禁用说法 | `docs/interview_talk_track.md` | 初版完成 |
| 14. 作品集化：文档导航与 CI | 2026-05-11 | 把作品集材料收口成易审阅、可自动检查的仓库 | 判断文档入口如何分层，CI 先覆盖哪些关键 sanity checks | 新增文档导航和 GitHub Actions pytest workflow | `docs/index.md` 和 `.github/workflows/tests.yml` | 初版完成 |

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

阶段 5 global model / feature comparison 已完成：

- 对比对象包括 `seasonal_naive`、`ridge_baseline`、`histgbdt_compact`、`histgbdt_baseline`、`histgbdt_extended`。
- 使用同一组 August / pre-test explicit windows，保证和前面的失败实验诊断在同一验证框架下比较。
- `histgbdt_baseline` mean RMSLE 为 `0.490514`，仍是当前最稳方案。
- `histgbdt_compact` mean RMSLE 为 `0.492959`，fold 1 改善但 fold 2/3/4 变差。
- `histgbdt_extended` mean RMSLE 为 `0.500922`，fold 1/3/4 改善但 fold 2 大幅变差。
- `seasonal_naive` 和 `ridge_baseline` 明显弱于 tree baseline，只能作为参考。
- LightGBM 本轮未运行，因为当前环境没有安装 `lightgbm`。
- 决策：不替换 baseline，不生成新提交；下一步优先尝试 LightGBM 或简单 blending，并继续用 stability slice checks 作为保留门槛。

阶段 5 simple prediction blending 已完成：

- LightGBM 当前环境不可用，未运行训练；本轮先做不依赖新包的 simple blending。
- 新增 `src/store_sales/blend_validation.py`，用于读取两个 validation run 的 fold predictions 并按权重混合。
- `baseline + seasonal_naive` 失败：`99% baseline + 1% seasonal_naive` mean RMSLE 为 `0.495169`，差于 baseline `0.490514`。
- `baseline + extended` 有信号：最佳为 `55% baseline + 45% extended`，mean RMSLE `0.486839`，worst fold `0.645720`。
- 但最佳 blend 的 fold 2 回退 `+0.009239`。
- stability checks 显示 target family 略差，仍有 `7` 个非目标 family 变差，并有 `15` 个 test-overweighted non-target regression slices。
- 决策：暂不生成 Kaggle submission；该 blend 只能作为有风险候选，当时 best submission 仍是 baseline public score `0.58410`。

阶段 5 LightGBM baseline validation 已完成：

- 已安装并验证 `lightgbm==4.6.0` 可用。
- 使用 baseline feature profile 和同一组 August / pre-test explicit windows 跑 `--model-type lightgbm`。
- `lightgbm_baseline` mean RMSLE 为 `0.486767`，低于 `histgbdt_baseline` 的 `0.490514`，也略低于最佳 simple blend 的 `0.486839`。
- worst fold 从 baseline `0.656282` 降到 `0.583115`，改善明显。
- 但 fold 1/2 分别回退 `+0.048240` 和 `+0.040950`。
- stability checks 显示 target family 和 non-target overall 都改善，但仍有 `13` 个非目标 family 变差，以及 `8` 个 test-overweighted non-target regression slices。
- 已生成 candidate submission：`artifacts/submissions/lightgbm_baseline_v1/submission.csv`。
- submission 已通过本地格式校验：行数/id 顺序与 `sample_submission.csv` 一致，无重复、缺失、负数或非有限值。
- Kaggle public score 为 `0.50834`，明显优于 baseline public score `0.58410`。
- 决策：LightGBM baseline 成为当前 best submission；下一步围绕 LightGBM 做参数收缩、early stopping 或稳定性约束。

阶段 7 验证协议与 submission gate 初版已完成：

- 正式主验证协议固定为 `August / pre-test explicit windows`。
- 提交判断不再只看 mean RMSLE，而是必须结合 `worst fold`、`non-target families worsened`、`overweighted non-target regression slices` 和 promotion bin stability。
- 当前参考方案拆成两层：
  - 历史诊断参考：`histgbdt_baseline`
  - 当前 submission 参考：`lightgbm_baseline`
- gate 结果分成三档：
  - `Promote`
  - `Review`
  - `Block`
- 历史案例校准结论：
  - `school_supplies_aug_promo` 应被 `Block`
  - `baseline + extended blend` 应被 `Block`
  - `lightgbm_baseline` 属于 `Review`，它是带 warning 的强候选，而不是无风险候选
- 下一步不应直接盲目调参，而是先按这套 protocol/gate 跑后续 LightGBM 候选。

阶段 8 LightGBM 系统化调参第一轮已完成：

- 固定 `baseline` feature profile，不同时改特征和模型，保证实验只回答“参数是否更稳”。
- 固定使用 August / pre-test explicit windows：
  - `2014-08-16:2014-08-31`
  - `2015-08-16:2015-08-31`
  - `2016-08-16:2016-08-31`
  - `2017-07-31:2017-08-15`
- 对比候选包括 `lightgbm_baseline`、`lightgbm_shrinkage_es`、`lightgbm_regularized_es`、`lightgbm_conservative_es`。
- `lightgbm_baseline` mean RMSLE 为 `0.486767`，worst fold 为 `0.583115`，仍是本轮最优。
- `lightgbm_shrinkage_es` mean RMSLE 为 `0.499285`，worst fold 恶化到 `0.710339`。
- `lightgbm_conservative_es` mean RMSLE 为 `0.507772`，worst fold 为 `0.711345`。
- `lightgbm_regularized_es` mean RMSLE 为 `0.519939`，worst fold 为 `0.717537`。
- 决策：不替换 `lightgbm_baseline`；第一轮 broad tuning 没有带来稳定提升，后续应转向 worst fold、non-target family 和 test-like slice 的稳定性优化。

阶段 9 特征消融第一轮已完成：

- 新增/使用 `feature_ablation` 流程，按特征组做移除实验。
- 本轮使用 `lightgbm_baseline_fast300` 配置，baseline mean RMSLE 为 `0.498996`，worst fold 为 `0.594955`。
- 由于该配置使用 `n_estimators=300` 的快速版本，它适合作为方向性证据，不应直接等同于最终 submission 配置。
- 移除后最明显变差的特征组是 `sales_rolling`，mean delta 为 `+0.061111`，说明滚动销量统计是当前最重要的特征组。
- `promotion` mean delta 为 `+0.042030`，说明促销特征需要继续保留并可能继续增强。
- `earthquake`、`store_metadata`、`holidays`、`identity`、`transactions` 移除后也不同程度变差，暂不直接删除。
- `calendar` 是 mixed 信号：mean 变差但 worst fold 变好，不能直接作为保留或删除判决。
- `oil` 移除后 mean delta 为 `-0.000803`，是小幅 removal candidate，但收益很小，需要复验。
- `sales_lags` 移除后 mean RMSLE 变好，但 worst fold 变差 `+0.016073`，属于混合信号，不能简单删除。
- 决策：短期保留 `sales_rolling` 和 `promotion`，把 `oil` 与 `sales_lags` 作为后续复验/重设计对象。

阶段 10 作品集化可复现性初版已完成：

- 新增 `docs/reproducibility.md`，把项目复现拆成环境安装、数据放置、smoke check、主验证协议复现和 submission 生成。
- 明确区分“本地可复现结果”和“Kaggle public score 外部评测记录”。
- 当前推荐复现当前 champion 的命令使用 `lightgbm_baseline + baseline feature profile + 4 个 August / pre-test explicit windows`。
- 复现文档给出预期产物，包括 `validation_metrics.json`、`validation_summary.csv`、`validation_predictions_fold_*.csv` 和 `submission.csv`。
- README 已加入可复现性文档入口。

阶段 11 作品集化轻量测试初版已完成：

- 新增 `tests/`，使用小样本 DataFrame 测试关键逻辑，不依赖 Kaggle 全量数据。
- 测试覆盖 validation windows、submission frame、training lag safety、recursive lag safety 和 recursive forecast 写回逻辑。
- `pyproject.toml` 新增 `test` optional dependency 和 pytest 默认测试目录。
- README 和 `docs/reproducibility.md` 已加入 `python3 -m pytest -q`。
- 本地结果：`11 passed`。

阶段 11 之后的下一步原本是写完整 case study；该事项已在阶段 12 完成。

阶段 12 作品集化 case study 初版已完成：

- 新增 `docs/case_study.md`，把项目主线整理为问题、数据、EDA、baseline、误差分析、失败实验、验证协议、模型对比、特征消融和工程化收口。
- case study 中明确当前 champion 是 `lightgbm_baseline`，public score 为 `0.50834`，原始 HistGBDT baseline public score 为 `0.58410`。
- 文档单独解释 `school_supplies_aug_promo` 为什么是有价值的失败实验。
- 文档包含 30 秒和较完整的面试讲述版本。
- README 已加入 case study 入口。

下一步应整理独立的 interview talk track，把 case study 压缩成面试现场更自然的 30 秒、60 秒和追问回答模板。

阶段 13 作品集化面试讲述稿初版已完成：

- 新增 `docs/interview_talk_track.md`，把 case study 压缩成面试现场话术。
- 文档包含 15 秒、30 秒、60 秒和 3 分钟版本。
- 文档整理了数据泄漏、随机切分、transactions、递归预测、RMSLE、失败实验、LightGBM 选择和项目局限等高频追问。
- 文档单独区分数据分析岗位版本和数据科学岗位版本。
- README 已加入面试讲述稿入口。

阶段 14 作品集化文档导航与 CI 初版已完成：

- 新增 `docs/index.md`，把 README、结果总结、case study、复现、验证协议、学习记录、报告和面试材料分层整理。
- 新增 `.github/workflows/tests.yml`，在 push / pull request 到 `main` 时运行 `python -m pytest -q`。
- README 增加文档导航入口、CI 说明和工程检查说明。
- 当前 CI 只覆盖 11 个轻量 sanity checks，不依赖 Kaggle 全量数据。

一周作品集化收尾已完成。下一步可以根据具体岗位 JD 定制更短讲稿，或继续做模型稳定性优化。

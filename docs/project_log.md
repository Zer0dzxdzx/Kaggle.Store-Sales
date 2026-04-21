# Store Sales 项目日志

## 项目概览

- 项目名称：`Kaggle Store Sales`
- 仓库路径：`/Users/du/Desktop/codex/Store Sales`
- GitHub 仓库：`https://github.com/Zer0dzxdzx/Kaggle.Store-Sales`
- 当前目标：围绕 Kaggle `Store Sales - Time Series Forecasting` 比赛，建立可迭代的时序预测工程基线，并逐步提升验证与榜单表现。
- 结构化实验记录文件：`docs/experiment_log.csv`

## 记录规则

后续建议每次发生下面任一事件时追加一条日志：

- 新增或重构核心模块
- 修正影响训练/验证正确性的逻辑
- 更新重要文档
- 完成一次有意义的实验
- 调整验证方案、特征方案或模型方案

如果需要快速回顾实验版本、分数、结论和下一步，优先查看 `docs/experiment_log.csv`。本文件更适合记录阶段性里程碑和背景说明。

建议每条日志至少包含：

- 日期
- 目标
- 改动内容
- 结果
- 风险/问题
- 下一步

## 时间线

### 2026-04-15

#### 阶段 1：初始化项目与基线流水线

- 本地初始化 Git 仓库，并建立基础目录结构。
- 创建了模块化训练框架，核心模块包括：
  - `src/store_sales/data.py`
  - `src/store_sales/features.py`
  - `src/store_sales/modeling.py`
  - `src/store_sales/pipeline.py`
  - `src/store_sales/cli.py`
- 建立了从原始 CSV 到训练、验证、递归预测、提交文件导出的完整流程。
- 默认模型采用 `HistGradientBoostingRegressor`，同时预留 `LightGBM` 可选后端接口。
- 在特征侧加入了：
  - 日历特征
  - 滞后特征
  - 滚动统计特征
  - 油价特征
  - 节假日/事件特征
  - 门店静态特征
  - 发薪日与地震冲击特征
- 为验证过程实现了递归预测逻辑，避免多步预测时错误使用未来真实销量。
- 对 `transactions` 的使用加了时间边界，避免验证阶段聚合到未来信息。

结果：

- 项目形成了可运行的 baseline。
- 生成了 `README.md`、`pyproject.toml` 和基础忽略规则。
- 在合成数据上完成了端到端 smoke test。

相关提交：

- `b8972b8` `feat: add modular store sales baseline pipeline`

#### 阶段 2：发布到 GitHub

- 配置远端 `origin` 为 `git@github.com:Zer0dzxdzx/Kaggle.Store-Sales.git`。
- 将本地 `main` 分支首次推送到 GitHub 仓库。

结果：

- 本地与远端仓库打通，后续可以直接基于 `origin/main` 继续迭代。

#### 阶段 3：补充比赛说明文档

- 新增了 `docs/store_sales_competition_guide.md`，系统整理比赛目标、数据表结构、评估指标、验证方案、特征工程重点、建模路线与常见坑。
- 将比赛说明入口挂到 `README.md`。
- 对公开镜像中“测试窗口 15 天/16 天”表述不一致的问题进行了说明，并明确建议以手头原始 `test.csv` 的真实日期范围为准。
- 将 `README.md` 中默认验证窗口的说法调整为“本地默认验证窗口”，避免把工程参数写成官方题面事实。
- 将 `.DS_Store` 加入 `.gitignore`。

结果：

- 仓库文档从“仅有使用说明”升级为“包含比赛理解、建模建议与工程记录入口”的状态。

相关提交：

- `ac0009d` `docs: add detailed store sales competition guide`

#### 阶段 4：补充项目日志

- 新增本文件 `docs/project_log.md`，用于持续记录项目进展、关键设计决策、验证结果与后续计划。
- 将项目日志入口挂到 `README.md`。

当前状态：

- 仓库具备基础建模能力与文档说明能力。
- 代码和文档均已过一轮子代理复核。
- 目前尚未在真实 Kaggle 原始数据上完成一次正式训练与提交验证。

下一阶段里程碑：

1. 下载并放置真实 Kaggle 原始 CSV，跑通首次正式训练。
2. 记录首个真实验证分数与首个公开榜单分数。
3. 增加多窗口时序验证，避免只盯最后一个窗口。
4. 继续迭代节假日处理、促销特征与更强模型。

### 2026-04-16

#### 阶段 5：跑通真实数据 baseline

- 使用 `data/raw/` 中的真实 Kaggle 原始数据运行了当前 `HistGradientBoostingRegressor` 基线。
- 成功生成：
  - `artifacts/validation_metrics.json`
  - `artifacts/validation_predictions.csv`
  - `artifacts/submission.csv`
- 本次运行使用：
  - `train_start_date=2015-01-01`
  - `validation_horizon=16`
  - `model_type=hist_gbdt`
  - `random_state=42`

结果：

- 首个真实离线验证分数为 `RMSLE = 0.423002`
- Kaggle 公开榜分数为 `0.58410`
- 验证集行数为 `28,512`
- 提交文件行数为 `28,512`
- 预测值最小值为 `0.0`，最大值约为 `13031.17`

结论：

- 当前仓库已经从“工程基线可运行”进入“真实比赛基线已落地”的阶段。
- 后续所有实验都可以围绕这次真实 baseline 做对照，不需要再从合成数据结果出发。
- 公开榜分数明显高于单窗口离线分数，说明当前离线验证可能偏乐观；下一步应优先增加多窗口验证，而不是只追单次 holdout。

下一步：

1. 增加多窗口验证，检查离线分数与公开榜的相关性。
2. 把这次真实 baseline 作为 `experiment_log.csv` 中的主参照版本。
3. 尝试更稳的季节性/分组特征，或切换到更强的 `LightGBM` 后端。

#### 阶段 6：实现多窗口验证与自动实验日志

- 在 pipeline 中新增多窗口验证能力：
  - `validation_windows` 控制验证窗口数量
  - `validation_step_days` 控制相邻窗口间隔
  - 每个窗口都会输出独立的 `validation_predictions_fold_*.csv`
  - 汇总输出到 `validation_summary.csv`
- 在 metrics 中新增多窗口汇总指标：
  - `validation_rmsle_mean`
  - `validation_rmsle_std`
  - `validation_rmsle_min`
  - `validation_rmsle_max`
  - 每折起止日期、训练行数、验证行数与预测文件路径
- 新增 `src/store_sales/experiment_log.py`，支持在 CLI 运行结束后自动追加结构化实验日志。
- CLI 新增参数：
  - `--validation-windows`
  - `--validation-step-days`
  - `--log-experiment`
  - `--experiment-name`
  - `--experiment-log-path`
  - `--data-snapshot`
  - `--experiment-conclusion`
  - `--experiment-next-action`

结论：

- 后续实验可以直接用多窗口均值和标准差判断稳定性，不再只依赖最后一个 holdout。
- 实验记录可以由命令行自动写入，减少手工记录遗漏。

#### 阶段 7：新增 EDA 可视化报告

- 新增 `src/store_sales/eda.py`，用于生成可复现的 EDA 报告。
- 报告输出目录为 `reports/eda/`，包含：
  - `eda_report.md`
  - `figures/*.png`
  - `tables/*.csv`
- 当前 EDA 覆盖：
  - 全局每日销售趋势
  - family 销售排名
  - family 零销量比例
  - 星期周期
  - 促销与销售关系
  - 油价与月销售趋势
  - 节假日/事件日期平均销售
  - 门店 type/cluster 销售差异
  - 多窗口验证 fold 分数

结论：

- EDA 报告用于解释当前模型误差来源和指导下一轮特征工程。
- 下一步应结合验证误差分组，进一步检查哪些 family/store 是 public score 偏高的主要来源。

#### 阶段 8：明确简历级项目交付目标

- 项目目标从“跑出一份提交”升级为“可跑、可复现、可迭代、可讲述”的完整项目。
- 新增特征工程 profile：
  - `compact`
  - `baseline`
  - `extended`
- 新增模型类型：
  - `seasonal_naive`
  - `ridge`
  - `hist_gbdt`
  - `lightgbm`
- 新增 `compare` 命令，用于批量运行模型/特征方案并生成 `reports/model_comparison/`。
- 新增 `docs/resume_project_summary.md`，沉淀可写进简历和面试讲述的项目总结。
- 已完成第一版三模型三窗口对比：
  - `histgbdt_baseline`：mean RMSLE `0.401601`，std `0.017124`
  - `seasonal_naive`：mean RMSLE `0.458129`，std `0.053525`
  - `ridge_baseline`：mean RMSLE `2.734132`，std `0.016583`

结论：

- 后续所有优化必须通过多窗口验证和实验日志记录，不能只看单次提交分数。
- 树模型相对 seasonal lag benchmark 明显更好，但 Kaggle public score 仍高于本地验证，需要优先处理验证-public mismatch。
- `ridge_baseline` 在当前序数编码特征下效果很差，暂时只作为负向对照，不作为提交候选。
- 下一步应做按 `family`、`store_nbr`、零销量比例分组的误差分析，再决定是否启用 `extended` 特征方案。

#### 阶段 9：回到学习主线，从读题开始

- 新增 `docs/project_progress_table.md`，把项目拆成学习阶段，而不是只按代码功能推进。
- 当前先完成阶段 0：读题。
- 读题阶段记录了：
  - 比赛预测目标
  - 本地数据范围
  - 训练集与测试集时间范围
  - RMSLE 指标含义
  - 5 个关键问题的解释

结论：

- 后续项目推进要区分“用户自己主导的判断”和“Codex 辅助提速的工程工作”。
- 下一步进入阶段 1：读数据表，逐张判断每个 CSV 的业务含义、可用性和泄漏风险。

#### 阶段 10：读数据表

- 新增 `docs/data_tables_reading.md`，逐表记录本地 Kaggle CSV 的业务含义、字段、关键统计、使用方式和泄漏风险。
- 已核对的表包括：
  - `train.csv`
  - `test.csv`
  - `sample_submission.csv`
  - `stores.csv`
  - `oil.csv`
  - `holidays_events.csv`
  - `transactions.csv`
- 关键发现：
  - `train.csv` 零销量行比例约 `31.30%`
  - `test.csv` 的 `onpromotion` 均值约 `6.97`，高于训练集均值约 `2.60`
  - `oil.csv` 有 `43` 个油价缺失，需要插值或填充
  - `holidays_events.csv` 的 `locale` 需要区分 National / Regional / Local
  - `transactions.csv` 只到训练集最后一天，不能直接作为未来逐日特征

结论：

- `stores.csv`、合法处理后的 `oil.csv` 和 `holidays_events.csv` 可以对 train/test 直接对齐使用。
- `transactions.csv` 必须只做历史聚合，否则验证阶段容易泄漏未来真实客流。
- 下一步进入阶段 2：读 baseline，重点检查当前代码如何实现这些数据表的合并和泄漏控制。

补充说明：

- 已把 `merge`、数据泄漏、`transactions` 使用边界、测试期 `onpromotion` 分布差异补充到 `docs/data_tables_reading.md`。
- 后续进入代码阅读前，必须先能解释为什么 `stores.csv` 可以直接 merge，而 `transactions.csv` 不能直接按未来日期 merge。

#### 阶段 11：读 baseline

- 新增 `docs/baseline_reading.md`，按执行链路阅读当前 baseline。
- 阅读范围包括：
  - `src/store_sales/cli.py`
  - `src/store_sales/config.py`
  - `src/store_sales/data.py`
  - `src/store_sales/features.py`
  - `src/store_sales/modeling.py`
  - `src/store_sales/pipeline.py`
- 重点记录：
  - 原始 CSV 如何读入
  - `stores/oil/holidays/transactions` 如何 merge 或历史聚合
  - lag 和 rolling 特征如何避免使用当天真实 sales
  - 多窗口时间验证如何切分
  - `recursive_forecast()` 如何模拟真实 16 天预测

结论：

- 当前 baseline 的主要防泄漏点是：transactions 只基于 `train_history` 聚合；sales lag 使用 `shift`；验证和提交都用递归预测。
- 下一步进入阶段 3：EDA 解读，把已有图表转成你自己的建模假设。

补充说明：

- 已把阶段 2 的 6 个学习问题和合格答案整合进 `docs/baseline_reading.md`。

#### 阶段 12：EDA 解读

- 新增 `docs/eda_interpretation.md`，把已有 EDA 图表转成“观察 -> 建模假设 -> 下一步验证”的格式。
- 当前提炼的核心方向：
  - 日历周期明显，时间验证和日历特征必须保留
  - 零销量比例高且 family 差异大
  - 促销强度和销量相关，且测试期促销更强
  - 门店 type/cluster 有明显差异
  - 验证 fold 越靠近测试期 RMSLE 越高

结论：

- 阶段 3 的学习重点不是继续画图，而是把图表变成可验证假设。
- 下一步进入阶段 4：分组误差分析，优先按 `family`、`store_nbr/cluster`、`onpromotion` 分箱和 fold 对比检查错误来源。

用户当前判断：

- public score 偏高最可疑的线索是越靠近测试期的验证 fold 分数越差，但这只是观察和假设，需要 fold 3 分组误差分析确认。
- 高零销量 family 先做 family 级误差分析，不急着单独建模；如果确实贡献主要误差，再考虑零销量率、历史均值、低需求标记等特征。
- 促销特征值得继续检查，但应先按 `onpromotion` 分箱和 `family + promotion` 分组看误差。
- fold 3 变差优先怀疑时间漂移，但也可能来自促销、节假日、family/store 分布变化。
- 下一步先做误差分析，而不是直接尝试 `extended` lag；先定位错误来源，再决定特征实验。

#### 阶段 13：误差分析

- 新增 `src/store_sales/error_analysis.py`，用于生成阶段 4 的分组误差分析。
- 新增 `docs/error_analysis_reading.md`，记录阶段 4 的目标、输入、输出和需要判断的问题。
- 当前误差分析范围限定为：
  - family error
  - store error
  - promotion bin error
  - fold comparison

结论：

- 阶段 4 的目标是定位错误来源，不直接调参。
- 当前 family、store、promotion bin 是跨 validation folds 的汇总结果，fold comparison 只做 fold 级趋势判断。
- 先通过这四张表确认第一层错误方向，再决定是否继续做 fold 3 的交叉误差分析或特征实验。

补充说明：

- 已把阶段 4 误差分析扩展成完整说明文档，路径为 `docs/error_analysis_reading.md`。
- 文档补充了每张表的阅读方法、当前结果解读、不能下的结论和面试讲述版本。
- 当前阶段 4 的核心发现是：无促销样本 RMSLE 最高，fold 3 整体更差，family 误差更偏向低销量和部分高零销量品类。

#### 阶段 14：特征实验 1，low demand features

- 新增 `low_demand` feature profile，在 baseline 上加入 family 和 store-family 历史低需求统计。
- 新增 `docs/feature_experiments.md`，记录阶段 5 的实验假设、验证结果和保留决策。
- 新增 `reports/feature_experiments/low_demand_v1/experiment_report.md`，记录本次实验报告。
- 运行 3 窗口验证，输出目录为 `artifacts/experiments/histgbdt_low_demand_v1`。

结果：

- baseline mean RMSLE：`0.401601`。
- low demand v1 mean RMSLE：`0.403019`。
- baseline fold 3 RMSLE：`0.423002`。
- low demand v1 fold 3 RMSLE：`0.426889`。
- `SCHOOL AND OFFICE SUPPLIES` RMSLE 从 `0.671040` 恶化到 `0.712021`。

结论：

- 本实验不保留为默认方案。
- 低需求特征对少数 family 有小幅改善，但整体和 fold 3 变差，最关键 family 也变差。
- 下一步应先做 fold 3 的交叉误差分析，或者单独分析 `SCHOOL AND OFFICE SUPPLIES`，不要继续盲目增强 broad low-demand 特征。

#### 阶段 15：fold 3 交叉误差分析

- 新增 `src/store_sales/fold3_cross_error.py`，用于比较 fold 3 和 prior folds 的分组误差差异。
- 新增 `reports/fold3_cross_error/fold3_cross_error_report.md` 和对应 CSV 表。
- 分析维度包括：
  - family
  - store
  - promotion bin
  - family-store
  - family-promotion
  - store-promotion
  - family-store-promotion
  - fold 3 新出现的组合

结果：

- fold 3 RMSLE：`0.423002`。
- prior folds RMSLE：`0.391024`。
- 最大 family 变差来源：`SCHOOL AND OFFICE SUPPLIES`。
- 最大 store 变差来源：store `47`，Quito，type A。
- 最大 promotion bin 变差来源：`11-50`。
- 最大 family-store 变差组合：`SCHOOL AND OFFICE SUPPLIES` at store `47`。
- 最大 fold 3 新组合：`SCHOOL AND OFFICE SUPPLIES` at store `47` with promotion bin `11-50`。

结论：

- fold 3 变差的最强诊断线索集中在 `SCHOOL AND OFFICE SUPPLIES`、高促销 bin `11-50` 和 type A/Quito-Ambato 门店组合，模型在这些子集上明显低估。
- 这还不能证明具体原因；下一步应单独分析 `SCHOOL AND OFFICE SUPPLIES` 的时间规律、促销规律和门店规律。

#### 阶段 16：SCHOOL AND OFFICE SUPPLIES 单独分析

- 新增 `src/store_sales/family_focus_analysis.py`，用于对单个 family 做时间、促销、门店和 fold 3 错误交叉分析。
- 生成 `reports/family_focus/school_office_supplies/family_focus_report.md`，以及配套 CSV 表和图表。
- 本次只做诊断，不改变模型、不生成新提交文件。

结果：

- `SCHOOL AND OFFICE SUPPLIES` 在 2017 年 8 月总销量为 `50169`，明显高于 2017 年 7 月的 `8797`。
- 该 family fold 3 RMSLE 为 `0.866511`。
- fold 3 mean actual sales 为 `59.947917`，mean predicted sales 为 `18.501496`。
- 最强新错误组合是 store `47`，Quito，type A，promotion bin `11-50`，平均真实销量约 `538.4`，平均预测约 `33.6`。
- test period 中 store `44/47/48/50` 等 type A 门店仍有高促销，因此这个 family 对最终提交存在持续风险。

结论：

- 这不是一个适合继续用 broad low-demand 特征解决的问题。
- 当前证据更支持“该 family 在 fold 3 的高促销 type A/Quito-Ambato 门店样本被明显低估”。
- 下一步实验应该做窄特征，例如 school-supplies 的 8 月时间特征、family-promotion interaction、type A 门店交互特征。
- “开学季”只能作为待验证假设，不能直接写成已证明的外部原因。
- 外部业务原因仍不能直接下结论；报告只证明数据模式和模型误差集中位置。

#### 阶段 17：特征实验 2，school supplies August/promotion features

- 新增 `school_supplies_aug_promo` feature profile。
- 新增 `src/store_sales/feature_experiment_report.py`，用于对比 baseline 与 feature experiment 的 validation、target family 和 fold 3 store-promotion 误差。
- 运行 3 窗口验证，输出目录为 `artifacts/experiments/histgbdt_school_supplies_aug_promo_v1`。
- 生成 `reports/feature_experiments/school_supplies_aug_promo_v1/experiment_report.md` 和对应 CSV 表。

结果：

- baseline mean RMSLE：`0.401601`。
- school supplies v1 mean RMSLE：`0.398186`。
- baseline fold 3 RMSLE：`0.423002`。
- school supplies v1 fold 3 RMSLE：`0.412684`。
- `SCHOOL AND OFFICE SUPPLIES` fold 3 RMSLE 从 `0.866511` 降到 `0.688222`。
- store `47` + promotion bin `11-50` 的 predicted mean 从 `33.6` 提高到 `96.8`，actual mean 为 `538.4`。

结论：

- 当前本地验证结果支持 targeted feature 比 broad low-demand 更值得作为候选方向。
- 该 profile 可以保留为 candidate，但不能直接替换 default baseline。
- 下一步应生成该 profile 的 submission，提交 Kaggle 并和 baseline public score `0.58410` 对比。
- 由于特征设计来自 fold 3 错误分析，需要警惕 validation selection bias；如果 public score 不改善，说明它可能只是贴合本地 fold 3。

#### 阶段 18：school supplies v1 Kaggle public score

- 使用 `school_supplies_aug_promo` 生成 submission。
- 提交文件：`artifacts/submissions/school_supplies_aug_promo_v1/submission.csv`。
- Kaggle public score：`0.59096`。
- baseline public score：`0.58410`。

结论：

- 这次 public score 比 baseline 更差，不能替换 default baseline。
- 本地 validation 从 `0.401601` 改善到 `0.398186`，但 public score 从 `0.58410` 变差到 `0.59096`，说明本地 fold 3 改善没有泛化。
- 这是一个明确的 validation selection bias 案例：根据 fold 3 暴露的问题设计特征，再用 fold 3 改善作为核心证据，会高估真实 leaderboard 效果。

下一步：

- 当时最佳提交仍是 baseline。
- 不继续沿 `school_supplies_aug_promo` 加强。
- 后续优先改进验证设计，或尝试更稳健的模型/全局特征方案。

#### 阶段 19：August / pre-test historical validation

- 新增显式 validation windows 能力：`--validation-window YYYY-MM-DD:YYYY-MM-DD`。
- 新增 `src/store_sales/validation_window_report.py`，用于比较多个 run 在同一组窗口上的表现。
- 使用 `train_start_date=2013-01-01`，因为 2014 年窗口需要 2013 年历史数据生成 lag/rolling 特征。

验证窗口：

- `2014-08-16` 到 `2014-08-31`
- `2015-08-16` 到 `2015-08-31`
- `2016-08-16` 到 `2016-08-31`
- `2017-07-31` 到 `2017-08-15`

结果：

- `histgbdt_baseline` mean RMSLE：`0.490514`。
- `histgbdt_school_supplies_aug_promo` mean RMSLE：`0.486425`。
- 两个 run 的 worst fold 都是 fold 3，也就是 `2016-08-16` 到 `2016-08-31`。
- 在四个窗口上，`school_supplies_aug_promo` 都略优于 baseline。

结论：

- August / pre-test windows 没有筛掉 `school_supplies_aug_promo`。
- 这说明“历史 8 月窗口”能补充验证，但仍不足以预测 Kaggle public score。
- 之后不能只依赖 mean RMSLE；需要增加 public-like 切片检查，例如非目标 family 副作用、promotion bin 分布、store/family 分组漂移。

相关报告：

- `reports/validation/august_windows/validation_window_report.md`

#### 阶段 20：public-like stability slice checks

- 新增 `src/store_sales/stability_slice_report.py`。
- 基于 August / pre-test validation artifacts，对 `histgbdt_baseline` 和 `histgbdt_school_supplies_aug_promo` 做稳定性切片检查。
- 检查范围：
  - target vs non-target family
  - family-level side effects
  - promotion bin stability
  - validation/test family-promotion distribution drift
  - test-overweighted non-target regressions

结果：

- target family RMSLE 从 `0.681330` 降到 `0.599242`，改善明显。
- non-target families 整体 RMSLE 从 `0.493954` 降到 `0.493476`，表面略好。
- 但拆到 family 后，有 `16` 个非目标 family 变差。
- 变差最大的非目标 family 是 `DELI`，RMSLE delta `+0.007368`。
- `PERSONAL CARE + 11-50`、`DAIRY + 11-50`、`BREAD/BAKERY + 11-50` 在 test 中占比更高，同时这些具体切片本地已经变差。

结论：

- 这解释了为什么 mean validation 变好但 public score 变差：target family 的大幅改善掩盖了非目标 family 的局部回退，而 test 的 promotion 分布又放大了部分真实回退切片。
- 后续 feature profile 必须增加稳定性门槛：非目标 family 回退数量、promotion bin 回退、test-overweighted regression slices。

相关报告：

- `reports/validation/august_windows/stability_slices/stability_slice_report.md`

#### 阶段 21：global model / feature comparison

- 目标：在放弃 `school_supplies_aug_promo` 局部补丁后，检查是否存在更稳健的全局特征或模型方案。
- 对比对象：
  - `seasonal_naive`
  - `ridge_baseline`
  - `histgbdt_compact`
  - `histgbdt_baseline`
  - `histgbdt_extended`
- 验证方式：继续使用 August / pre-test explicit windows，并保持 `train_start_date=2013-01-01` 与 16 天 recursive forecast。
- LightGBM 本轮没有运行，因为当前环境没有安装 `lightgbm`。

结果：

- `histgbdt_baseline` mean RMSLE：`0.490514`，仍是当前最稳方案。
- `histgbdt_compact` mean RMSLE：`0.492959`，fold 1 变好，但 fold 2/3/4 变差。
- `histgbdt_extended` mean RMSLE：`0.500922`，fold 1/3/4 变好，但 fold 2 大幅变差。
- `seasonal_naive` mean RMSLE：`0.624068`，弱于 tree baseline，只能作为参照或后续 blending 候选。
- `ridge_baseline` mean RMSLE：`2.892314`，在当前 ordinal categorical encoding + linear setup 下不可用。

结论：

- 本轮没有发现比 `histgbdt_baseline` 更稳的全局特征或模型方案。
- 不生成新的 Kaggle submission；当时 best submission 仍是 baseline public score `0.58410`。
- 下一步如果继续模型方向，应优先尝试 LightGBM，或做 baseline 与 seasonal/lag benchmark 的简单 blending。
- 后续实验保留标准仍要结合 stability slice checks，不能只看 mean RMSLE。

相关报告：

- `reports/validation/august_global_models/validation_window_report.md`

#### 阶段 22：simple prediction blending

- 目标：在不新增特征、不重新训练模型的情况下，测试简单 prediction blending 是否能提升稳定性。
- LightGBM 状态：当前环境没有安装 `lightgbm`，本轮未运行 LightGBM 训练。
- 新增工具：`src/store_sales/blend_validation.py`，用于读取两个 validation run 的 fold predictions 并按权重做加权平均。

实验 1：`histgbdt_baseline + seasonal_naive`

- 结果：失败。
- 最轻量的 `99% baseline + 1% seasonal_naive` mean RMSLE 为 `0.495169`，差于 baseline `0.490514`。
- 决策：不保留，不生成 submission。

实验 2：`histgbdt_baseline + histgbdt_extended`

- 最优权重：`55% baseline + 45% extended`。
- mean RMSLE：`0.490514 -> 0.486839`。
- worst fold RMSLE：`0.656282 -> 0.645720`。
- fold 1/3/4 改善，但 fold 2 回退 `+0.009239`。

stability checks：

- target family 略差：`0.681330 -> 0.681433`。
- non-target families 整体改善：`0.493954 -> 0.489896`。
- 仍有 `7` 个非目标 family 变差。
- test-overweighted non-target regression slices 仍有 `15` 个。

结论：

- `baseline + extended` blending 是一个有信号但有风险的 validation candidate。
- 由于存在 fold 2 回退和 public-like 切片风险，本轮不生成 Kaggle submission。
- 当时 best submission 仍是 baseline public score `0.58410`。

相关报告：

- `reports/validation/august_blending/blend_report.md`
- `reports/validation/august_blending_baseline_extended/blend_report.md`
- `reports/validation/august_blending_baseline_extended/stability_slices/stability_slice_report.md`

#### 阶段 23：LightGBM baseline validation

- 目标：安装 LightGBM 后，直接用现有 baseline feature profile 跑同一组 August / pre-test explicit windows。
- 环境：`lightgbm==4.6.0`。
- 运行方式：`--model-type lightgbm --feature-profile baseline --skip-submission`。

结果：

- `lightgbm_baseline` mean RMSLE：`0.486767`。
- `histgbdt_baseline` mean RMSLE：`0.490514`。
- `blend_histgbdt_baseline_histgbdt_extended_base_w550` mean RMSLE：`0.486839`。
- LightGBM 是当前 August / pre-test windows mean RMSLE 最低的模型。

fold 对比：

- fold 1 回退：`+0.048240`。
- fold 2 回退：`+0.040950`。
- fold 3 改善：`-0.073167`。
- fold 4 改善：`-0.031013`。
- worst fold 从 `0.656282` 降到 `0.583115`。

stability checks：

- target family RMSLE：`0.681330 -> 0.572111`。
- non-target families 整体 RMSLE：`0.493954 -> 0.489086`。
- 但仍有 `13` 个非目标 family 变差。
- test-overweighted non-target regression slices 有 `8` 个。

结论：

- LightGBM 是当前最有价值的新候选模型。
- 但由于 fold 1/2 回退和非目标切片风险，本轮还不直接替换 baseline。
- 已生成 LightGBM candidate submission：`artifacts/submissions/lightgbm_baseline_v1/submission.csv`。
- submission 已通过本地格式校验：行数/id 顺序与 `sample_submission.csv` 一致，无重复、缺失、负数或非有限值。
- 下一步应上传 Kaggle 并记录 public score，再决定是否替换 baseline。

相关报告：

- `reports/validation/august_lightgbm/validation_window_report.md`
- `reports/validation/august_lightgbm/stability_slices/stability_slice_report.md`

#### 阶段 24：LightGBM Kaggle public score

- 提交文件：`artifacts/submissions/lightgbm_baseline_v1/submission.csv`。
- Kaggle public score：`0.50834`。
- 对比原 baseline public score：`0.58410`。
- 对比 `school_supplies_aug_promo` public score：`0.59096`。

结论：

- LightGBM baseline 成为当前 best submission。
- 本地 August / pre-test validation mean RMSLE 也支持这个方向：`0.486767` 优于 `histgbdt_baseline` 的 `0.490514`。
- 但 LightGBM 在 fold 1/2 回退，且仍有非目标 family 和 test-overweighted regression slices 风险。
- 下一步优化应围绕 LightGBM 做更稳健的参数收缩、early stopping 或 family/promotion 稳定性约束，而不是盲目增加复杂特征。

## 日志模板

后续可以直接复制下面这段继续追加：

```md
### YYYY-MM-DD

#### 阶段 X：标题

- 目标：
- 改动：
- 结果：
- 风险/问题：
- 下一步：

相关提交：

- `commit_hash` `commit message`
```

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

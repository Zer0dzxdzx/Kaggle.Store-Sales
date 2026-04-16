# Store Sales 数据表阅读记录

## 阅读目标

本阶段目标不是建模，而是判断每张表在比赛中的角色：

- 它表达什么业务信息
- 预测未来时是否已知
- 能否直接作为特征使用
- 是否存在数据泄漏风险

## 数据表总览

| 文件 | 行数 | 日期范围 | 主键/粒度 | 预测时是否已知 | 建模角色 |
| --- | ---: | --- | --- | --- | --- |
| `train.csv` | 3,000,888 | 2013-01-01 到 2017-08-15 | `date + store_nbr + family` | 历史已知，未来未知 | 训练目标与历史特征来源 |
| `test.csv` | 28,512 | 2017-08-16 到 2017-08-31 | `date + store_nbr + family` | 已知 | 待预测样本与未来促销信息 |
| `sample_submission.csv` | 28,512 | 无日期列 | `id` | 已知 | 提交格式模板 |
| `stores.csv` | 54 | 无日期列 | `store_nbr` | 已知 | 门店静态画像 |
| `oil.csv` | 1,218 | 2013-01-01 到 2017-08-31 | `date` | 测试期可对齐 | 外部经济变量 |
| `holidays_events.csv` | 350 | 2012-03-02 到 2017-12-26 | `date + locale + locale_name + description` | 测试期可对齐 | 节假日与事件特征 |
| `transactions.csv` | 83,488 | 2013-01-01 到 2017-08-15 | `date + store_nbr` | 未来未知 | 历史门店客流代理特征 |

## 核心概念补充

### 什么是 merge

`merge` 是按共同字段把两张表拼起来，类似 Excel 的 `VLOOKUP` 或数据库里的 `JOIN`。

主表 `train.csv` 和 `test.csv` 只有：

- `date`
- `store_nbr`
- `family`
- `sales`，仅 train 有
- `onpromotion`

但门店城市、门店类型、油价、节假日等信息在其他表里。模型无法自动知道这些信息，必须把它们按 key 合并到主表上，才能作为特征使用。

例如 `stores.csv` 可以按 `store_nbr` merge：

| date | store_nbr | family | sales |
| --- | ---: | --- | ---: |
| 2017-08-01 | 1 | BEVERAGES | 1000 |

`stores.csv` 中：

| store_nbr | city | state | type | cluster |
| ---: | --- | --- | --- | ---: |
| 1 | Quito | Pichincha | D | 13 |

merge 后：

| date | store_nbr | family | sales | city | state | type | cluster |
| --- | ---: | --- | ---: | --- | --- | --- | ---: |
| 2017-08-01 | 1 | BEVERAGES | 1000 | Quito | Pichincha | D | 13 |

这样模型才能学习不同城市、不同门店类型、不同 cluster 的销售模式差异。

### 哪些表适合怎么 merge

| 表 | merge key | 是否可直接 merge | 原因 |
| --- | --- | --- | --- |
| `stores.csv` | `store_nbr` | 可以 | 门店静态信息，预测未来时已知 |
| `oil.csv` | `date` | 可以，但要处理缺失和滚动方向 | 油价覆盖测试期，是外生变量 |
| `holidays_events.csv` | National 按 `date`，Regional 按 `date + state`，Local 按 `date + city` | 可以，但不能粗暴处理 | 节假日未来已知，但影响范围不同 |
| `transactions.csv` | 不能直接按未来 `date + store_nbr` merge | 不可以直接 merge | 未来真实交易量未知，直接 merge 会泄漏 |

### 什么是数据泄漏

数据泄漏是指：训练或验证时使用了真实预测场景中不可能提前知道的信息。

泄漏会导致：

- 本地验证分数虚高
- Kaggle 提交分数明显变差
- 实验结论不可信

在 Store Sales 中，合法信息和泄漏信息的边界如下：

| 场景 | 合法信息 | 泄漏信息 |
| --- | --- | --- |
| 预测 2017-08-16 sales | 日期、星期、门店信息、测试集 `onpromotion`、历史 sales、已知节假日、已知油价 | 2017-08-16 真实 sales、2017-08-16 真实 transactions |
| 验证 2017-07-31 sales | 2017-07-30 及以前的数据 | 2017-07-31 当天真实 sales 或真实 transactions |

泄漏的本质不是“这个字段有没有用”，而是“预测当下是否已经知道这个字段”。越接近目标结果的字段，越容易造成泄漏。

### 为什么 transactions 最容易泄漏

`transactions.csv` 记录的是某门店某天真实交易次数。它和销售额高度相关，因此很有预测价值。

问题在于，真实预测未来时无法提前知道未来当天的交易次数。

错误用法：

```text
2017-08-16 真实 transactions -> 预测 2017-08-16 sales
```

这是泄漏，因为真实提交时没有 2017-08-16 的真实 transactions。

正确用法：

```text
用 2017-08-15 及以前的 transactions，计算门店历史均值、星期均值、月份均值，再用于预测 2017-08-16。
```

也就是说，transactions 可以用，但只能以历史聚合形式使用。

### 测试期 onpromotion 更高意味着什么

本地数据统计显示：

- 训练期 `onpromotion` 均值约 `2.60`
- 测试期 `onpromotion` 均值约 `6.97`

这说明测试期促销强度明显高于训练期平均水平。

可能影响：

- 模型必须学好 `onpromotion` 和 `sales` 的关系。
- 如果训练集中高促销样本不足，模型可能无法稳定预测测试期高促销场景。
- 不同 family 对促销的响应可能不同，因此后续应分析 `family + onpromotion` 的交互。
- 这是一种 train-test distribution shift，需要在误差分析中重点检查高促销样本。

## 逐表阅读

### `train.csv`

字段：

- `id`
- `date`
- `store_nbr`
- `family`
- `sales`
- `onpromotion`

业务含义：

- 这是监督学习主表。
- 一行表示某一天、某家门店、某个商品家族的销售情况。
- `sales` 是目标变量。
- `onpromotion` 是当天该门店该 family 的促销商品数量。

关键统计：

- 日期范围：2013-01-01 到 2017-08-15
- 门店数：54
- family 数：33
- `sales` 最小值：0.0
- `sales` 最大值：124,717.0
- `sales` 均值：357.78
- 零销量行比例：31.30%
- `onpromotion` 均值：2.60
- `onpromotion` 最大值：741

使用方式：

- 用于训练模型。
- 用历史 `sales` 构造 lag、rolling mean、rolling std。
- 用历史 `onpromotion` 构造促销 lag 和 rolling sum。

泄漏风险：

- 验证或测试时不能使用未来真实 `sales` 生成 lag。
- 任何基于 `sales` 的聚合特征都必须只用当前预测日期之前的数据。

### `test.csv`

字段：

- `id`
- `date`
- `store_nbr`
- `family`
- `onpromotion`

业务含义：

- 这是未来待预测样本。
- 没有 `sales`，需要模型预测。
- 覆盖 2017-08-16 到 2017-08-31，共 16 天。
- 每天有 `54 * 33 = 1,782` 行。

关键统计：

- 行数：28,512
- 日期数：16
- 门店数：54
- family 数：33
- `onpromotion` 均值：6.97
- `onpromotion` 最大值：646

使用方式：

- 作为最终预测和提交的输入。
- `date`、`store_nbr`、`family`、`onpromotion` 都是预测时已知字段。

判断：

- `test.csv` 的 `onpromotion` 均值明显高于训练集均值，说明测试期促销强度可能更高。
- 后续误差分析需要关注高促销样本是否预测稳定。

泄漏风险：

- `test.csv` 没有 `sales`，本身不会泄漏目标。
- 但如果为了构造测试特征而错误使用未来真实销量或未来真实 transactions，就会泄漏。

### `sample_submission.csv`

字段：

- `id`
- `sales`

业务含义：

- 这是 Kaggle 提交格式模板。
- 只要求提交 `id` 和预测的 `sales`。

使用方式：

- 用于确认提交行数和列名。
- 最终提交文件必须保持同样结构。

判断：

- 提交时不需要 `date`、`store_nbr`、`family`。
- 但本地生成预测时必须保留这些字段用于对齐和递归预测，最后再只输出 `id,sales`。

### `stores.csv`

字段：

- `store_nbr`
- `city`
- `state`
- `type`
- `cluster`

业务含义：

- 门店静态属性表。
- `city` 和 `state` 可用于匹配 Local / Regional 节假日。
- `type` 和 `cluster` 表示门店类别或分群。

关键统计：

- 门店数：54
- 城市数：22
- 州/省数：16
- 门店 type 数：5
- cluster 数：17

使用方式：

- 可以直接按 `store_nbr` merge 到 train/test。
- 适合作为静态类别特征。
- 项目代码中应将 `type` 重命名为 `store_type`，避免和 holidays 的 `type` 字段混淆。

泄漏风险：

- 基本无泄漏风险，因为是静态门店信息。
- 它可以直接 merge 到 train/test，因为预测未来时已经知道每家门店的城市、州、类型和 cluster。

### `oil.csv`

字段：

- `date`
- `dcoilwtico`

业务含义：

- 每日油价。
- 厄瓜多尔经济和油价相关，因此油价可能影响消费水平。

关键统计：

- 日期范围：2013-01-01 到 2017-08-31
- 行数：1,218
- `dcoilwtico` 缺失值：43

使用方式：

- 按日期 merge 到 train/test。
- 缺失值需要插值或前后填充。
- 可以构造油价原始值、变化量、滚动均值。

判断：

- `oil.csv` 覆盖到测试期，因此测试期油价可以对齐使用。
- 但油价不是直接销售数据，只能作为外生解释变量。

泄漏风险：

- 使用测试期油价本身通常是合法的，因为官方提供了测试期日期对应数据。
- 如果构造滚动油价特征，要确认不会用到当前日期之后的油价。

### `holidays_events.csv`

字段：

- `date`
- `type`
- `locale`
- `locale_name`
- `description`
- `transferred`

业务含义：

- 节假日和事件表。
- `locale` 表示影响范围：
  - `National`
  - `Regional`
  - `Local`
- `locale_name` 对 Regional / Local 很重要，用于匹配 `state` 或 `city`。
- `transferred=True` 表示节假日被转移，不能简单当作当天真实节假日。

关键统计：

- 日期范围：2012-03-02 到 2017-12-26
- 类型数量：
  - `Holiday`: 221
  - `Event`: 56
  - `Additional`: 51
  - `Transfer`: 12
  - `Bridge`: 5
  - `Work Day`: 5
- `locale` 数量：
  - `National`: 174
  - `Local`: 152
  - `Regional`: 24
- `transferred=True` 数量：12

使用方式：

- National 节假日按日期全局 merge。
- Regional 节假日应按 `date + state` 匹配。
- Local 节假日应按 `date + city` 匹配。
- `Holiday`、`Event`、`Work Day`、`Bridge`、`Additional` 最好分开建特征，不宜全部压成一个 `is_holiday`。

泄漏风险：

- 泄漏风险不高，因为节假日表覆盖未来且预测时已知。
- 主要风险是业务含义处理错误，例如把 Local 节假日当成全国节假日。

### `transactions.csv`

字段：

- `date`
- `store_nbr`
- `transactions`

业务含义：

- 某门店某天真实交易量。
- 它可以看作客流量或订单量代理。

关键统计：

- 日期范围：2013-01-01 到 2017-08-15
- 行数：83,488
- 门店数：54

使用方式：

- 不能直接用于测试期逐日预测，因为测试期没有真实 transactions。
- 可以用历史数据构造门店级聚合特征：
  - 某门店历史平均交易量
  - 某门店按星期几平均交易量
  - 某门店按月份平均交易量

泄漏风险：

- 高。
- 验证时如果把验证日期当天的真实 transactions merge 进去，就等于使用未来真实客流量。
- 正确做法是每个验证 fold 只能使用该 fold 训练截止日期之前的 transactions。
- 需要记住：不是 transactions 不能用，而是不能使用预测日期当天或之后的真实 transactions。

## 阶段 1 结论

| 判断 | 结论 |
| --- | --- |
| 主训练目标来自哪张表？ | `train.csv` 的 `sales` |
| 最终要预测哪张表？ | `test.csv` 中每个 `id` 的 `sales` |
| 哪些表可以直接 merge？ | `stores.csv`、合法处理后的 `oil.csv`、合法处理后的 `holidays_events.csv` |
| 哪张表要特别防泄漏？ | `transactions.csv` 和任何由未来 `sales` 生成的特征 |
| 哪个字段是重要的未来已知变量？ | `test.csv` 中的 `onpromotion` |
| 当前最重要的数据现象 | 零销量比例高，测试期促销强度高，节假日有不同影响范围，transactions 不能直接用于未来 |

## 你需要自己复述的问题

1. `train.csv` 和 `test.csv` 的区别是什么？
2. merge 是为了什么？请用 `stores.csv` 举例。
3. 为什么 `stores.csv` 可以直接 merge？
4. 为什么 `holidays_events.csv` 不能只做一个简单的 `is_holiday`？
5. 什么是数据泄漏？为什么它会让本地验证分数不可信？
6. 为什么 `transactions.csv` 是最容易泄漏的表？
7. 为什么 `transactions.csv` 不能直接按日期 merge 到验证集或测试集？
8. 测试期 `onpromotion` 均值比训练期高，这可能对模型有什么影响？

# MySQL → 达梦 DM8 · 信创离线适配（转换器方案）

> 类型：信创数据库迁移 · 工程化适配
> 时间：2026 上半年（与国产化 K8s 交付同一条信创主线）
> 源目录：`delopy/atomic/`、`delopy/mcp/`（转换器与产物 SQL 均在源目录，本仓只沉淀口径）
> 关联：[`../01-K8s-Troubleshooting/cases/kylin-offline-k8s-v1.26/`](../01-K8s-Troubleshooting/cases/kylin-offline-k8s-v1.26/)（同一套离线内网环境）

---

## 1. 做了什么 / 为什么

| 项 | 内容 |
|----|------|
| 背景 | 信创内网交付：数据库必须从 MySQL 换成达梦 DM8，机器全离线，无公网工具可用 |
| 问题 | 十几套表 + 大量初始化 INSERT（dp_ao 320KB、全量备份 4.8MB），手工改 SQL 不可行也不可验证 |
| 方案 | 自写 **Python 规则转换器**（`mysql_to_dm_converter.py`，约 800 行）：MySQL dump 进 → DM8 兼容 SQL 出，带**输出自校验** |
| 覆盖 | `dp_ao.sql→dp_ao-dm.sql`、`mcp_init_dm.sql`、`atomic-center.sql→atomic-center-dm.sql`；配套保留字清单 `_dm_reserved_words.txt` |
| 应用侧 | `kaihong.db.type=dm` / `spring.profiles.active=local,dm` 切数据源，业务代码不动 |

## 2. 核心转换规则（面试可讲的「设计」）

| MySQL 写法 | 达梦处理 | 原因 |
|------------|----------|------|
| `AUTO_INCREMENT` 主键 | `IDENTITY(1,1)`；带显式 id 的 INSERT 前后包 `SET IDENTITY_INSERT ON/OFF` | 语义映射，漏包必报错 |
| 表尾 `ENGINE=... CHARSET=...` | 整段剥离 | 达梦无此语法 |
| 内联 `KEY/UNIQUE KEY` | 拆成独立 `CREATE INDEX` | 达梦不支持建表内联索引 |
| `LOCK/UNLOCK TABLES`、`/*!40000` 条件注释、`USE`/`CREATE DATABASE` | 剔除 | MySQL 专属 |
| `''` 空串插入 NOT NULL 字符串列 | 改写为合法值/NULL 化（`fix_dm_empty_strings`） | **达梦把 '' 当 NULL**，与 MySQL 最大语义差异 |
| `` ` `` 反引号、`@` 会话变量 | 去引号；变量解析为字面量 | 达梦不认 |
| VALUES 大元组拆行 | 引号感知的安全切分 | 逗号在字符串里不能当分隔符 |
| 业务特例（mcp server_random / tool short_code 跨表 id） | 生成子查询替换字面量 | dump 里硬编码 id 换库后对不上 |

**自校验**（`validate_output`）：产物里残留 `ENGINE=InnoDB`、未转换语句 → 直接报错退出，不交付半成品。

## 3. 关键坑（每条都能被追问）

1. **'' 即 NULL**：MySQL 里空串能进 NOT NULL 列，达梦直接违反约束 → 按「表 × NOT NULL 字符串列」扫描改写
2. **显式 id INSERT**：迁移数据都带原 id，`IDENTITY` 列不包 `IDENTITY_INSERT` 必失败；漏写 `OFF` 会污染后续插入
3. **MySQL `#` 注释不以分号结尾**：朴素按 `;` 切分语句会把注释和下一条 SQL 吞成一条 → 预处理先剔 `#` 行
4. **保留字**：达梦保留字比 MySQL 多（清单驱动替换），报错点离根因很远，靠清单前置防御
5. **执行入口**：disql / SQLark 执行，**空库/测试库先验证**再上交付库

## 4. 结果 / 验收

- 三套 DM8 全量初始化脚本一次生成、可重复生成（源 SQL 更新 → 一条命令重转）
- 转换器 + 保留字清单纳入离线交付物料，换项目复用
- 验收：DM8 空库执行 0 报错 → 应用 `db.type=dm` 启动 → 关键表行数与 MySQL 对账一致

## 5. 面试口径

**30 秒**：
> 信创项目要把 MySQL 全量库迁到达梦 DM8，机器全离线没法用现成工具。我写了一个带自校验的 Python 规则转换器，处理 AUTO_INCREMENT 转 IDENTITY、空串当 NULL、内联索引拆独立 DDL 这些语义差异，三套库的初始化脚本一次生成，空库执行零报错，应用侧加个 db.type 开关就完成切换，后续源 SQL 更新一条命令重转。

**追问预判**：
- 「达梦和 MySQL 最大差异」→ 空串=NULL + IDENTITY + 保留字，举 '' 进 NOT NULL 列的坑
- 「怎么保证转换对」→ 转换器自校验 + 空库试跑 + 行数对账，不靠人眼
- 「为什么不用工具」→ 离线环境装不了第三方工具；规则转换器可重复、可审计、可复用
- 「和应用怎么衔接」→ hsweb/配置层 `db.type=dm` + profile 切数据源，业务代码零改动

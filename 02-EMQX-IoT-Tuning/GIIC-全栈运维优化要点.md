# GIIC 全栈运维优化要点（面试用 · 脱敏）

> **现网原文（只读）**：`D:\gerrit\iot-server\docs\ops\`  
> - [`GIIC高并发全栈优化说明.md`](file:///D:/gerrit/iot-server/docs/ops/GIIC高并发全栈优化说明.md)（管理层一页纸）  
> - [`nginx-tcp-proxy-tuning.md`](file:///D:/gerrit/iot-server/docs/ops/nginx-tcp-proxy-tuning.md) + `config/nginx-tcp-sysctl.conf`  
> - [`mysql-production-tuning.md`](file:///D:/gerrit/iot-server/docs/ops/mysql-production-tuning.md) + `config/prod-*-mysqld.cnf`  
> **关联证据**：[`GIIC-15万压测参与复盘.md`](GIIC-15万压测参与复盘.md)  
> **角色**：运维/入口/库侧 **协助对齐与文档沉淀**；与 Java 协议/网关改造 **同属 15W 闭环**，勿只讲 jar。

---

## 0. 30 秒口述

15 万长连接不是只改业务 jar。入口要调 **内核临时端口 + Nginx TCP 代理**（防 errno 99、防上游雪崩），库要按内存选档并和 **连接池联动**；应用侧再做 per-connection / L1 / Token。三层缺一，高峰就会在入口或 MySQL 露底。

---

## 1. 三层一张图

```text
设备/压测机
  → 入口 Nginx（TCP Stream 代理）+ 宿主机 sysctl
      → 多节点 iot-server（GIIC 网关/协议）
          → 共用 MySQL（生产档 cnf）+ Redis
```

| 层 | 典型症状（调前） | 手段（调后） | 不改什么 |
|----|------------------|--------------|----------|
| **内核** | 临时端口耗尽、握手丢、长连接空闲后发得慢 | `ip_local_port_range`、somaxconn/backlog、`tcp_slow_start_after_idle=0`、file-max 等（宿主机持久化） | 业务协议 |
| **Nginx** | `Cannot assign requested address`；`no live upstreams`；压测机少 IP 打爆单后端 | 容器放宽出站端口 + nofile；`hash $remote_addr$remote_port`；`max_fails` 放宽；大 backlog / proxy_timeout | 报文内容 |
| **MySQL** | 连接顶满、热表反复读盘 | 按内存选 **prod-128g / 64g / test-4g**；buffer pool + `max_connections` 与应用池公式联动；**不关**刷盘换吞吐 | SQL 语义 |

---

## 2. Nginx / 内核（面试记 5 点）

1. **Docker bridge**：只调宿主机不够，容器 namespace也要出站端口；Docker 28+ 多数 sysctl 只能放宿主机。  
2. **errno 99**：代理侧 ephemeral port 耗尽 → 拉大 `ip_local_port_range` + nofile。  
3. **粘滞**：`$remote_addr`  alone 会让少数压测机 IP 打爆单节点 → 用 **`$remote_addr$remote_port`**。  
4. **摘流**：`max_fails` 过小 → 四台一起 disabled；放宽容忍、缩短 fail_timeout。  
5. **硬上限**：单入口单 IP 代理连接约 **6 万级**；再高要 LVS/多入口，不是无限拧参数。

**验收口令**：大规模建连时 Nginx error 不再持续涨「端口耗尽 / no live upstreams」。

---

## 3. MySQL（面试记 4 点）

1. **一套生产参数长期在线**（压测 ≠ 另开「关刷盘」档）。  
2. **按机器内存选档**，不按「今天压 GIIC」单独改一版危险参数。  
3. **`max_connections` > 各节点连接池之和 + 余量**；只加大应用池会把库打满。  
4. GiicHotCache 减读 **不能替代** 容量规划；Login/状态等仍可能打库。

---

## 4. 与 Java 改造怎么分工（防吹）

| 你可讲「我做过 / 对齐过」 | 勿写成 |
|--------------------------|--------|
| 协助入口机 sysctl/Nginx 合入与验收口径 | 「我一个人改了全公司内核」 |
| 推动/对照 MySQL 生产档与连接池公式 | 「我是 DBA owner」 |
| 应用侧 per-connection / L1 / Token（复盘主文） | 只讲应用、假装入口没问题 |

---

## 5. 追问速答

| 问 | 答 |
|----|----|
| 为什么还要调 Nginx？ | 长连接全代理占出站端口；不调会在入口先挂，后端 JVM 还活着 |
| 和应用 profile 什么关系？ | **独立**；sysctl/Nginx 是基础设施长期保留，不是 `application-perf` 开关 |
| 单机入口不够怎么办？ | 架构上 LVS DR / 多入口，不是再调 `worker_connections` 无限涨 |

---

## 6. 同步记录

| 日期 | 动作 |
|------|------|
| 2026-07-23 | 自现网 `docs/ops` 脱敏摘要入库，挂到 15W 复盘与全链路白板 |

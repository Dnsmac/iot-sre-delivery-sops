# 案例：压测期 ES 写入瓶颈（NFS + iot buffer/dead）

> **时间**：2026-08-13  
> **环境**：node130 / k8s meta 压测中  
> **角色**：现场只读排查（MCP 连主机 + ES），给调参与架构建议；**未改现网代码**  
> **会话**：`96cb4a21-a15d-4e39-8858-978dbcadb089`

---

## 1. 现象

- 主机 CPU/内存**未打光**，但 iot-server 与 ES 写入都「很痛」。  
- 临时把 `refresh_interval` 调到 10s **只能缓解一部分**，不是治本。  
- 长跑后出现：ES 查询滞后、iot 侧 `elasticsearch-buffer` 巨大、dead 队列膨胀。

---

## 2. 因果链（面试主线）

```text
压测高写入
  → ES data 落在 NFS（写线程满、CPU 不高 → 等 IO）
  → bulk 超时 / 协调层熔断 / 部分失败
  → iot PersistenceBuffer：活 queue 积压 或 失败进 dead
  → 堆压 / 内存过载保护；主机资源看起来还有余量
```

| 证据点 | 含义 |
|--------|------|
| ES write pool active 打满、CPU 仅数核 | **等 IO**，不是算力不够 |
| data path → `nfs_share/...elasticsearch-data` | 存储介质天花板 |
| 每 pod `*.queue` ~30G+（高峰合计 ~155GB） | 应用侧缓冲爆 |
| 长跑 `*.queue.dead` 每 pod ~26G | 失败永久堆 NFS，不回 ES |
| `hasFailures` → 代码整批 requeue | 部分失败会整批重试，加重 ES |
| `replicas=1` | 写放大 ×2 |

---

## 3. 建议分层（可讲清取舍）

| 优先级 | 动作 | 作用 |
|--------|------|------|
| **长期** | ES data **离开 NFS** → 本地 SSD | 治本 |
| **压测临时** | 热索引 `replicas=0` + `refresh_interval` 加大或 `-1` | 减写放大/刷新 IO |
| **应用** | 消化 buffer；评估降采样/限流；改「只重试失败项」（需改代码） | 防止 ES 恢复后继续灌爆 |
| **节点** | 腾空转占内存的 BestEffort Pod；iot 与 ES data 反亲和 | 减同机争抢 |

---

## 4. 30 秒口述

> 压测时主机资源看着还有，其实写入已经堵死：ES 数据盘在 NFS 上，写线程在等 IO；iot 侧本地 elasticsearch-buffer 堆到几十 GB，失败还会进 dead。调 refresh 只能减轻刷新，真正要换盘或压测期关副本；应用侧还要防止整批失败整批重试把 ES 打得更惨。

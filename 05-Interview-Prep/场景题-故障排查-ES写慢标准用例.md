# 场景题 · 故障排查 · ES 写慢（复用模板的第 3 实例 · 故障型）

> **模板**：[`场景题-容量预估L4-GIIC15W标准用例.md`](场景题-容量预估L4-GIIC15W标准用例.md) —— 故障型用 **Step F0→F5**，**不混用**容量 Step 0→6。
> **案例**：[`es-nfs-write-bottleneck-2026-08`](../02-EMQX-IoT-Tuning/cases/es-nfs-write-bottleneck-2026-08/README.md)
> **登记表**：见模板 Step -1 第 3 行。

---

## Step F0 · 现象（⏱ 20s · 1 句 + 数字）

> k8s meta 压测中，主机 **CPU/内存没打满**，但 iot-server 与 ES 写入都「很痛」：ES 查询滞后、iot 侧 `elasticsearch-buffer` 巨大、dead 队列膨胀，每 pod `*.queue` **~30G+**，高峰合计 **~155GB**。

---

## Step F1 · 分层（⏱ 40s · 入口/网关/总线/存储）

```text
压测高写入
  → ES data 落在 NFS（write pool 满、CPU 不高 → 等 IO）
  → bulk 超时 / 协调层熔断 / 部分失败
  → iot PersistenceBuffer：活 queue 积压 或 失败进 dead
  → 堆压 / 内存过载保护；主机资源看着还有余量
```

| 证据点 | 含义 |
|--------|------|
| ES write pool active 打满、CPU 仅数核 | **等 IO**，不是算力不够 |
| data path → `nfs_share/...elasticsearch-data` | 存储介质天花板 |
| `hasFailures` → 代码整批 requeue | 部分失败整批重试，加重 ES |
| `replicas=1` | 写放大 ×2 |

---

## Step F2 · 根因（⏱ 60s · 证据命令）

```bash
# 1. ES 写线程与 CPU 对照 → 等 IO 判断
GET _cat/thread_pool/write?v
GET _cat/nodes?v&h=name,cpu,load_1m

# 2. data 路径确认落在 NFS
# 3. 应用侧 buffer/dead 膨胀量
docker exec <iot-pod> du -sh /data/*.queue* 2>/dev/null
```

**根因一句**：ES data 落在 **NFS**，写线程在等 IO（CPU 不高、pool 满），bulk 超时失败后 iot 侧 buffer/dead 堆到 155GB，且 `hasFailures` 整批重试把 ES 打得更惨。

---

## Step F3 · 止血（⏱ 30s · 临时）

| 动作 | 作用 |
|------|------|
| 热索引 `replicas=0` + `refresh_interval` 加大或 `-1` | 减写放大/刷新 IO |
| 限流 / 降采样，消化 buffer | 防 ES 恢复后继续灌爆 |

---

## Step F4 · 长期 + 边界（⏱ 30s）

| 动作 | 作用 |
|------|------|
| ES data **离开 NFS → 本地 SSD** | 治本 |
| 改「只重试失败项」（需改代码） | 防整批重试 |
| iot 与 ES data **反亲和**；腾 BestEffort Pod | 减同机争抢 |

**边界**：我是**现场只读排查**（MCP 连主机 + ES），给调参与架构建议，**未改现网代码**。

---

## Step F5 · 钩子（⏱ 20s）

```text
「ES NFS 这条是故障型：现象是 CPU 不高但写入痛，根因是等 IO。同一套分层思路，
我 15W GIIC 的 Redis/Sink 热路径也是这么定位的——您想听容量预估还是继续这条故障链？」
```

---

## §7 口播（⏱ 2min）

> 压测时主机资源看着还有，其实写入已经堵死：ES 数据盘在 NFS 上，写线程在等 IO（CPU 不高、pool 满）；iot 侧本地 elasticsearch-buffer 堆到几十 GB，失败还会进 dead，长跑每 pod 26G。调 refresh 只能减轻刷新，真正要换盘或压测期关副本；应用侧还要防止「整批失败整批重试」把 ES 打得更惨。我是现场只读排查，给的是分层建议，没改现网代码。

---

## §8 追问陷阱

| 陷阱 | 标准答 |
|------|--------|
| 「你改 ES 了吗？」 | **只读排查**，建议换盘/关副本，**未改现网代码** |
| 「为什么不加机器？」 | 主机 CPU/内存没满，瓶颈在 **NFS IO**，加机器没用 |
| 「refresh 调到 10s 够吗？」 | 只能**缓解一部分**，不是治本；治本要 SSD |

---

## §9 收工动作（待实测）

| 填哪格 | 命令/动作 |
|--------|-----------|
| 155GB 精确值 | `docker exec <iot-pod> du -sh /data/*.queue*` |
| 换盘后 write pool | `GET _cat/thread_pool/write?v` 对比 |

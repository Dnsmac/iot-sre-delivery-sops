# C3 Broker 调优

> 优先级: **P3 运维** | 预计阅读 35 分钟 | 深度：已深化

## 本章解决什么问题

掌握 **Mosquitto 开发机** 与 **EMQX 生产** 的可调旋钮：连接上限、飞行窗口、心跳、持久化、缓冲区、操作系统内核参数，使延迟与稳定性可预期，而不是默认安装值扛全量流量。

---

## 面试常问

1. `max_inflight_messages` 设太小会怎样？
2. Mosquitto `autosave_interval` 和性能什么关系？
3. EMQX 的 zone 限流解决什么问题？
4. TCP `somaxconn` 和 MQTT 连接风暴有何关系？
5. 调优后如何验证没有引入消息丢失？

---

## 核心知识

### 客户端侧（Paho，与 Broker 协同）

| 参数 | 作用 | 建议 |
|------|------|------|
| `keepAliveInterval` | 心跳周期 | 30～300s，移动网络可略长 |
| `maxInflight` | 未确认 QoS1/2 条数 | 10～100，过高占内存 |
| `automaticReconnect` | 断线重连 | 生产开，配指数退避 |
| `connectionTimeout` | 连接超时 | 10～30s |

### Mosquitto（本仓 `docker/mosquitto.conf`）

```conf
max_connections 1000
message_size_limit 1048576
max_inflight_messages 20
max_queued_messages 1000
autosave_interval 60
persistence true
```

- **`max_queued_messages`**：慢消费者队列，满则可能丢或拒（视版本与策略）。
- **`persistence`**：QoS1/2 与 retain 落盘；磁盘慢则整体延迟升。
- 开发可放宽；生产改 **认证 + ACL** 后再压测。

### EMQX 生产向

- **监听器**：`max_connections`、`max_conn_rate` 防连接风暴。
- **Zone**：按证书/用户名分租户限速（消息速率、字节速率）。
- **会话**：`max_subscriptions`、`max_mqueue_len` 防止单 Client 拖垮节点。
- **飞行窗口**：与 MQTT 5.0 会话过期、流控配合。
- **桥接**：`bridge` 重试间隔、队列长度（见 [C4](C4-bridge.md)）。

### 操作系统

```text
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
fs.file-max = 2097152
# 进程 ulimit -n 与 EMQX systemd LimitNOFILE 一致
```

---

## 生产环境注意点

- 调优 **一次改一类参数**，便于回滚与 A/B。
- 调 `max_inflight` 前确认消费者能跟上，否则只是延迟堆积到客户端。
- EMQX 集群各节点配置 **一致**（除 `node.name`），避免行为分裂。
- 变更后跑 [C11](C11-loadtest-connections.md) 同阶梯对比基线。
- 日志级别生产用 `warning`，排障临时开 `debug` 并限时。

---

## 易错点与反例

1. **Keep Alive 30s + 网络 NAT 60s 超时** — 假在线，Broker 认为仍连接但数据不通。
2. **关闭 persistence 却用 QoS1** — Broker 重启后会话状态丢失。
3. **只调 Broker 不调消费者线程池** — 表现为 Broker CPU 低但 [P4 积压](../04-问题百科/P4-slow-backlog.md)。
4. **max_conn_rate 过小** — OTA 重连合法流量被拒。
5. **容器未调 ulimits** — 连接到 8K 即 `too many open files`。

---

## 动手验证

```powershell
# QoS1 + inflight 观察
mosquitto_pub -h localhost -t dev/tune/qos1 -m "x" -q 1
mosquitto_sub -h localhost -t dev/tune/qos1 -q 1 -C 5

# EMQX（若有）：查看监听器与限流
# curl http://127.0.0.1:18083/api/v5/listeners
```

对比调优前后：`mosquitto_sub -v` 延迟、EMQX Dashboard「消息速率」曲线。

---

## 相关章节

- [C2 容量](C2-capacity.md) | [C5 监控](C5-monitoring.md) | [B10 客户端调优](../02-开发篇/B10-performance-tuning.md)
- [附录 G 配置参考](../附录/G-config-reference.md) | [附录 D](../附录/D-performance-params.md)

# 附录 E：MQTT 排查决策树

> 完整场景剧本见 [B9](../02-开发篇/B9-troubleshooting.md)；Part D 机理见 [INDEX](../04-问题百科/INDEX.md)。

---

## 主树：我遇到了什么？

```
                    ┌─────────────┐
                    │  现象入口    │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      收不到/丢        重复/乱序        断连/慢/吞吐
           │               │               │
           ▼               ▼               ▼
        树 A             树 B             树 C
```

---

## 树 A：收不到 / 丢失

```
收不到或条数少
├─ CLI 同 Broker 同账号能收到？
│   ├─ 否 → topic/ACL/连错 Broker → B9§1, P1, P9
│   └─ 是 → 应用订阅/SUBACK/代码 topic 拼错 → B9§1
├─ QoS0？
│   └─ 是且不能丢 → 改 QoS1 + 幂等 → P1
├─ 需离线却 cleanSession=true？
│   └─ 是 → false + 稳定 ClientId → B9§7, P7
├─ 桥接下游少条？
│   └─ 规则/权限/lag → B9§12, C4
└─ 仅生产不行？
    └─ TLS/ACL/地址 → 附录 I, P9
```

**证据命令：**

```bash
mosquitto_sub -h "$BROKER" -t '<精确topic>' -q 1 -v -d
mosquitto_pub -h "$BROKER" -t '<精确topic>' -m test -q 1 -d
```

---

## 树 B：重复 / 乱序

```
重复消费
├─ QoS1 或重连？ → 是：上幂等 dedup → P2, B9§2
└─ 多消费者同 topic？ → 共享订阅或分区 → B9§2

乱序
├─ 多线程处理 callback？ → 按 deviceId 单线程 → B9§3, P3
├─ 多写者同 topic 无 seq？ → payload 带 seq → P3
└─ 桥接多 worker？ → 分区策略 → P3
```

---

## 树 C：断连 / 慢 / 吞吐低

```
connectionLost / 发不动 / msg/s 低
├─ callback 慢？ → 有界线程池 → B9§4, P4
├─ KeepAlive / NAT / LB？ → 对齐超时 → B9§6, P6
├─ ClientId 冲突？ → 规范命名 → P6
├─ inflight 满 / QoS2 多？ → L0/L3 B10
├─ 订阅 prod/#？ → 收窄 → B9§10, P5
├─ Mosquitto 单机？ → EMQX 集群 → B12
└─ 桥接堆积？ → 规则与下游 → P4, B9§12
```

---

## 树 D：状态与配置类

```
Retain / 遗嘱 / 环境
├─ 新订阅收到陈旧值？ → retain 清除/版本号 → B9§8, P8
├─ 误报离线？ → disconnect / Will Delay → B9§11
└─ 本地 OK 生产失败？ → 附录 I → P9, P10
```

---

## 五步方法论（与 B9 一致）

```
现象 → 划界(客户端/Broker/网络/桥接) → 证据(CLI/日志/$SYS) → 缩小(单变量) → 验证
```

---

## Part D 快速映射

| 现象 | 文档 |
|------|------|
| 丢失 | [P1](../04-问题百科/P1-message-loss.md) |
| 重复 | [P2](../04-问题百科/P2-duplicate.md) |
| 乱序 | [P3](../04-问题百科/P3-out-of-order.md) |
| 积压慢 | [P4](../04-问题百科/P4-slow-backlog.md) |
| 吞吐 | [P5](../04-问题百科/P5-performance.md) |
| 断连 | [P6](../04-问题百科/P6-disconnect.md) |
| 离线 | [P7](../04-问题百科/P7-offline-message.md) |
| Retain | [P8](../04-问题百科/P8-retain.md) |
| 本地vs生产 | [P9](../04-问题百科/P9-local-vs-prod.md) |
| K8s | [P10](../04-问题百科/P10-k8s.md) |

---

## 相关

- [B9 十二场景](../02-开发篇/B9-troubleshooting.md) | [附录 F CLI](F-mosquitto-cli-cheatsheet.md)

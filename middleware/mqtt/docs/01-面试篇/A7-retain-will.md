# A7 Retain、遗嘱与排队的消息

> 优先级: **P1 面试** | 预计阅读 25 分钟 | 深度：已深化 | 学习路径：**D4 | 面试：★★★** | 主路径：[学习路径](../学习路径.md)

## 本章解决什么问题

区分 **Retain**（最后已知值）、**遗嘱 Will**（异常离线通知）与普通 QoS 队列；会配置、会清除脏 Retain，避免遗嘱误触发。

---

## 面试常问

1. Retain 消息是什么？新订阅者会收到几条？
2. 如何清除 Retain？
3. 遗嘱消息什么时候发？
4. Retain 和 QoS 离线队列有什么区别？
5. 遗嘱 QoS 怎么选？

---

## 核心知识

### Retain

- PUBLISH 的 **retain=1** 时，Broker **只保留该主题最后一条** retain 消息。
- **新订阅者** SUBACK 后会 **立即收到** 一条（若存在），用于「当前在线状态、最后温度」等。
- **不是**历史消息队列，只有 **一条**。

清除：向同主题发布 **空 payload** 且 **retain=1**。

### 遗嘱 Will

- 在 **CONNECT** 时注册：主题、payload、QoS、retain。
- 当客户端 **异常断开**（未发 DISCONNECT、TCP 断）时，Broker **代发** 一条 PUBLISH。
- 典型：`device001/status` → `offline`，供平台告警。

### 对比

| | Retain | 遗嘱 | QoS1 离线队列 |
|---|--------|------|----------------|
| 触发 | 每次 retain 发布更新 | 异常断连 | 持久会话+断线 |
| 条数 | 每主题 1 条 | 一次 | 多条（有限） |
| 新订阅 | 立即收 retain | 不直接相关 | 重连后收 |

---

## 面试标准答案

### 题：Retain 和离线消息有什么区别？

> Retain 是 Broker 在每个主题上保存的最后一条标记为 retain 的消息，新订阅者一来就能拿到当前快照，只有一条。离线消息是会话在 Clean Session false 且 QoS1 或 2 时，设备断线期间缓存的队列，重连后按会话投递。一个是状态快照，一个是断线期间的队列，不要混为一谈。

### 题：为什么遗嘱经常误报在线状态？

> 因为应用正常退出时没有发 DISCONNECT，或者进程被 kill，Broker 认为是异常断开就发了遗嘱 offline。运维发布、滚动重启要规范下线流程，或遗嘱主题与业务心跳分离。

---

## 生产环境注意点

- Retain 仅用于 **状态类** 主题，勿对高频遥测开 retain（浪费、易脏）。
- 遗嘱 payload 尽量小；QoS1 + 订阅端幂等。
- 变更固件前 **清 retain** 避免新固件读到旧状态。

---

## 易错点与反例

1. **对每秒遥测开 retain** — 无意义且占存储。
2. **以为 retain 能补历史** — 只有最后一条。
3. **正常 stop 也触发遗嘱** — 未 DISCONNECT。
4. **遗嘱主题与业务 topic 混用 `#` 订阅** — 误收大量告警。

---

## 动手验证

```bash
mosquitto_pub -h localhost -t dev/status -m online -r
mosquitto_sub -h localhost -t dev/status -C 1 -v
# 清除 retain
mosquitto_pub -h localhost -t dev/status -n -r
```

---

## 相关章节

- [A4 报文](A4-packets-connect-flow.md) | [B2 发布](../02-开发篇/B2-publish.md) | [P8 Retain 异常](../04-问题百科/P8-retain.md)

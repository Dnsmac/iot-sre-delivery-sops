# P7 离线期间收不到消息

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- 设备休眠或断网 **几小时后上线**，期望指令未收到。
- 在线时能收，**离线窗口** 消息缺失。
- 换 ClientID 后 **永远收不到** 历史。

## 常见原因

| 原因 | 说明 |
|------|------|
| Clean Session=true | 断线后会话清空 |
| QoS0 | 不缓存离线 |
| 未订阅 | 离线前未 SUBSCRIBE 该主题 |
| 队列上限 | `max_mqueue_len` 满后丢弃 |
| 会话被抢 | ClientID 冲突，旧会话清除 |
| 用 Retain 代替队列 | 仅最后一条 retain，非历史流 |
| 桥接不缓存 | 消息已写 Pulsar 但设备未订 MQTT |

## 排查步骤

1. 确认 **cleanSession** 与 **QoS** 组合（[A6](../01-面试篇/A6-session-keepalive.md)）。
2. 离线前是否已成功 **SUBACK**。
3. EMQX 查看该 ClientID **mqueue** 长度与丢弃计数。
4. 区分 **MQTT 离线缓存** vs **业务需从 Pulsar 补发**。
5. Mosquitto 查 `persistence` 与队列配置（开发对照）。

## 解决

- 必达指令：**QoS1 + cleanSession=false** + 唯一 ClientID。
- 调大 Broker **离线队列**（有上限，需容量评估）。
- 长时间离线：**上线后从 Pulsar/DB 按时间拉取补偿**，不只依赖 MQTT 会话。
- OTA/指令 topic 可配合 **retain** 最新版本（见 [P8](P8-retain.md)）。
- 修 ClientID 冲突与 ACL 导致订阅失败。

## 预防

- 产品定义：**离线多久** 仍要保证；超过则走 AP 拉取。
- 文档写明 MQTT **不是长期消息存储**（对比 Pulsar）。
- 测试用例：断网 N 分钟再连，断言 QoS1 条数。

## 相关链接

- [A6 会话](../01-面试篇/A6-session-keepalive.md) | [A7 Retain/Will](../01-面试篇/A7-retain-will.md)
- [P1 丢失](P1-message-loss.md) | [C3 调优](../03-运维篇/C3-broker-tuning.md)

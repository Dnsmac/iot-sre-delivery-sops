# P6 频繁断连

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- 设备日志 **connection lost**，重连循环。
- Dashboard 连接数 **锯齿波**；CONNACK 成功后又 DISCONNECT。
- 仅移动网络或 **特定机房** 设备出现。
- 升级 Broker 后 **批量掉线**。

## 常见原因

| 原因 | 说明 |
|------|------|
| Keep Alive 超时 | 未发 PINGREQ 或 NAT 超时 |
| ClientID 冲突 | 后连踢前连 |
| LB 空闲超时 | TCP 被中间设备掐断 |
| 认证/ACL 变更 | 重连被拒 |
| Broker 重启/滚动升级 | 预期闪断 |
| 证书/TLS 失败 | 握手失败 |
| 资源限流 | `max_connections`、连接速率限制 |

## 排查步骤

1. 查 **CONNACK 返回码** 与断开原因（MQTT 5.0 reason code）。
2. 对比 **Keep Alive** 与 NAT/LB `idle_timeout`（建议 keepAlive < NAT/2）。
3. 搜是否 **同 ClientID** 多实例（K8s 副本误用固定 ID）。
4. EMQX 日志连接生命周期；Mosquitto `New client`/`Socket error`。
5. 抓包看 **PINGREQ/PINGRESP** 是否规律。
6. 关联变更：升级、证书、ACL（[C9](../03-运维篇/C9-upgrade.md)）。

## 解决

- 启用 **automaticReconnect** + 指数退避；唯一 ClientID（含 deviceId）。
- 调 LB **TCP 保活** 与 idle 至 大于 2×KeepAlive。
- 修复证书链；回滚 ACL。
- 升级用 **滚动** + 设备重连容忍（[C8](../03-运维篇/C8-ha-cluster.md)）。
- 扩容或放宽误伤的 **connect_rate** 限制。

## 预防

- 连接参数表：**Keep Alive、TLS、ClientID** 进配置中心。
- 监控：`connect_rate`、`disconnected` 率、认证失败。
- 演练 Broker 滚动对客户的影响。

## 相关链接

- [A6 会话 Keep Alive](../01-面试篇/A6-session-keepalive.md) | [C10 Runbook](../03-运维篇/C10-failure-runbook.md)
- [P9 本地与生产](P9-local-vs-prod.md) | [P10 K8s](P10-k8s.md)

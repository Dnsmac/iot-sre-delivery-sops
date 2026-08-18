# P8 Retain 消息异常

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- 新订阅者 **立刻收到一条旧数据**（未主动发布）。
- 配置下发 **总是旧版本**。
- 清 retain 后仍出现 **幽灵消息**。
- Broker 磁盘 **retain 堆积**。

## 常见原因

| 原因 | 说明 |
|------|------|
| 误设 retain 标志 | 普通遥测也 retain |
| 空 Payload retain | 部分 Broker 视为清除，行为需确认 |
| 多设备共 topic | 后写覆盖先写 |
| 桥接转发 retain | 启动时灌入下游 |
| 未发清除 | 升级后未 publish retain 空消息清除 |
| persistence | 重启后 retain 仍在（预期） |

## 排查步骤

1. `mosquitto_sub -h <host> -t '<topic>' -v` 看是否 **即时收到**（无 pub 情况下）。
2. 查发布代码 **`setRetained(true)`** 或 `-r` 参数。
3. EMQX Dashboard **Retained 消息** 列表；按主题删除。
4. 确认是否 **通配符订阅** 收到多条 retain。
5. 桥接规则是否 **转发 retain**（[C4](../03-运维篇/C4-bridge.md)）。

## 解决

- 仅 **配置/固件版本/最后已知状态** 使用 retain。
- 更新配置：同 topic **retain 发布新值**；废弃 topic 发 **零长度 retain** 清除。
- 定期审计 retain 主题清单；禁止 `prod/#` 级 retain。
- 桥接规则过滤 `retain` 标志或单独处理。
- Mosquitto：`persistence` 下 retain 文件需运维清理策略。

## 预防

- 代码评审 **默认 retain=false**。
- 主题命名分离：`.../telemetry`（无 retain）与 `.../config`（可 retain）。
- 集成测试断言新订阅不会收到意外 retain。

## 相关链接

- [A7 Retain/Will](../01-面试篇/A7-retain-will.md) | [P1 丢失](P1-message-loss.md)
- [附录 F CLI](../附录/F-mosquitto-cli-cheatsheet.md) | [C6 安全](../03-运维篇/C6-security-ops.md)

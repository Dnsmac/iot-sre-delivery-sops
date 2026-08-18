# 附录 G：MQTT 配置参考（Mosquitto + Paho + 环境变量）

> 生产 EMQX 细项见 [C3](../03-运维篇/C3-broker-tuning.md)、[B8](../02-开发篇/B8-config-management.md)。

---

## Mosquitto `mosquitto.conf` 要点

| 指令 | 说明 | 开发 | 生产 |
|------|------|------|------|
| `listener 1883` | 监听端口 | ✅ | 仅内网或禁用 |
| `listener 8883` + `cafile/certfile/keyfile` | TLS | 可选 | ✅ |
| `allow_anonymous` | 匿名 | 可 true | **false** |
| `password_file` | 密码文件 | 可选 | ✅ |
| `acl_file` | topic ACL | 建议开 | ✅ |
| `max_connections` | 连接上限 | -1 或 1000 | 按容量 |
| `message_size_limit` | 字节 | 0 默认 | 如 1MB |
| `max_queued_messages` | 每客户端队列 | 1000 | 调大+监控 |
| `persistence` | 持久化 | true | true |
| `autosave_interval` | 秒 | 60 | 按磁盘 |
| `sys_interval` | $SYS 发布间隔 | 10 | 10 |

**ACL 示例片段：**

```
user device001
topic read prod/acme/device001/#
topic write prod/acme/device001/telemetry
```

---

## Paho `MqttConnectOptions`

| 属性 | 默认倾向 | 备注 |
|------|----------|------|
| cleanSession | true | 离线队列用 false |
| keepAliveInterval | 60 | 与 LB 协调 |
| connectionTimeout | 30 | 秒 |
| automaticReconnect | false → 建议 true | |
| maxInflight | 10 | QoS1 窗口 |
| userName/password | - | 生产必填 |
| will | null | 见 A7 |

---

## Spring / 应用配置键（示例）

```yaml
mqtt:
  broker-url: ${MQTT_BROKER_URL:tcp://localhost:1883}
  username: ${MQTT_USER:}
  password: ${MQTT_PASS:}
  client-id-prefix: ${spring.application.name}-
  clean-session: true
  keep-alive-seconds: 120
  max-inflight: 20
  ssl:
    enabled: ${MQTT_SSL:false}
    trust-store: ${MQTT_TRUST_STORE:}
```

---

## 环境变量检查清单

| 变量 | 常见错误 |
|------|----------|
| `MQTT_BROKER_URL` | 仍指向 localhost |
| `MQTT_SSL` | 预发 false、生产 true 未区分 |
| ClientId | 多副本同 ID |

---

## Keep Alive 与 LB 对齐表

| 组件 | 建议关系 |
|------|----------|
| Keep Alive | 60–300s |
| LB TCP idle | > Keep Alive × 2 |
| NAT 超时 | > Keep Alive |

---

## 相关

- [附录 D 性能参数](D-performance-params.md) | [附录 I 迁移](I-env-migration-checklist.md) | [C6 安全](../03-运维篇/C6-security-ops.md)

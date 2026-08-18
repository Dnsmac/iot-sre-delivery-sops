# 附录 F：Mosquitto 命令行速查

> 开发排障必备；生产使用 **相同认证与 TLS** 参数。

---

## 基础发布 / 订阅

```bash
# 订阅（-v 打印 topic，-q QoS）
mosquitto_sub -h localhost -p 1883 -t 'dev/#' -v -q 1

# 发布
mosquitto_pub -h localhost -p 1883 -t 'dev/test' -m 'hello' -q 1

# 调试协议细节
mosquitto_sub -h localhost -t 'dev/test' -d
```

---

## 认证与 TLS

```bash
mosquitto_sub -h mqtt.example.com -p 8883 \
  --cafile ca.crt -u myuser -P 'secret' \
  -t 'prod/acme/#' -v -q 1

mosquitto_pub -h mqtt.example.com -p 8883 \
  --cafile ca.crt -u myuser -P 'secret' \
  -t 'prod/acme/device001/cmd' -m '{"on":1}' -q 1
```

---

## Retain 操作

```bash
# 设置 retain
mosquitto_pub -t 'dev/device001/status' -m 'online' -q 1 -r

# 清除 retain（空 payload + -r）
mosquitto_pub -t 'dev/device001/status' -n -r -q 1

# 只收一条验证
mosquitto_sub -t 'dev/device001/status' -v -C 1
```

---

## 遗嘱（测试时注意会误触发）

```bash
mosquitto_pub -h localhost -t 'dev/willtest' -m 'alive' -q 1 \
  --will-topic 'dev/willtest/lwt' --will-payload 'offline' --will-qos 1
# 用 Ctrl+C 结束而非正常流程会触发 will（测试场景）
```

---

## $SYS 统计（需 Broker 配置 sys_interval）

```bash
mosquitto_sub -h localhost -t '$SYS/#' -v
# 常见：$SYS/broker/clients/connected
```

---

## 批量冒烟（粗测吞吐非严谨）

```bash
for i in $(seq 1 1000); do
  mosquitto_pub -h localhost -t 'bench/t' -m "x$i" -q 0
done
```

---

## Docker 一键（示例）

```bash
docker run -it --rm eclipse-mosquitto mosquitto_sub \
  -h host.docker.internal -t 'dev/#' -v
```

---

## 与 Java 对照

| CLI | Paho |
|-----|------|
| `-q 1` | `MqttMessage.setQos(1)` |
| `-r` | `setRetained(true)` |
| `-u/-P` | `setUserName/setPassword` |
| `--will-*` | `setWill(...)` |

---

## 相关

- [B6 本地开发](../02-开发篇/B6-local-dev.md) | [B9 排障](../02-开发篇/B9-troubleshooting.md) | [附录 E 决策树](E-troubleshooting-decision-tree.md)

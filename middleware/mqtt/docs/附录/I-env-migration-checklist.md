# 附录 I：开发 → 预发 → 生产迁移 Checklist

> 差异矩阵见 [附录 J](J-env-diff-matrix.md)；环境模型见 [B12](../02-开发篇/B12-environment-models.md)。

---

## 使用方式

- 上线前 **逐项打勾**，责任人签字。  
- 与 [B9 场景9](../02-开发篇/B9-troubleshooting.md)、[P9](../04-问题百科/P9-local-vs-prod.md) 对照。

---

## 连接与网络

| # | 检查项 | 开发典型 | 生产要求 | ✓ |
|---|--------|----------|----------|---|
| 1 | `broker-url` 非 localhost | ❌ 常犯 | LB VIP / K8s DNS | |
| 2 | 端口 TCP 1883 / TLS 8883 / WSS | 1883 裸 TCP | 8883 或 WSS | |
| 3 | TLS 证书链完整（含中间 CA） | 无 | trustStore 配置 | |
| 4 | SNI / 主机名与证书 CN 一致 | - | openssl 验证 | |
| 5 | 防火墙 / NetworkPolicy 放行 | 全开 | 仅 8883 等 | |
| 6 | LB idle 超时 > Keep Alive×2 | 无 LB | 120s 级对齐 | |

---

## 认证与授权

| # | 检查项 | ✓ |
|---|--------|---|
| 7 | `allow_anonymous` 关闭 | |
| 8 | 每环境独立账号或 JWT | |
| 9 | ACL 按 `prod/{tenant}/` 前缀 | |
| 10 | 发布与订阅权限最小集 | |
| 11 | ClientId 命名规范（防冲突） | |

---

## 协议语义

| # | 检查项 | ✓ |
|---|--------|---|
| 12 | QoS 与产品表一致（关键流≥1） | |
| 13 | 消费幂等已上线（QoS1） | |
| 14 | Clean Session 与离线策略一致 | |
| 15 | 遗嘱 topic 独立、消费去抖 | |
| 16 | Retain 仅允许列表内 topic | |
| 17 | 禁止未审批 `prod/#` 订阅 | |

---

## 容量与监控

| # | 检查项 | ✓ |
|---|--------|---|
| 18 | 压测在 **EMQX 预发** 完成（非 Mosquitto） | |
| 19 | 连接数 / msg 速率 / 丢弃 告警 | |
| 20 | 桥接 MQTT in vs Pulsar in 对账 | |
| 21 | `max_queued_messages` 与慢消费预案 | |
| 22 | [B11](../02-开发篇/B11-performance-verification.md) 报告归档 | |

---

## 桥接与下游

| # | 检查项 | ✓ |
|---|--------|---|
| 23 | EMQX 规则 SQL 预发验证 | |
| 24 | Pulsar topic 预建与权限 | |
| 25 | 规则失败死信 / 重试策略 | |
| 26 | 桥接 QoS 与源端一致（关键流） | |

---

## 应用与配置

| # | 检查项 | ✓ |
|---|--------|---|
| 27 | 配置中心分环境 profile | |
| 28 | 启动健康检查连 Broker | |
| 29 | callback 无阻塞 I/O | |
| 30 | 日志不打印密码 / 证书私钥 | |

---

## 冒烟命令（生产影子账号）

```bash
mosquitto_sub -h "$PROD_HOST" -p 8883 --cafile "$CA" \
  -u "$USER" -P "$PASS" -t "prod/$TENANT/test" -q 1 -C 1 -v
```

---

## 相关

- [附录 J](J-env-diff-matrix.md) | [B13 改造](../02-开发篇/B13-advocacy-change-strategy.md) | [C1 部署](../03-运维篇/C1-deployment.md)

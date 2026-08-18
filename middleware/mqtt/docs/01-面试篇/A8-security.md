# A8 安全 TLS 与认证

> 优先级: **P1 面试** | 预计阅读 25 分钟 | 深度：已深化 | 学习路径：**D5 | 面试：★★★** | 主路径：[学习路径](../学习路径.md)

## 本章解决什么问题

生产 MQTT 如何 **加密传输、认证身份、授权主题**；能说明 TLS、mTLS、用户名密码与 ACL 的组合，以及开发环境与生产的差异。

---

## 面试常问

1. MQTT 如何加密？端口常用哪些？
2. 用户名密码放在哪？安全吗？
3. mTLS 是什么场景？
4. ACL 做什么？
5. 开发环境匿名，上线要注意什么？

---

## 核心知识

### 传输层

| 方式 | URI/端口 | 说明 |
|------|----------|------|
| 明文 | tcp:// :1883 | 仅开发/内网隔离 |
| TLS | ssl:// :8883 | 证书校验服务端 |
| WebSocket+TLS | wss:// | 浏览器/部分网关 |

### 认证

- **用户名/密码**：CONNECT 携带；Broker 校验（Mosquitto `password_file`、EMQX 内置/外部）。
- **客户端证书 mTLS**：双向 TLS，设备身份绑定证书，适合高安全物联网。

### 授权（ACL）

- 限制 ClientId/用户 **可 publish/subscribe 的主题**。
- 生产按 `{tenant}/{product}/{deviceId}/#` 隔离，禁止 `#` 全网。

### 生产基线

- 关匿名：`allow_anonymous false`
- 强制 TLS；证书轮换流程
- 最小权限 ACL；审计连接与失败认证

---

## 面试标准答案

### 题：MQTT 安全怎么做？

> 传输上生产必须用 TLS，常用 8883。身份认证用用户名密码或客户端证书，证书更适合设备唯一身份。授权在 Broker 用 ACL 限制每个客户端能发布和订阅的主题前缀，避免设备 A 订到设备 B 的数据。还要关匿名接入、限制连接数、打审计日志。应用层 payload 仍可加密或签名校验，那是业务层补充。

### 题：为什么本地能连生产连不上？

> 常见是生产开了 TLS 但客户端仍用 tcp、证书不信任、账号密码或 ACL 不同、地址端口错误。用 openssl s_client 或 mosquitto_sub -d 看 CONNACK 返回码。见 [P9](../04-问题百科/P9-local-vs-prod.md)。

---

## 生产环境注意点

- 密码不要写死在固件；用 **证书或动态注册**。
- LB 终止 TLS 时注意 **SNI** 与后端证书链。
- 见 [附录 I](../附录/I-env-migration-checklist.md)、[C6](../03-运维篇/C6-security-ops.md)。

---

## 易错点与反例

1. **生产仍用 1883 明文** — 窃听与伪造发布。
2. **所有设备同一账号** — 无法追责与 ACL 细分。
3. **校验证书关闭** — 中间人风险。
4. **ACL 过宽 `#`** — 数据泄露。

---

## 动手验证

本仓 Docker Mosquitto 若启用密码，见 `docker/mosquitto.passwd` 与 [B6](../02-开发篇/B6-local-dev.md)。

```bash
mosquitto_sub -h localhost -p 8883 --cafile ca.crt -u user -P pass -t 'dev/#' -q 1
```

---

## 相关章节

- [C6 安全运维](../03-运维篇/C6-security-ops.md) | [B8 配置](../02-开发篇/B8-config-management.md)

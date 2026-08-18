# C6 安全运维加固

> 优先级: **P3 运维** | 预计阅读 35 分钟 | 深度：已深化

## 本章解决什么问题

把 MQTT 从「能连上」提升到 **生产可审计、可防滥用**：TLS、认证、ACL、租户隔离、证书轮换、漏洞与 Dashboard 暴露面治理；开发 Mosquitto 可宽松，生产 EMQX 必须 **默认拒绝**。

---

## 面试常问

1. MQTT 认证有哪些方式？用户名密码和 mTLS 如何选？
2. ACL 按主题还是按 ClientID？
3. 如何防止设备订阅 `/#` 窃听全站？
4. EMQX 多租户隔离怎么做？
5. 证书快过期如何无感轮换？

---

## 核心知识

### 安全分层

```text
传输层 TLS 1.2+ (8883)
    → 认证 (用户名密码 / JWT / 客户端证书)
        → 授权 ACL (pub/sub 主题白名单)
            → 应用层 Payload 签名/加密（可选）
```

### Mosquitto 开发基线

- `password_file` + `acl_file`；关闭 `allow_anonymous` 后再提交镜像。
- 本仓 `docker/mosquitto.passwd` 仅用于本地，**禁止** 入库生产密码。

### EMQX 生产

- **监听器分离**：设备 8883、运维 Dashboard 内网 + SSO。
- **认证链**：内置数据库仅 PoC；生产 LDAP/JWT/HTTP 插件对接 IdP。
- **ACL**：按 **用户名或证书 CN** 映射到主题前缀 `prod/{productId}/{deviceId}/#`。
- **限流**：见 [C3](C3-broker-tuning.md) zone，防单设备刷爆。
- **审计**：连接、订阅、鉴权失败写 SIEM。

### 常见威胁

| 威胁 | 防护 |
|------|------|
| 弱口令扫描 | 强密码策略 + 失败锁定 |
| 未授权订阅 `#` | ACL 禁止 broad wildcard |
| 大 Payload DoS | `max_packet_size` / zone 字节限速 |
| 伪造 ClientID | 证书绑定 + 服务端分配 ID |
| 中间人 | 双向 TLS、证书固定（设备侧） |

---

## 生产环境注意点

- **最小权限**：设备只能 pub 自己的 telemetry、sub 自己的 command。
- 证书 **90 天** 轮换演练纳入 [C9 升级](C9-upgrade.md) 窗口。
- Dashboard/API **禁止** 0.0.0.0 公网；改 VPN 或零信任。
- 合规：日志保留周期、个人信息在 Payload 中需脱敏。
- 与 [A8 安全](../01-面试篇/A8-security.md) 面试题答案一致，运维侧落地。

---

## 易错点与反例

1. **生产仍 `allow_anonymous true`** — 任意人发布 `prod/cmd/#`。
2. **ACL 只限发布不限订阅** — 数据被拖库。
3. **所有设备共用一账号** — 无法吊销单设备。
4. **TLS 终止在 LB 但后端明文 1883 跨公网** — 内网嗅探。
5. **把密钥写在固件镜像** — OTA 泄露全量；应每设备签发。

---

## 动手验证

```powershell
# Mosquitto 密码用户（示例）
mosquitto_pub -h localhost -u devuser -P devpass -t dev/sec/test -m ok

# 预期 ACL 拒绝
mosquitto_sub -h localhost -u devuser -P devpass -t prod/other/#
```

EMQX：在 Dashboard **认证/ACL** 页用测试 Client 验证 allow/deny。

---

## 相关章节

- [C1 部署](C1-deployment.md) | [A8 安全](../01-面试篇/A8-security.md)
- [P9 本地与生产](../04-问题百科/P9-local-vs-prod.md) | [附录 G](../附录/G-config-reference.md)

# P9 本地正常、生产不行

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- `mosquitto_pub` / 本仓 Java 示例在 **localhost 成功**，生产 EMQX **失败或无消息**。
- 预发偶现、生产必现；或反向生产行本地不行。
- 同一套代码 **仅改 broker URL** 就异常。

## 常见原因

| 原因 | 说明 |
|------|------|
| 协议/端口 | 本地 1883 明文，生产 8883 TLS |
| 主题前缀 | `dev/` vs `prod/` ACL 不允许 |
| 认证 | 本地匿名，生产用户名/证书 |
| ClientID | 生产禁止固定 `test-client` |
| QoS/会话 | 环境配置中心值不同 |
| 负载均衡 | 连到错误入口或健康检查误配 |
| 防火墙 | 出站 8883 被封 |
| 版本差异 | Mosquitto 3.1.1 与 EMQX 5.0 特性 |

## 排查步骤

1. 对照 [附录 J 环境矩阵](../附录/J-env-diff-matrix.md) 逐项 diff。
2. 用生产等价参数 **本地 EMQX 单节点** 复现（缩小差距）。
3. `openssl s_client -connect host:8883` 验证证书。
4. 查 EMQX **鉴权日志** 与 CONNACK 码。
5. 确认订阅主题 **与 ACL 完全一致**（大小写）。
6. 排除 **VPN/Hosts** 指错 Broker IP。

## 解决

- 统一 **配置中心**：brokerUrl、topicPrefix、qos、trustStore。
- CI 增加 **staging 冒烟**（非仅 Mosquitto）。
- 提供 **诊断 CLI** 脚本（证书、pub/sub 一条）。
- 文档化环境差异，禁止硬编码 `localhost`。
- TLS：设备导入正确 CA；服务端完整链。

## 预防

- [B6 本地开发](../02-开发篇/B6-local-dev.md) 与 [B8 配置管理](../02-开发篇/B8-config-management.md) 对齐结构。
- 预发 ACL 与生产 **同策略不同前缀**。
- 发布检查清单：证书过期日、主题表。

## 相关链接

- [附录 J](../附录/J-env-diff-matrix.md) | [附录 I 迁移](../附录/I-env-migration-checklist.md)
- [C1 部署](../03-运维篇/C1-deployment.md) | [C6 安全](../03-运维篇/C6-security-ops.md) | [P6 断连](P6-disconnect.md)

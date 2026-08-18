# 附录 F：pulsar-admin 速查

> 深度：全文加深 ✓ | Windows 下经 Docker：`docker exec pulsar-standalone bin/pulsar-admin ...`

---

## 一、集群健康

```bash
pulsar-admin brokers healthcheck
pulsar-admin brokers list
pulsar-admin clusters list
pulsar-admin bookies list-bookies
pulsar-admin bookies list-bookies -rw    # 可写 Bookie
```

---

## 二、租户与 Namespace

```bash
# 创建
pulsar-admin tenants create dev --allowed-clusters standalone
pulsar-admin namespaces create dev/test

# 策略查看
pulsar-admin namespaces policies persistent://dev/test
pulsar-admin namespaces get-retention persistent://dev/test
pulsar-admin namespaces get-message-ttl persistent://dev/test
pulsar-admin namespaces get-backlog-quotas persistent://dev/test

# 设置（示例）
pulsar-admin namespaces set-retention persistent://dev/test --time 7d --size 10G
pulsar-admin namespaces set-message-ttl persistent://dev/test --messageTTL 86400
pulsar-admin namespaces set-backlog-quota persistent://dev/test \
  --limit 1G --policy producer_request_hold --type destination_storage
```

---

## 三、Topic

```bash
# 非分区
pulsar-admin topics create persistent://dev/test/my-topic
pulsar-admin topics list dev/test
pulsar-admin topics delete persistent://dev/test/my-topic

# 分区 Topic
pulsar-admin topics create-partitioned-topic persistent://dev/test/events -p 8
pulsar-admin topics partitioned-stats persistent://dev/test/events
pulsar-admin topics update-partitioned-topic persistent://dev/test/events -p 16  # 只增不减

# 统计与窥探
pulsar-admin topics stats persistent://dev/test/my-topic
pulsar-admin topics stats-internal persistent://dev/test/my-topic
pulsar-admin topics peek-messages persistent://dev/test/my-topic -s my-sub -n 10

# 订阅管理
pulsar-admin topics unsubscribe persistent://dev/test/my-topic -s my-sub
pulsar-admin topics skip-all persistent://dev/test/my-topic -s my-sub  # 慎用：跳过积压
```

**stats 关键字段：** `msgRateIn`、`msgRateOut`、`storageSize`、`subscriptions.<name>.msgBacklog`、`consumers[].connected`。

---

## 四、Schema

```bash
pulsar-admin schemas get-schema-version persistent://dev/test/events
pulsar-admin schemas get-schema-authentication-data persistent://dev/test/events
pulsar-admin namespaces get-schema-compatibility-strategy persistent://dev/test
pulsar-admin namespaces set-schema-compatibility-strategy persistent://dev/test --strategy BACKWARD
```

详 [附录 L Schema](L-Schema注册表速查.md)、[A9](../part-a-interview/A9-Schema注册.md)。

---

## 五、权限（生产）

```bash
pulsar-admin namespaces grant-permission persistent://company/production \
  --roles order-service --actions produce,consume
pulsar-admin namespaces revoke-permission persistent://company/production --roles old-svc
```

---

## 六、消费测试（冒烟）

```bash
bin/pulsar-client produce persistent://dev/test/hello -m "ping"
bin/pulsar-client consume persistent://dev/test/hello -s test-sub -n 1
```

---

## 七、PowerShell 别名（本仓库）

```powershell
function pa { docker exec pulsar-standalone bin/pulsar-admin @args }
pa topics stats persistent://dev/test/hello
```

---

## 八、命令 → 场景

| 你想… | 命令 |
|--------|------|
| 消息丢没进 Topic | `topics stats` 看 msgIn |
| 谁在消费 | `stats` → subscriptions |
| 积压多少 | `msgBacklog` |
| 偷看消息不消费 | `peek-messages` |
| 重置进度 | `unsubscribe` 或 `skip-all`（慎） |
| 磁盘谁占满 | 各 Topic `storageSize` + Bookie 主机 `df` |

---

## 相关

- [B6](../part-b-java-dev/B6-本地开发.md) | [附录 E](E-排查决策树.md) | [C10](../part-c-ops/C10-故障预案.md)

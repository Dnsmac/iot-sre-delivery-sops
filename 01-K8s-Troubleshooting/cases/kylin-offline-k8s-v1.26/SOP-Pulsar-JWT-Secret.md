# SOP · Pulsar JWT Secret 与 Helm pending

| 字段 | 内容 |
|------|------|
| 场景 | Helm 安装 Pulsar（JWT 非对称） |
| 现象 | broker/proxy `FailedMount`：`pulsar-token-asymmetric-key not found`；或 `another operation in progress` |
| 影响 | Pulsar 起不来；重跑 install 一直失败 |

## 1. 快速定界

```bash
kubectl get secret -n meta | grep pulsar-token
kubectl describe pod -n meta pulsar-broker-0 | tail -20
helm list -n meta -a
# STATUS=pending-install → 锁住
```

## 2. 根因

1. Chart 需要 `pulsar-token-asymmetric-key`（PUBLICKEY/PRIVATEKEY）+ admin/broker/proxy token；旧脚本只 apply 了 token YAML  
2. 上次 `--wait` 超时留下 **pending-install**，后续 upgrade 被拒  

**Token 策略**：全环境固定（与历史 `delopy/k8s国产化/pulsar` 密钥对一致）。

## 3. 修复

```bash
# JWT（脚本 03-install-pulsar.sh 已自动化）
kubectl -n meta create secret generic pulsar-token-asymmetric-key \
  --from-file=PUBLICKEY=/opt/offline/configs/pulsar/jwt-public.key \
  --from-file=PRIVATEKEY=/opt/offline/configs/pulsar/jwt-private.key \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f /opt/offline/configs/pulsar/pulsar-jwt-secrets.yaml

# 清 Helm 锁
kubectl delete secret -n meta -l owner=helm,name=pulsar
# 或：kubectl delete secret -n meta sh.helm.release.v1.pulsar.v1

bash /opt/offline/scripts/cluster/03-install-pulsar.sh
```

## 4. 验证

```bash
helm list -n meta   # pulsar = deployed
kubectl get pods -n meta | grep pulsar
```

## 5. 防复发

- B00 必须含 `jwt-*.key` + 安装前创建 asymmetric Secret  
- 安装脚本自动清理 `pending-*`

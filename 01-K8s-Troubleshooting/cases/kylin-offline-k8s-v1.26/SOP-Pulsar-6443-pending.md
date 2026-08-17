# SOP · Pulsar Helm 6443 connection refused / pending-install

| 字段 | 内容 |
|------|------|
| 场景 | `install-all-middleware` 装 Pulsar |
| 现象 | `dial tcp 127.0.0.1:6443: connect: connection refused`；Helm `pending-install` |

## 1. 根因

装中间件时在控制面 **`systemctl restart kubelet`**（旧版 NFS 装包后、或 Harbor containerd 后再启 kubelet），静态 Pod apiserver 短暂不可用。  
Helm `--wait` 查 Service 时连不上本机 6443 → 失败并留下 `pending-install`。

旁证：kubelet 日志出现 `Stopping/Started Kubernetes Kubelet`；Pod 事件有 `etcdserver: request timed out`。

## 2. 现场恢复

```bash
export KUBECONFIG=/etc/kubernetes/admin.conf
kubectl get --raw=/readyz                    # 须 ok
kubectl get pods -n meta | grep pulsar       # 常已 Running，仅 Helm 状态坏
helm list -n meta -a
kubectl delete secret -n meta -l owner=helm,name=pulsar
# 或按名删 sh.helm.release.v1.pulsar.v1
bash /opt/offline/scripts/cluster/03-install-pulsar.sh
bash /opt/offline/scripts/cluster/04-install-camellia-proxy.sh   # 若 install-all 中断
```

## 3. 防复发（B00 v1.0.16+）

- NFS 只装 `nfs-utils`，**不再** restart kubelet  
- Harbor containerd **只** restart containerd，不再 restart kubelet  
- `install-all-middleware` 在 Helm 前 `wait_k8s_api`  
- Pulsar 失败自动清 pending 重试一次  
- **禁止**中间件安装过程中手动 restart kubelet（尤其 105）

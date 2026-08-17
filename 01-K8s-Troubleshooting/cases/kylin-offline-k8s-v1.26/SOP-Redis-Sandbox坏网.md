# SOP · Redis 重启 / Calico Sandbox 坏网

| 字段 | 内容 |
|------|------|
| 场景 | 装簇后 Helm 装 Redis Cluster |
| 现象 | 部分 Pod 反复重启；Startup probe `no route to host` / `invalid argument` |
| 影响 | Redis 集群无法组网；Helm 可能长期 pending |

## 1. 快速定界

```bash
kubectl get pods -n meta -o wide
kubectl describe pod -n meta redis-cluster-1 | tail -30
# 在节点上：
# Pod netns 仅有 lo、无 eth0；主机无对应 cali* 接口
# 新起测试 Pod 网络正常 → 说明 Calico 整体 OK，仅坏 Sandbox
```

跨节点：

```bash
kubectl exec -n meta redis-cluster-0 -- sh -c \
  'timeout 3 bash -c "echo >/dev/tcp/<peer-pod-ip>/6379" && echo OK || echo FAIL'
```

## 2. 根因

- 部分节点 **restart kubelet** 后，Helm 安装中 Pod 快速删建  
- CNI 拆了旧 `cali`，kubelet 仍持旧 Sandbox → **IP 还在、网卡没了**

## 3. 修复

```bash
kubectl delete pod -n meta redis-cluster-1 redis-cluster-3 --force --grace-period=0
# 仍异常：
kubectl delete pod -n kube-system -l k8s-app=calico-node
```

## 4. 验证

```bash
kubectl get pods -n meta -l app.kubernetes.io/name=redis-cluster
# 期望 6/6 Ready；cluster_state:ok
```

## 5. 防复发

- 中间件安装完成前 **禁止** 单节点 `systemctl restart kubelet`  
- 必须重启：四台一起 + 滚动 calico-node  
- Redis Ready 后再装 Pulsar

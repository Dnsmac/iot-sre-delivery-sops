# SOP · nodelocaldns 探针超时 / DNS 环路（Lab VM 线）

| 字段 | 内容 |
|------|------|
| 场景 | Kuboard-Spray 离线装簇后（K8s v1.26.4 + Calico + nodelocaldns） |
| 现象 | ① 控制面 `NotReady`、nodelocaldns 探针超时；② nodelocaldns CrashLoop，meta 内 Redis 等按 Service 名解析失败 |
| 影响 | 节点 NotReady、业务 Pod DNS 全挂；离线环境外网查询无出口，错误改法会加重 |
| 源记录 | `delopy/k8s国产化/runbooks/offline-install-checklist.md` §2/§4.3 |

## 1. 快速定界

```bash
kubectl get nodes                          # NotReady？
kubectl get pods -n kube-system | grep nodelocaldns   # CrashLoop / 探针失败？
curl -s http://169.254.25.10:9254/health   # 节点上执行，应 OK
cat /etc/resolv.conf                       # 看是否含 169.254.25.10（环路特征）
iptables -L OUTPUT -n --line-numbers       # 看 DROP 是否吞了内网网段
```

两类故障，一次排查定界：

- **iptables 吞包**：DROP 外网时未放行集群网段 → 探针超时 / 控制面 NotReady
- **resolv.conf 环路**：宿主机 `/etc/resolv.conf` 含 `169.254.25.10` → nodelocaldns 转发上游又是自己 → FATAL loop

## 2. 根因

### 2.1 iptables 漏放集群网段

模拟离线只写了 `DROP 外网`，但装簇/健康检查依赖内网互通。必须放行：

| 网段 | 原因 |
|------|------|
| `192.168.127.0/24` | 节点互访 / SSH |
| `127.0.0.0/8` | 本机 API |
| `10.233.0.0/16` | Service CIDR（Calico install-cni 访问 API） |
| `10.234.0.0/16` | Pod CIDR |
| `169.254.25.10` | nodelocaldns 健康检查 `:9254` |

> 只 DROP 外网、不放行上述网段 → 装簇「成功」后节点 `NotReady`、nodelocaldns 不健康。

### 2.2 resolv.conf 自指环路

宿主机 `/etc/resolv.conf` 含 `169.254.25.10` 后，nodelocaldns 的 `.` 区（上游）读到它 → 自己转发给自己。
**禁止**把 `.:53` 整段改成 `forward . 10.233.0.3`：外网查询会全部打到 CoreDNS，离线环境不稳定。

## 3. 修复

```bash
# ① iptables：每台节点执行脚本（放行上表 5 项，其余 DROP）
bash lab-offline-iptables.sh

# ② DNS 环路：改宿主机 resolv + 恢复标准 Corefile
UPSTREAM_DNS=192.168.127.2 bash fix-nodelocaldns-loop.sh      # 每台节点
bash fix-nodelocaldns-configmap.sh                            # 仅控制面
```

正确分层：

| 层级 | DNS | 说明 |
|------|-----|------|
| Pod | `169.254.25.10` | kubelet `clusterDNS`，不变 |
| 节点宿主机 | 网关/现场 DNS | `/etc/resolv.conf` **不得**含 `169.254.25.10` |
| nodelocaldns | 标准 Corefile | `cluster.local` → CoreDNS；`.` → `/etc/resolv.conf` |

脚本源：`delopy/k8s国产化/runbooks/scripts/fix-nodelocaldns-loop.sh`、`fix-nodelocaldns-configmap.sh`（不复制进本仓，以源仓为准）。

## 4. 验证

```bash
kubectl get pods -n kube-system | grep nodelocaldns   # 1/1 Running，无 FATAL loop
curl http://169.254.25.10:9254/health                 # OK
kubectl exec -n meta <pod> -- getent hosts kubernetes.default.svc.cluster.local
```

## 5. 防复发

- 断外网脚本与集群网段放行**同一个脚本**维护，禁止手工零散 iptables 命令
- 节点镜像/初始化阶段就固化 `/etc/resolv.conf`（不含 169.254.25.10），装簇后只读
- Corefile 保持 Spray 默认，不手工改区转发

# SOP · containerd 节点配 Harbor HTTP（443 refused）

| 字段 | 内容 |
|------|------|
| 场景 | 装簇后，K8s 节点（containerd 1.6.19）拉取内网 Harbor（HTTP :80）业务镜像 |
| 现象 | `crictl pull` 报 `443 connection refused`；nfs-client-provisioner `ImagePullBackOff`；误配后 kubelet 循环 `CRI v1 runtime API is not implemented` |
| 影响 | 业务镜像全部拉不下来，中间件/业务装不下去 |
| 源记录 | `delopy/k8s国产化/runbooks/k8s-node-harbor-containerd-record-2026-08-05.md` |

## 1. 快速定界

```bash
crictl pull 192.168.127.251/meta/kh-meta/common/bitnami/redis-cluster:6.2.7-debian-11-r60
journalctl -u containerd --since "10 min ago" | grep -i -E "invalid|refused"
cat /etc/containerd/config.toml | grep -A3 registry
```

两个特征对应两种错：

- `443 connection refused`：containerd 把 HTTP Harbor 当 HTTPS 打 → 没配 certs.d
- `mirrors cannot be set when config_path is provided` + kubelet 循环 CRI 报错：`config_path` 与旧 `registry.mirrors` 段**同时存在**

## 2. 根因

1. Harbor 走 HTTP :80，containerd 默认对非 HTTPS registry 先试 443
2. containerd 1.6 有**两套互斥**配置：旧 `registry.mirrors` 内联段 vs 新 `config_path`（certs.d 目录）——共存即 invalid plugin config，kubelet 起不来

## 3. 修复

### 3.1 config.toml 只保留 config_path（删 mirrors 整段）

```toml
[plugins."io.containerd.grpc.v1.cri".registry]
  config_path = "/etc/containerd/certs.d"
```

### 3.2 certs.d 目录（每台节点）

```toml
# /etc/containerd/certs.d/192.168.127.251/hosts.toml
server = "http://192.168.127.251"

[host."http://192.168.127.251"]
  capabilities = ["pull", "resolve", "push"]
  skip_verify = true
```

建议保留 `docker.io/hosts.toml`（指向 registry-1.docker.io），避免业务镜像 tags 混淆。

### 3.3 生效

```bash
systemctl restart containerd && systemctl restart kubelet
```

批量脚本：`delopy/k8s国产化/runbooks/scripts/configure-harbor-containerd.sh`（`HARBOR_IP=<ip> bash ...`，不复制进本仓）。

## 4. 验证

```bash
# 必须用 crictl（走 CRI）；ctr pull 仍会走 https:443，不能作为验收标准
crictl pull 192.168.127.251/meta/kh-meta/common/sig-storage/nfs-subdir-external-provisioner:v4.0.2
kubectl get pods -n kube-system -l app=nfs-client-provisioner   # Running
kubectl get sc                                                   # nfs-client
```

## 5. 防复发

- Harbor HTTP 的验收口径统一为 **`crictl pull` 成功**，不因 443 报错误判 Harbor 挂了
- 节点初始化基线里内置 certs.d 配置；装簇镜像对齐时一起校验
- 与 `SOP-Harbor导入401误报.md` 区分：那个是 push 后 verify 401（镜像其实已入库），这个是节点侧拉取配置问题

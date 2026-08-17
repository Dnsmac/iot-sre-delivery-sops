# 案例：麒麟 V10 离线 K8s v1.26.4 交付

> **类型**：现场交付 / 实验室复盘证据  
> **时间**：2026-08  
> **环境**：192.168.27.105～110（NFS+Spray / Harbor / 4×K8s）  
> **交付源码仓**（可执行脚本与物料）：`C:\Users\kaihong\Desktop\87\work`（VERSION **1.0.16**）  
> **本目录**：只沉淀 **SOP + 踩坑 + 面试口径**，不复制 GB 级离线包。

---

## 拓扑（一句话）

```text
109 NFS + Kuboard-Spray:8080
110 Harbor:80
105～108 K8s（105 控面装中间件 Redis/Pulsar）
```

完全离线：B00～B09 分包；装簇用 Spray；中间件 Helm。

---

## 文档索引

| 文件 | 用途 |
|------|------|
| [`踩坑清单.md`](踩坑清单.md) | 全量问题 → 根因 → 修复（排障地图） |
| [`交付复盘.md`](交付复盘.md) | 面试/复盘叙事（现象→排查→结论→防复发） |
| [`SOP-模拟离线iptables.md`](SOP-模拟离线iptables.md) | 断外网规则（含 Docker FORWARD） |
| [`SOP-Harbor导入401误报.md`](SOP-Harbor导入401误报.md) | push 成功但 verify 401 |
| [`SOP-Redis-Sandbox坏网.md`](SOP-Redis-Sandbox坏网.md) | Redis 重启 / Pod 无 eth0 |
| [`SOP-Pulsar-JWT-Secret.md`](SOP-Pulsar-JWT-Secret.md) | 缺 asymmetric-key / Helm pending |
| [`SOP-Spray-SSH私钥.md`](SOP-Spray-SSH私钥.md) | 实验室 vs 现场客户私钥 |
| [`SOP-Pulsar-6443-pending.md`](SOP-Pulsar-6443-pending.md) | 中间件 restart kubelet → 6443 refused / pending |
| [`SOP-物料校验与B08截断.md`](SOP-物料校验与B08截断.md) | rar 损坏、CHECKSUMS CRLF、/tmp 满 |

---

## 和本仓其它目录的关系

| 本仓位置 | 关系 |
|----------|------|
| `01-K8s-Troubleshooting/` | **本案例归属**（CNI/Sandbox/装簇交付） |
| `04-Middleware-Linux/` | Redis/Pulsar 坑可挂链到本案例 SOP |
| `05-Interview-Prep/stories/` | 可抽「离线交付一次过」故事（见交付复盘 §面试口径） |
| 交付源码 | `87\work`：脚本以源仓为准；本仓不维护第二份脚本 |

---

## 快速验收口径（装完应满足）

- `kubectl get nodes`：4 Ready  
- `helm list -n meta`：redis-cluster / pulsar 均为 `deployed`  
- `kubectl get pods -n meta`：redis 6/6、pulsar 组件 Running  
- Harbor：匿名 `docker pull` 关键业务镜像成功（不以 curl manifest 401 判失败）

# D2 学习记录：MetalLB（网络暴露 / L4 负载均衡）

> W1 · 对应手册 D2 · 属 **网络路由** 子专题，总览见 [`D3_网络路由.md`](D3_网络路由.md)  
> 关联：MetalLB、LoadBalancer Service、kube-proxy、CNI  
> 学习日期：________  
> **与面试题清单双向对齐**：题有笔记补在 §7.1～§9、§8.6～8.7 等；笔记有题补在题清单 §四。
---

## 1. MetalLB 是什么（一句话）

在裸机/自建 K8s 没有云厂商 LB 时，**MetalLB 为 `type=LoadBalancer` 的 Service 分配并宣告 VIP**，把外部流量引进集群；**Pod 间路由仍由 CNI 负责**，MetalLB 只管 VIP 宣告。

---

## 2. 核心组件

| 组件 | 作用 |
|------|------|
| **Controller** | 监听 `type=LoadBalancer` 的 Service；从 `IPAddressPool` 选未占用 IP；写入 `status.loadBalancer.ingress.ip` |
| **Speaker** | 以 DaemonSet 跑在各节点；负责 **L2 ARP 宣告** 或 **BGP 路由宣告** |

---

## 3. 地址分配流程

```text
用户创建 Service (type=LoadBalancer)
    → Controller 监听到事件
    → 从 IPAddressPool 选取空闲 IP
    → 更新 Service.status.loadBalancer.ingress.ip
    → Speaker 在节点上宣告该 VIP（L2 或 BGP）
```

### 3.1 配置 CRD（IPAddressPool / Advertisement）

| 对象 | 作用 |
|------|------|
| **IPAddressPool** | 定义可分配的 IP 段（如 `192.168.27.190-200`） |
| **L2Advertisement** | 声明某池用 **Layer2（ARP）** 宣告 |
| **BGPAdvertisement** | 声明某池用 **BGP** 宣告 |

关系：`Pool` 提供 IP → `Advertisement` 决定怎么宣告 → `Controller` 分配 → `Speaker` 执行。  
现网从 Service 注解可见池名：`metallb.universe.tf/ip-allocated-from-pool: first-pool`。

---

## 4. Layer2 模式

### 工作原理

- 集群内 **Speaker DaemonSet** 通过内部协议 **选举 Leader**（基于 **memberlist / gossip**）。
- Leader 节点响应局域网 **ARP**：对外宣告「VIP 的 MAC 在我这里」。
- 外部流量被引到 **Leader 节点**；该节点上 **kube-proxy**（iptables/ipvs）按规则转发到后端 Pod。

### 流量路径

```text
外部请求 → VIP
    →（L2）ARP 到 Leader 节点
    → 节点 kube-proxy（iptables/ipvs）
    → Service ClusterIP / Endpoints
    → Pod IP
```

### 缺点与故障转移

| 项 | 说明 |
|----|------|
| 瓶颈 | 流量经 **单 Leader**，易成单点带宽瓶颈 |
| 故障转移 | 依赖新 Leader 选举 + **客户端 ARP 缓存刷新** |
| 时间粗算 | 选举 gracePeriod（约 **1～5s**）+ ARP 缓存刷新（常见 **30s 内**） |

### 4.1 L2 单点瓶颈与优化（面试题 3）

**为何单点**：同一 VIP 在 L2 下通常只有一个 Leader 接收入口流量，再经本机 kube-proxy 转 Pod。

**优化手段**：

1. 改 **BGP + ECMP**（多节点分担，要路由器配合）
2. **拆 VIP**：多 Service、多环境各用独立 VIP（现网 meta / meta-test / meta-biz）
3. 加大 Leader 节点网卡/CPU、优化后端副本
4. 中小流量接受 L2，大流量规划 BGP

### 4.2 故障转移怎么测（面试题 15）

| 操作 | 测到什么 |
|------|----------|
| 删 **后端 Pod** | 只测 kube-proxy / Endpoints，**不会**换 MetalLB Leader |
| **Leader 节点宕机** 或该节点 Speaker 不可用 | 才测 MetalLB 换节点宣告 VIP |

---

## 5. BGP 模式

### 工作原理

- 各节点 Speaker 与 **上层路由器** 建立 **BGP 对等**。
- 向路由器 **宣告到达 VIP 的路由**。
- 路由器用 **ECMP** 把流量分到多个节点，实现 **多节点负载**，减轻 L2 单 Leader 瓶颈。

### 前提与备注

| 项 | 说明 |
|----|------|
| 依赖 | 上游交换机/路由器需配置 **AS 号、Neighbor IP、MD5、路由过滤** 等 |
| 特点 | **非开箱即用**；需网络侧配合 |
| ECMP | 依赖路由器硬件/策略支持 |

### 流量路径

```text
外部请求 → VIP
    →（BGP）路由器 ECMP 到任意节点
    → 节点 kube-proxy → Pod IP
```

### 5.1 节点故障为何丢包（面试题 4）

- 节点宕机后 Speaker **撤回 BGP 宣告**，路由器 **路由表收敛** 需时间（秒级～数十秒）。
- 收敛前路由器仍可能把包发到 **已挂节点** → **短暂丢包**；ECMP 哈希到坏节点同理。
- 应用无重试时：超时、**MQTT 断连**。  
- **与 L2 对比**：L2 慢在 **ARP 缓存**；BGP 慢在 **路由收敛**，都可能短时丢包。

---

## 6. L2 vs BGP 对比（面试用）

| 维度 | Layer2 | BGP |
|------|--------|-----|
| 宣告方式 | ARP，单 Leader | 路由，多节点 ECMP |
| 瓶颈 | Leader 单点 | 相对分散 |
| 运维复杂度 | 低，易上手 | 高，要配路由器 |
| 故障转移 | 慢（ARP 缓存） | 相对快（路由收敛） |

### 6.1 面试陷阱简记（题 F1～F5）

| 陷阱 | 正解 |
|------|------|
| F1 L2 一定只过一节点？ | 是，入口单 Leader；BGP 可多节点，但收敛期仍可能丢包 |
| F2 ARP 冲突 | 多节点误应答同一 VIP → 流量漂移；见 §7.2 strictARP |
| F3 MetalLB 能做 L7？ | **不能**，只做 L4；L7 用 Ingress |
| F4 多 Service 共用一个 VIP？ | 一般 **一 Service 一 VIP**，不要硬共用 |
| F5 与 Calico BGP 一样？ | **不是**：Calico 宣告 **Pod 网段**；MetalLB 宣告 **Service VIP** |

---

## 7. 与 Ingress、CNI 的边界

| 层级 | 谁负责 | 说明 |
|------|--------|------|
| L4 VIP | **MetalLB** | 只负责 VIP 分配与宣告 |
| L7 HTTP 路由 | **Ingress**（若使用） | 域名/路径转发；IoT 常是 TCP/MQTT，不一定走 Ingress |
| Pod 网络 | **CNI** | Pod IP、跨节点转发 |
| Service → Pod | **kube-proxy** | ClusterIP / NodePort / LB 后端转发 |

**完整链路（牢记）**：

```text
外部请求 → VIP
    → (L2: ARP 到 Leader / BGP: 路由器 ECMP 到任意节点)
    → 节点 iptables/ipvs（kube-proxy）
    → ClusterIP / Endpoints
    → Pod IP（CNI）
```

### 7.1 三种 Service 类型（面试题 17、19、32）

| 类型 | 谁能访问 | 典型用途 |
|------|----------|----------|
| **ClusterIP** | 仅集群内 | 微服务互调 |
| **NodePort** | 节点 IP + 高位端口 | 调试、临时暴露 |
| **LoadBalancer** | **VIP + 标准端口** | 生产设备、**MQTT 1883** |

**裸机为何要 MetalLB**：没有云 LB 时，LoadBalancer 需要 MetalLB 才有 VIP；**NodePort** 要让设备记「某节点 IP + 随机高端口」，防火墙难管，不适合 40W 设备固定接入。

**为何 LB 上还有 NodePort**（现网 `80:30673`、`1883:30189`）：K8s 默认行为，LB 类型 **保留** NodePort。  
- **生产设备**：连 **VIP:1883**  
- **NodePort**：仅调试备用，不要给设备配。

**ClusterIP 与 EXTERNAL-IP 并存**（现网 `10.233.40.193` + `192.168.27.190`）：  
- 集群内：走 **ClusterIP / 服务名**  
- 集群外/设备：走 **VIP**

### 7.2 strictARP 与 kube-proxy 模式（面试题 5、18）

| 项 | 说明 |
|----|------|
| **iptables / ipvs** | VIP 进节点后由 **kube-proxy** 转发；**ipvs** 性能通常更好 |
| **strictARP** | 常见于 **Calico + kube-proxy IPVS + MetalLB Layer2** |
| **为何开** | 避免 **非 Leader 节点** 错误响应 VIP 的 ARP，导致 VIP 漂移异常、间歇不通 |
| **怎么查模式** | `kubectl get cm kube-proxy -n kube-system -o yaml \| grep mode` |

MetalLB **不替代** kube-proxy，也不替代 CNI。

---

## 8. 结合现项目（现网证据 2026-05-19）

### 8.1 MetalLB 组件状态

| 项 | 现网值 |
|----|--------|
| Namespace | `metallb-system` |
| Controller | 1 个 Pod Running（如 `controller-5fd797fbf7-5826m`） |
| Speaker | **6** 个 Pod Running（DaemonSet，对应 **6 节点** 集群） |
| 运行时长 | 组件已稳定运行约 68 天（以你集群为准） |

```bash
kubectl get pods -n metallb-system
# controller ×1 + speaker ×6
```

### 8.2 地址池与模式

| 项 | 现网值 |
|----|--------|
| IP 池名称 | `first-pool`（注解 `metallb.universe.tf/ip-allocated-from-pool`） |
| VIP 网段 | `192.168.27.0/24` 段（见下表各 VIP） |
| **实际模式** | **Layer2**（Events 明文） |

**关键 Event（describe svc 顶部）**：

```text
Normal  metallb-speaker announcing from node "node6" with protocol "layer2"
```

→ 与笔记 §4 一致：当前由 **node6** 作为 L2 Leader 对外 ARP 宣告 VIP。

### 8.3 LoadBalancer 服务（iot-web 系列）

| Namespace | Service | 类型 | EXTERNAL-IP (VIP) | 说明 |
|-----------|---------|------|-------------------|------|
| `meta` | `iot-web` | LoadBalancer | **192.168.27.190** | 生产/主环境（本次 describe 对象） |
| `meta-test` | `iot-web` | LoadBalancer | 192.168.27.197 | 测试环境 |
| `meta-biz` | `iot-web-service` | LoadBalancer | 192.168.27.193 | 业务环境 |

同一 IP 池为不同 NS 各分配独立 VIP，环境隔离靠 **NS + VIP**，不是共用同一个 Service。

### 8.4 样例：`meta/iot-web`（你执行的 describe）

| 字段 | 值 |
|------|-----|
| ClusterIP | `10.233.40.193` |
| LoadBalancer Ingress | `192.168.27.190` |
| 端口 | `80/TCP` → NodePort `30673`；**`1883/TCP`** → NodePort `30189` |
| Endpoints | **3** 个后端 Pod（`10.234.x.x`，三副本） |
| 对外方式 | **LoadBalancer + MetalLB L2**（非 Ingress） |

**流量路径（本环境）**：

```text
设备/客户端 → 192.168.27.190:80 或 :1883
    → L2 ARP 到 node6（Leader，可变）
    → kube-proxy → Endpoints(3 Pods)
```

**IoT 关联**：`1883` 为 MQTT 常用端口，说明 **iot-web** 在 L4 同时暴露 HTTP 与 MQTT，符合物联网接入场景。

### 8.5 验证命令留存

```bash
kubectl describe svc iot-web -n meta
kubectl get svc -A | grep iot-web
kubectl get pods -n metallb-system
```

### 8.6 VIP 正常但访问不通（面试题 31）

MetalLB 只保证 **包进到入口节点**；之后靠 **kube-proxy → Endpoints → Pod**。

```bash
kubectl get endpoints iot-web -n meta
kubectl get pods -n meta -l <selector>
kubectl describe svc iot-web -n meta
kubectl logs <iot-web-pod> -n meta
```

| 现象 | 可能原因 |
|------|----------|
| Events 有 `layer2 announcing`，Endpoints **空** | 后端 Pod 未 Ready / selector 错 |
| Endpoints 有 IP，仍不通 | 应用未监听 80/1883、防火墙、网络策略 |

### 8.7 LoadBalancer 一直 Pending（面试题 12）

1. `kubectl get pods -n metallb-system` — Controller/Speaker 是否 Running  
2. 是否配置 **IPAddressPool** + **L2Advertisement**（或 BGPAdvertisement）  
3. `kubectl logs -n metallb-system -l component=controller` — 是否 **池耗尽**、无可用 IP  
4. Service 是否 `type: LoadBalancer`  
5. 环境匹配：裸机用 MetalLB；公有云一般用云 LB，**不要混用错方案**

### 8.8 如何确认当前宣告节点（面试题 16）

```bash
kubectl describe svc iot-web -n meta
# Events: announcing from node "node6" with protocol "layer2"
```

---

## 9. 云厂商 LB 与 keepalived（面试题 6、7）

### 9.1 MetalLB vs 云 LoadBalancer

| 维度 | 云 LB（ELB/SLB 等） | MetalLB |
|------|---------------------|---------|
| 场景 | 公有云托管 K8s | **裸机 / IDC / 私有云** |
| 实现 | 云 API 分配、云控面健康检查 | Controller 分 IP + Speaker ARP/BGP |
| K8s 接口 | 同为 `type=LoadBalancer` | 同上 |
| 能力 | 常带 WAF、证书 | **仅 L4 VIP** |

### 9.2 MetalLB Layer2 vs keepalived

| | keepalived (VRRP) | MetalLB L2 |
|---|-------------------|------------|
| 场景 | VM/物理机手工 VIP | **按 Service 自动** 分配/释放 VIP |
| 选举 | VRRP | Speaker **memberlist/gossip** |
| 相似 | 都是 ARP + **单活跃节点** 接收入口流量 | 同左 |

**一句**：MetalLB L2 ≈ K8s 原生、Service 驱动的 keepalived。

---

## 10. 自检（D2）

- [x] 能说出 Controller / Speaker 各做什么
- [x] 能画 L2 与 BGP 流量路径差异
- [x] 能说明 MetalLB 与 CNI、kube-proxy 的分工
- [x] 能一句话对比 Ingress（L7）与 LoadBalancer+MetalLB（L4）
- [x] 现网已确认：**Layer2 + first-pool + node6 宣告 + iot-web:190**
- [ ] 能说明 **strictARP** 适用场景（§7.2）
- [ ] 能对比 **云 LB / keepalived**（§9）
- [ ] 能排查 **Pending** 与 **VIP 通业务不通**（§8.6、§8.7）

---

## 11. 面试复习（题 ↔ 笔记双向对照）

| 题清单 | 笔记章节 |
|--------|----------|
| 1、6、F1 | §4、§5、§6、§9 |
| 2、25、30 | §4、§4.1 |
| 3、26 | §4.1、§5 |
| 4、5.1 | §5.1 |
| 5、18、F2 | §7.2 |
| 6、7 | §9 |
| 8、22、23、33 | §3、§3.1、§8.2 |
| 9、28 | §2、§8.1 |
| 10、21 | §7 |
| 11、32 | §7、§7.1、§8.4 |
| 12、34 | §8.7、§8.1、§8.5 |
| 13、29 | §3.1、§8.3 |
| 14、30 | §4、§4.1 |
| 15 | §4.2 |
| 16 | §8.8 |
| 17、19、24 | §7.1、§8.4 |
| 20 | §8.3、§8.4 |
| 31 | §8.6 |
| F3～F5 | §6.1、§7.2 |

- 题清单（39 题）：[`../interview/MetalLB_面试题清单.md`](../interview/MetalLB_面试题清单.md)  
- 答案：[`../interview/answers/MetalLB_答案.md`](../interview/answers/MetalLB_答案.md)

## 12. 参考

- MetalLB 概念：https://metallb.universe.tf/concepts/
- L2：https://metallb.universe.tf/concepts/layer2/
- BGP：https://metallb.universe.tf/concepts/bgp/

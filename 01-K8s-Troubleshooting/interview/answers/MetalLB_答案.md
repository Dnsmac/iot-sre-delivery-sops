# MetalLB 面试题参考答案

> 忘词时查本文件。回答控制在 **30～90 秒**，先结论后原理，最后可带一句现网例子。  
> 现网锚点：`meta/iot-web` → `192.168.27.190`，池 `first-pool`，**Layer2**，Event 显示 **node6** 宣告。

---

## 一、你今天看到的 8 题

### 1. MetalLB 有哪两种模式？区别是什么？

**答：**

| 模式 | 怎么对外宣告 VIP | 流量入口 | 优点 | 缺点 |
|------|------------------|----------|------|------|
| **Layer2** | 选举 Leader，用 **ARP** 把 VIP 的 MAC 指到某一节点 | 先进 **单个 Leader 节点** | 配置简单，不依赖路由器 | Leader 带宽瓶颈；故障转移慢（ARP 缓存） |
| **BGP** | 各节点 Speaker 与上游路由器 **BGP 对等**，宣告 VIP 路由 | 路由器 **ECMP** 到多节点 | 多节点分担流量，扩展性好 | 要配 AS、Neighbor、认证；依赖网络设备 |

**共同点**：都只解决 **L4 VIP 分配与宣告**；Pod 间转发仍靠 **CNI**，Service 到 Pod 靠 **kube-proxy**。

---

### 2. Layer2 模式的 Leader 是怎么选举的？

**答：**

- 每个节点跑 **Speaker**（DaemonSet）。
- Speaker 之间用 **memberlist（gossip）** 协调，对**每个 VIP** 选举出一个 **Leader**。
- 只有 Leader 对该 VIP 回 **ARP**，把「VIP → 本机 MAC」告诉局域网。
- Leader 挂了，其他 Speaker 重新选举，新 Leader 开始 ARP 宣告。

**现网验证**：`kubectl describe svc iot-web -n meta` 的 Events 里可见  
`announcing from node "node6" with protocol "layer2"`。

---

### 3. 为什么说 Layer2 有单点瓶颈？如何优化？

**答：**

**原因：**

- 同一时刻，一个 VIP 在 L2 下通常只有 **一个 Leader** 接收发往该 VIP 的入口流量。
- 所有南北向流量先进 Leader，再由 **kube-proxy** 转后端 Pod → **Leader 网卡/CPU 易成瓶颈**。
- 故障转移时要换 Leader，还受 **客户端 ARP 缓存** 影响，短时间内可能不通或走错节点。

**优化：**

1. **改用 BGP + ECMP**：流量由路由器分到多节点（需网络支持）。
2. **水平拆 VIP**：不同业务/环境用不同 Service、不同 VIP（你们 `meta` / `meta-test` / `meta-biz` 各一个 IP）。
3. **增加 Leader 节点网卡带宽**、优化后端 Pod 数量与资源。
4. **接受 L2 用于中小流量**，大流量场景规划 BGP。

---

### 4. BGP 模式下，为什么节点故障会导致丢包？

**答：**

- BGP 依赖 **路由收敛**：节点宕机后，Speaker 撤回宣告，路由器更新表项需要时间（秒级到数十秒）。
- 收敛期间，路由器仍可能把包发给 **已故障节点** → **短暂丢包**。
- 若 **ECMP 哈希** 到坏节点，也会丢包直到会话重算或路由更新。
- 应用层无重试时，表现为连接超时、MQTT 断连等。

**对比 L2**：L2 是 ARP 缓存刷新慢；BGP 是 **路由收敛** 慢，原因不同，都可能短时丢包。

---

### 5. 什么情况下需要开启 strictARP？

**答：**

- 主要和 **kube-proxy 使用 IPVS 模式** 且集群里跑 **MetalLB Layer2** 有关。
- 部分 CNI（如 **Calico**）在 IPVS + ARP 场景下，需要节点对 ARP 行为更严格，避免 **ARP 响应混乱**（例如本不应响应的节点回了 VIP 的 ARP）。
- **strictARP** 常在 Calico 等配置里设为 `true`，让非 Leader 不要乱应答 VIP 的 ARP。

**面试句**：  
「若 CNI 文档要求（常见于 Calico + IPVS + MetalLB L2），要在 CNI 配置开 strictARP，避免多节点 ARP 冲突导致 VIP 漂移异常。」

**若被追问你们集群**：看 Calico/Cilium 文档及 `kube-proxy` 模式：`kubectl get cm kube-proxy -n kube-system -o yaml | grep mode`。

---

### 6. MetalLB 和云厂商的 LoadBalancer 有什么区别？

**答：**

| 维度 | 云 LB（AWS ELB/阿里云 SLB 等） | MetalLB |
|------|--------------------------------|---------|
| 适用 | 公有云托管 K8s | **裸机、IDC、私有云** 无云 LB |
| 实现 | 云 API 分配 VIP/CLB，云控面管健康检查 | 集群内 Controller 分 IP，Speaker **ARP/BGP** |
| 集成 | `Service type=LoadBalancer` 自动调云 API | 同样 Service 类型，由 **MetalLB** 写 `status.loadBalancer` |
| 能力 | 常带 WAF、证书、跨 VPC | **仅 L4 VIP**，不管 L7 |
| 运维 | 云控制台计费、配额 | 自管 IP 池、路由器 BGP |

**一句**：API 一样都是 Kubernetes `LoadBalancer`，底层一个是云厂商，一个是 MetalLB。

---

### 7. Layer2 和 keepalived 有什么异同？

**答：**

| | keepalived (VRRP) | MetalLB Layer2 |
|---|-------------------|----------------|
| 场景 | 传统 VM/物理机 VIP 漂移 | **Kubernetes Service** 自动分配 VIP |
| 选举 | VRRP 主备 | Speaker **memberlist** 选 Leader |
| 宣告 | VIP 漂移到主节点 ARP | Leader 对 Service 的 VIP ARP |
| 与 K8s | 需手工配 VIP，和 Pod 生命周期脱节 | 监听 Service，**自动** 分配/释放 IP |
| 相似 | 都是 **ARP + 单活跃节点** 接收入口流量 | 同左 |

**一句**：L2 像「K8s 原生、按 Service 驱动的 keepalived」。

---

### 8. MetalLB 的 IP 地址从哪里来？

**答：**

- 来自你配置的 **IPAddressPool**（IP 段或 CIDR 列表）。
- **Controller** 在有 `type=LoadBalancer` 的 Service 时，从池中挑 **未占用** IP，写入 `status.loadBalancer.ingress.ip`。
- 注解可看到池名，例如：`metallb.universe.tf/ip-allocated-from-pool: first-pool`。
- **Speaker** 只负责宣告，**不分配** IP。

**现网**：VIP 在 `192.168.27.x`，池名 `first-pool`；`meta`/`meta-test`/`meta-biz` 各拿不同 IP。

---

## 二、补充高频题答案

### 9. Controller 和 Speaker 分别做什么？

- **Controller**：控制面；监听 Service；从 **IPAddressPool** 分配/回收 IP；更新 Service status。
- **Speaker**：数据面；DaemonSet 每节点一个；**L2** 时 ARP 宣告，**BGP** 时与路由器建会话宣告路由。

---

### 10. 外部流量从 VIP 到 Pod 的完整路径？分工？

```text
客户端 → VIP (MetalLB 宣告)
  → 入口节点 (L2: Leader / BGP: ECMP 任一节)
  → kube-proxy (iptables/ipvs)
  → Service ClusterIP / Endpoints
  → Pod IP (CNI 跨节点转发)
```

- **MetalLB**：只到「包进到某一节点」。
- **kube-proxy**：Service → Pod。
- **CNI**：Pod 之间、跨节点。

---

### 11. MetalLB 和 Ingress 区别？IoT 为什么常用 LB？

| | MetalLB (LB) | Ingress |
|---|--------------|---------|
| 层级 | **L4**（IP+端口） | **L7**（HTTP/HTTPS 路由） |
| 协议 | 任意 TCP/UDP（如 **1883 MQTT**） | 主要是 HTTP(S) |
| IoT | **MQTT、自定义 TCP** 直接暴露端口 | Ingress 通常不管 1883，除非特殊 TCP Ingress |

**现网**：`iot-web` 同时 `80` 和 `1883`，用 **LoadBalancer** 合理。

---

### 12. LoadBalancer 一直 Pending 怎么排查？

1. 是否安装 MetalLB：`kubectl get pods -n metallb-system`
2. 是否有 **IPAddressPool**、L2Advertisement/BGPAdvertisement
3. Controller 日志是否报错「无可用 IP」
4. Service 是否 `type: LoadBalancer`
5. 云集群误用 MetalLB 或相反——环境要匹配

---

### 13. IPAddressPool？多环境多 VIP？

- **IPAddressPool**：声明可用 IP 段（如 `192.168.27.190-200`）。
- **L2Advertisement / BGPAdvertisement**：哪些池用哪种模式宣告。
- 多环境：**每个 NS 一个 LB Service**，Controller 从同池或不同池分配 **不同 IP**（你们 meta / meta-test / meta-biz 三个 VIP）。

---

### 14. Layer2 故障转移多久？

- 新 Leader 选举：约 **gracePeriod 1～5s**（配置相关）。
- 客户端更新 ARP：**数秒～30s+**（看 OS/缓存）。
- 面试答：**秒级到数十秒**，生产要配合应用重连、MQTT keepalive。

---

### 15. 删 Pod 不能当故障转移测试？Leader 宕机呢？

- 删 **后端 Pod**：只测 kube-proxy 转发，**不切换** MetalLB Leader。
- 要测 MetalLB：让 **当前 Leader 节点宕机或 speaker 不可用**，再看 VIP 是否改到别的节点宣告。

---

### 16. 如何确认当前哪个节点在宣告 VIP？

```bash
kubectl describe svc <lb-svc> -n <ns>
# Events: announcing from node "node6" with protocol "layer2"
```

---

### 17. 为什么既有 EXTERNAL-IP 又有 NodePort？

- `LoadBalancer` 类型 Service **兼容保留 NodePort**（K8s 默认行为）。
- 对外主要用 **EXTERNAL-IP（VIP）**；NodePort 便于调试或没有 LB 时的备用入口。
- 生产 IoT 设备应连 **VIP:1883**，不是随便 NodePort。

---

### 18. iptables 和 ipvs 对 MetalLB 的影响？

- MetalLB 把包送到节点后，由 **kube-proxy** 规则转发。
- **ipvs** 性能通常更好；与 Calico 组合时可能需 **strictARP**（见第 5 题）。
- MetalLB 不替代 kube-proxy。

---

### 19. 裸机为什么需要 MetalLB？不用 NodePort？

- **NodePort**：要访问 `任意节点IP:高位端口`，端口范围受限，防火墙难管，不适合给 **设备固定入口**。
- **LoadBalancer + MetalLB**：业务侧固定 **VIP + 标准端口（80/1883）**，更接近生产交付。

---

### 20. 你们项目 iot-web LB 怎么讲？（ flagship 简版）

> 我们是裸机 K8s，用 **MetalLB Layer2**，地址池 **first-pool**，网段 **192.168.27.x**。  
> 生产 `meta/iot-web` 分配 **192.168.27.190**，同时暴露 **80** 和 **1883**，后端 3 副本。  
> describe 可见 **node6** 以 **layer2** 宣告 VIP。测试、业务环境用不同 NS 各拿独立 VIP，隔离清晰。  
> 流量路径：客户端 → VIP → Leader 节点 kube-proxy → Pod；Pod 间仍走 CNI。

---

## 三、追问陷阱简答

| # | 简答 |
|---|------|
| F1 | L2 入口单 Leader 有瓶颈；BGP 可多节点，但收敛期仍可能丢包，不是银弹。 |
| F2 | 多节点错误 ARP 同一 VIP → 流量漂移、间歇不通；故可能要 strictARP。 |
| F3 | 不能。MetalLB 只做 L4；L7 用 Ingress。 |
| F4 | 一般 **一个 Service 一个 VIP**；不要多 Service 硬共用一个 IP（除非非常规配置）。 |
| F5 | 不是。Calico BGP 是 **Pod 网段** 路由；MetalLB BGP 宣告的是 **Service VIP**。 |

---

## 四、来自 D2 笔记的补充题答案（§四 21～34）

### 21. MetalLB 负责什么、不负责什么？

| 负责 | 不负责 |
|------|--------|
| 为 `LoadBalancer` Service **分配 VIP** | **Pod 之间**组网（CNI） |
| 在节点上 **宣告 VIP**（L2 ARP / BGP 路由） | **Service → Pod** 转发（kube-proxy） |
| 写 `status.loadBalancer.ingress.ip` | **L7** 路由、TLS、域名（Ingress） |

**口诀**：MetalLB 管 **南北向 VIP 进门**；进门之后靠 **kube-proxy + CNI**。

---

### 22. 创建 LoadBalancer Service 后的完整流程？

```text
1. 用户 apply Service (type=LoadBalancer)
2. Controller 监听到 Service
3. 从 IPAddressPool 选空闲 IP
4. 写入 Service.status.loadBalancer.ingress.ip（及池注解）
5. Speaker 在节点上宣告 VIP（L2: ARP / BGP: 路由）
6. 外部可访问 VIP:Port → 入口节点 kube-proxy → Endpoints → Pod
```

**面试强调**：分配 IP 是 **Controller**，宣告 IP 是 **Speaker**，两步分工。

---

### 23. 注解 `metallb.universe.tf/ip-allocated-from-pool`？

- MetalLB 自动打在 Service 上。
- 表示该 VIP 从哪个 **IPAddressPool** 分配（你们现网：`first-pool`）。
- 排查「IP 从哪来、池是否用尽」时看这个注解。

---

### 24. 为何同时有 ClusterIP 和 EXTERNAL-IP？

- **LoadBalancer** 类型在 K8s 里 **继承** ClusterIP（集群内仍用 `10.x` 访问）。
- **EXTERNAL-IP** 是 MetalLB 分配的 **VIP**，给集群外/设备用。
- **集群内** Pod 互访：通常走 **ClusterIP** 或 DNS 服务名。  
- **集群外** 设备：走 **VIP**（如 `192.168.27.190:1883`）。

---

### 25. memberlist / gossip 的作用？

- Speaker 之间用 **memberlist（gossip）** 维护集群成员视图、协调 **每个 VIP 的 Leader 选举**。
- **不是 etcd**：etcd 管 K8s 对象；memberlist 只在 MetalLB Speaker 间用。
- 与 **VRRP**：目的一样（选主），协议不同；MetalLB 按 **Service/VIP** 粒度选举，和 K8s 生命周期集成。

---

### 26. ECMP 是什么？如何缓解 L2 瓶颈？

- **ECMP（等价多路径路由）**：路由器把到同一 VIP 的流量 **哈希到多条下一跳**（多个节点）。
- BGP 模式下各节点都宣告 VIP 路由 → 路由器 **多节点分担入口流量** → 避免 L2 **单 Leader** 网卡打满。
- **前提**：上游路由器支持 ECMP 且配置正确。

---

### 27. BGP 上游要配什么？为何非开箱即用？

**一般要配：**

- 本端/对端 **AS 号**
- **Neighbor** 邻居 IP
- 可选 **MD5** 认证
- **路由过滤**（只宣告允许的 VIP 段）

**非开箱即用**：要网络工程师在 **交换机/路由器** 上配合，K8s 侧只跑 Speaker 不够。

---

### 28. Speaker 为何 DaemonSet？Controller 为何 1 个？

| 组件 | 部署 | 原因 |
|------|------|------|
| **Speaker** | DaemonSet | **每个节点**都可能成为 L2 Leader 或 BGP 宣告点，必须每节点一份 |
| **Controller** | 通常 1 副本 Deployment | **控制面**分配 IP，有 leader 选举即可，不需每节点一份 |

**现网**：6 节点 → 6 个 Speaker + 1 个 Controller。

---

### 29. 同池多环境多 VIP 会冲突吗？

- **不会**：Controller 从 `first-pool` 选 **未占用** IP，每个 LoadBalancer Service 一个 VIP。
- 你们：`meta` .190、`meta-test` .197、`meta-biz` .193 — **一服务一 VIP**。
- **隔离**：靠 **Namespace + 不同 Service + 不同 VIP**，不是共用一个 Service。

---

### 30. gracePeriod 和 ARP 缓存对转移时间的影响？

| 阶段 | 时间量级 | 说明 |
|------|----------|------|
| **gracePeriod** | 约 1～5s | Speaker 判定旧 Leader 失效、选出新 Leader |
| **ARP 缓存** | 数秒～30s+ | 客户端/网关仍把 VIP 指旧 MAC，直到刷新 |

**总转移**：通常 **秒级到数十秒**；MQTT 要靠 **keepalive/重连** 扛过去。

---

### 31. VIP 正常但访问不通，和 Endpoints 有关吗？

**有关。** MetalLB 只保证 **包进到集群入口节点**；之后靠 **kube-proxy → Endpoints → Pod**。

**排查顺序：**

```bash
kubectl get endpoints iot-web -n meta          # 是否有后端 IP
kubectl get pods -n meta -l <selector>       # Pod 是否 Ready
kubectl describe svc iot-web -n meta         # Events：MetalLB + 端口
kubectl logs <backend-pod>                   # 应用是否监听 80/1883
```

**现象分离**：Events 有 `layer2 announcing` 但 endpoints 为空 → **后端问题**，不是 MetalLB。

---

### 32. 三种 Service 类型区别？IoT 为何用 LB？

| 类型 | 访问方式 | 典型场景 |
|------|----------|----------|
| **ClusterIP** | 仅集群内 | 内部微服务互调 |
| **NodePort** | 节点 IP + 高位端口 | 测试、临时暴露 |
| **LoadBalancer** | **固定 VIP + 标准端口** | 生产设备、MQTT **1883** |

IoT 设备需要 **稳定 VIP 和标准端口**，故用 **LB + MetalLB**，不用让设备记 NodePort。

---

### 33. IPAddressPool、L2Advertisement、BGPAdvertisement 关系？

```text
IPAddressPool     → 定义「有哪些 IP 可分配」
L2Advertisement   → 声明「某池用 Layer2 方式宣告」（ARP）
BGPAdvertisement  → 声明「某池用 BGP 方式宣告」（走路由器）
```

- 一个池可被一种或多种 Advertisement 引用（看配置）。
- 你们现网：**Layer2** + 池名 **first-pool**（从 Service 注解可见）。

---

### 34. 如何检查 metallb-system 是否正常？

```bash
# 1. 组件是否 Running
kubectl get pods -n metallb-system
# 期望：controller 1 个 Running；speaker 数 = 节点数（你们 6）

# 2. Service 是否分到 VIP
kubectl get svc -A | grep LoadBalancer

# 3. 是否正在宣告
kubectl describe svc iot-web -n meta
# Events: announcing from node "xxx" with protocol "layer2"

# 4. Controller 日志（分配失败时）
kubectl logs -n metallb-system -l app=metallb,component=controller --tail=50
```

**异常常见原因**：池耗尽、无 L2Advertisement、Speaker 未 Ready、Service 不是 LoadBalancer。

---

## 五、复习检查（一周后）

- [ ] §一 8 题闭卷口述  
- [ ] §四 21～34 能答核心点（尤其 21、22、24、31、34）  
- [ ] 第 20 题带 .190 / node6 / 1883  
- [ ] 能画 L2 vs BGP 路径图  
- [ ] strictARP + Calico+IPVS（第 5 题）  


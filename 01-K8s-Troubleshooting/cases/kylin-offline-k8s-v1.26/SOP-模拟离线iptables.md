# SOP · 模拟离线 iptables

| 字段 | 内容 |
|------|------|
| 场景 | 实验室模拟无外网（真实现场物理断网则不需要） |
| 现象 | 断外网后内网/集群异常；Spray :8080 不可达 |
| 影响 | 装簇控制台打不开；Pod 互通失败 |

## 1. 时机

- **装簇成功、pre-cluster 完成后再断外网**
- 中间件安装过程中不要改 iptables / 不要 restart kubelet

## 2. 快速定界

```bash
iptables -L OUTPUT -n -v | head -20
iptables -L FORWARD -n -v | head -20
sysctl net.ipv4.ip_forward
ping -c1 192.168.27.105
ping -c1 -W2 8.8.8.8
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.27.109:8080/
```

## 3. 根因

- OUTPUT DROP 未放行内网 / Service(`10.233`) / Pod(`10.234`) / nodelocaldns
- **109 Docker**：缺 `ip_forward` + `172.17.0.0/16` FORWARD → Spray 8080 不通
- 网段写错（曾把 `27` 写成 `127`）→ 内网也被 DROP

## 4. 修复（网段按现场改）

**K8s 节点：**

```bash
iptables-save > /tmp/iptables.bak
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -d 192.168.27.0/24 -j ACCEPT
iptables -A OUTPUT -d 127.0.0.0/8 -j ACCEPT
iptables -A OUTPUT -d 10.233.0.0/16 -j ACCEPT
iptables -A OUTPUT -d 10.234.0.0/16 -j ACCEPT
iptables -A OUTPUT -d 169.254.25.10 -j ACCEPT
iptables -A OUTPUT -j DROP
iptables -I INPUT -d 169.254.25.10 -p tcp --dport 9254 -j ACCEPT
```

**Spray/Docker 机（109）额外：**

```bash
sysctl -w net.ipv4.ip_forward=1
iptables -I FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -I FORWARD -s 172.17.0.0/16 -j ACCEPT
iptables -I FORWARD -d 172.17.0.0/16 -j ACCEPT
iptables -I FORWARD -s 192.168.27.0/24 -j ACCEPT
iptables -I FORWARD -d 192.168.27.0/24 -j ACCEPT
# 再加与节点相同的 OUTPUT/INPUT
```

交付脚本：`lab-offline-iptables.sh k8s-node|nfs-spray`（读 `SUBNET_CIDR`）。

## 5. 验证

- 内网 ping OK；外网 ping 失败  
- 109：`curl` Spray 8080 有响应  

## 6. 防复发

- 改网段后用 `-I` 插入 ACCEPT（必须在 DROP 前）  
- 只执行一次；恢复用 `iptables-restore`

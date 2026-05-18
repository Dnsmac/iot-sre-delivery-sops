# {故障名称} 排查 SOP

| 字段 | 内容 |
|------|------|
| 场景 | 生产/演练 |
| 现象 | |
| 影响 | |
| 开始时间 | |

## 1. 快速定界（≤5min）

```bash
# 替换为实际命名空间/Pod
kubectl get pods -n <ns> -o wide
kubectl describe pod <pod> -n <ns>
kubectl logs <pod> -n <ns> --previous
kubectl top pod -n <ns>
kubectl get events -n <ns> --sort-by='.lastTimestamp'
```

| 命令 | 用途 | 本次关键输出 |
|------|------|--------------|
| | | |

## 2. 根因

- 结论：
- 证据（日志/Events 片段）：

## 3. 修复

| 动作 | 命令/配置 | 风险 |
|------|-----------|------|
| | | |

## 4. 验证

```bash
kubectl get pod <pod> -n <ns>
# 预期：READY 1/1，RESTARTS 不持续增长
```

## 5. 防复发

- 参数/资源限制：
- 监控/告警：

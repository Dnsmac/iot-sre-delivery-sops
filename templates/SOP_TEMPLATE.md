# {故障名称} 排查 SOP

| 字段 | 内容 |
|------|------|
| 场景 | 生产/演练 |
| 现象 | |
| 影响 | |
| 开始时间 | |

## 1. 快速定界（≤5min）

```bash
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
- 证据：

## 3. 修复

| 动作 | 命令/配置 | 风险 |
|------|-----------|------|
| | | |

## 4. 验证

```bash
kubectl get pod <pod> -n <ns>
```

## 5. 防复发

- 参数/资源限制：
- 监控/告警：

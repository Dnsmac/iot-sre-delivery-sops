# Inbox — 零登录粘贴 JD（公司网络可用）

> **不登录**猎聘/BOSS：在手机或回家复制 JD，粘贴到本目录，再跑 `run.py --week YYYY-W__`。

## 文件名

- 推荐：`2026-W22.txt`（与 `--week` 一致）
- 或任意 `*.txt`（程序会合并读取）

## 格式（复制改）

```text
[iot_java_isv]
资深 Java 物联网开发 | 某ISV公司 | 22-28k | 统招本科 深圳

[byd_java_iot]
Java高级工程师 设备对接 | 比亚迪汽车工业 | 20-30k | K8s 物联网

[industrial_java]
Java后端 MES | 某工业软件 | 18-26k |

# 以 # 开头为注释；空行忽略
```

**字段**：`标题 | 公司 | 薪资 | 标签(可选)` — 用英文竖线 `|` 分隔。

## 每周流程（公司网）

1. 午休/回家用 **5～10min** 复制 3～8 条 JD 进 `2026-W22.txt`
2. 公司电脑：

```powershell
cd D:\demo\iot-sre-delivery-sops\tools\industry-radar
py -3 run.py --week 2026-W22
```

3. 只读 L1：`05-Interview-Prep/行业雷达/方向/2026-W22.md`

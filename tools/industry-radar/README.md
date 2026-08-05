# 职业方向雷达（零登录默认 · 公司网络可用）

> **公司网不能登录猎聘** → 默认 **inbox 粘贴 + 公开页**，无需 Playwright。

## 安装（一次性）

```powershell
cd D:\demo\iot-sre-delivery-sops\tools\industry-radar
py -3 -m pip install pyyaml jinja2
```

**不需要** `playwright install`（除非在家用 `--liepin`）。

## 每周（公司网络 · 推荐）

### 1. 粘贴 JD（5～10min，手机/回家复制）

编辑 [`inbox/2026-W22.txt`](inbox/2026-W22.txt)（格式见 [`inbox/README.md`](inbox/README.md)）：

```text
[byd_java_iot]
Java开发 物联网 | 比亚迪 | 20-30k | 一类本科
```

### 2. 跑脚本（~10 秒）

```powershell
py -3 run.py --week 2026-W22
```

### 3. 只读 L1（≤5min）

`05-Interview-Prep/行业雷达/方向/2026-W22.md`

---

## 命令一览

| 命令 | 登录 | 说明 |
|------|------|------|
| `py -3 run.py --week 2026-W22` | **否** | inbox + 公开页（默认） |
| `py -3 run.py --week 2026-W22 --inbox-only` | **否** | 仅读 inbox |
| `py -3 run.py --demo --week 2026-W22` | **否** | 样本数据 |
| `py -3 run.py --login liepin` | 要 | **仅在家** |
| `py -3 run.py --week 2026-W22 --liepin` | 要 | 在家采集猎聘 |

公开页抓失败时自动用 `fixtures/public_fallback.json`，**以 inbox 粘贴为准**。

## 输出

| 层 | 路径 |
|----|------|
| **L1** | `05-Interview-Prep/行业雷达/方向/YYYY-W__.md` |
| L2 | `05-Interview-Prep/行业雷达/详情/YYYY-W__/` |
| raw | `out/raw/YYYY-W__.json` |

设计：[`docs/superpowers/specs/2026-05-30-career-direction-radar-design.md`](../../docs/superpowers/specs/2026-05-30-career-direction-radar-design.md)

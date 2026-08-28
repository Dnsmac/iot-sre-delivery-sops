# 简历文件说明（只看这里）

> 更新：2026-08-28

## 你要用哪个？

| 用途 | 文件 | 说明 |
|------|------|------|
| **通用投递 / 甲方转正（主用）** | [`投递/骆峰-Java后端-IoT.pdf`](投递/骆峰-Java后端-IoT.pdf) | 内容最全（含 OpenAPI TPS、ARM64 麒麟、MQTT 水位细节） |
| **偏 K8s / 交付岗投递** | [`投递/骆峰-Java后端-IoT-k8s.pdf`](投递/骆峰-Java后端-IoT-k8s.pdf) | 突出 k8s 压测排障与国产化交付（原版，留档） |
| **k8s 优化版（推荐）** | [`投递/骆峰-Java后端-IoT-k8s-v2.pdf`](投递/骆峰-Java后端-IoT-k8s-v2.pdf) | 在 k8s 版基础上补定位标签、拆长句、补关键数字；源文件 [`投递/骆峰-Java后端-IoT-k8s-v2.html`](投递/骆峰-Java后端-IoT-k8s-v2.html) |
| 改内容 | 对应 `.html` | 改完 HTML 再导出 PDF（命令见下） |
| **外包平台备案（旧）** | `D:\鸿讯文件\java开发 - 骆峰.pdf` | 鸿讯登记用，**已过时，勿当主简历** |
| 历史版本 | [`archive/`](archive/) | 迭代备份，勿投（见 [`archive/README.md`](archive/README.md)） |

```text
05-Interview-Prep/resume/
├── README.md                 ← 本文件
├── 投递/                     ← ★ 对外只用这里
│   ├── 骆峰-Java后端-IoT.html / .pdf      （通用版）
│   ├── 骆峰-Java后端-IoT-k8s.pdf          （k8s 版，原版）
│   ├── 骆峰-Java后端-IoT-k8s-v2.html/.pdf （k8s 优化版）
│   └── 骆峰-Java后端-IoT-v2.pdf           （历史变体）
├── 甲方备案/                 ← 外包/背调专用口径
│   └── README.md
└── archive/                  ← 历史备份，勿投
    └── README.md + （旧版 html/pdf）
```

## 版本区别（一句话）

| 版本 | 写法 |
|------|----------------|
| **投递-通用版** | 内容最全：工作经历带定位标签；IoT 项目含 OpenAPI 五接口 TPS、MQTT 水位拒连（eventloop System.gc）、麒麟 ARM64/死 IP 收敛细节 |
| **投递-k8s 版** | 突出「10 万级 k8s 压测排障（ES NFS / buffer 积压 / Camellia / R2dbc）+ 麒麟离线交付」；工作经历无定位标签 |
| **投递-k8s-v2（优化版）** | k8s 版基础上：恢复工作经历定位标签；拆「10 万级」长句为 ES/NFS 与中间件连接层两条；补 OpenAPI 五接口 TPS、OOM Dominator 数字、麒麟 ARM64/26 处 IP；压测表述统一为「长稳 96h」 |
| **甲方备案版** | 拆成 **一家技术 + 谚礼**（与银行流水/劳务协议一致，鸿讯要时用） |

背调若问到 2022 年后主体：口述「同一项目、后期远程、薪资走谚礼」，投递版简历不必写两家。

## 导出 PDF

在项目根目录执行（或浏览器打开 HTML → 打印 → 另存 PDF）：

```powershell
$html = "file:///D:/project/iot-sre-delivery-sops/05-Interview-Prep/resume/投递/骆峰-Java后端-IoT-k8s-v2.html"
$pdf  = "D:\project\iot-sre-delivery-sops\05-Interview-Prep\resume\投递\骆峰-Java后端-IoT-k8s-v2.pdf"
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="$pdf" "$html"
```

## 更新记录

| 日期 | 动作 |
|------|------|
| 2026-08-28 | 新增 k8s 优化版（v2：HTML+PDF）；README 补齐投递各版本说明；根目录旧版 PDF 移入 archive 并加说明 |

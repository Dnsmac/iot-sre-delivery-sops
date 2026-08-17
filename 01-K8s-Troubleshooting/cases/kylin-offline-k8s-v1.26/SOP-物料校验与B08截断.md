# SOP · 物料校验 / B08 截断 / /tmp 满

| 字段 | 内容 |
|------|------|
| 场景 | 上传 bundles、解压、sha256 校验 |
| 现象 | unrar checksum error；B08 仅 32KB；sha256 `$'\r'`；extract 无空间；B00 未出现在校验结果 |

## 1. 快速定界

```bash
ls -lh /root/bundles/bundle-08-images.tar.gz   # 正常约 6.3G，异常见 32K
df -h / /tmp
du -sh /tmp/* 2>/dev/null | sort -hr | head
# 看首行是否带 BOM（开头出现 357 273 277）
sed -n '1,3p' /root/bundles/CHECKSUMS.sha256 | od -c | head
```

## 2. 根因

| 现象 | 根因 |
|------|------|
| Unexpected end of archive | rar/拷贝 **截断** |
| B08=32KB | 解压失败残留 |
| 「1 行格式不适当」且 **B00 未校** | CHECKSUMS 首行 **UTF-8 BOM**（`EF BB BF`）和/或 **CRLF** |
| 设备没有空间 | `/tmp` 是 **tmpfs**，被 `bundles.rar` 占满 |

## 3. 修复

```bash
rm -f /tmp/bundles.rar
df -h /tmp

rm -f /root/bundles/bundle-08-images.tar.gz
# 重传完整 B08 + 新 CHECKSUMS（与 B00 同批；新 CHECKSUMS 应无 BOM）

cd /root/bundles
sed -i 's/\r$//' CHECKSUMS.sha256
sed -i '1s/^\xEF\xBB\xBF//' CHECKSUMS.sha256
sha256sum -c CHECKSUMS.sha256
# 必须看到：bundle-00-common.tar.gz: 成功
```

角色解压：

```bash
# 109
bash /root/bundles/extract-bundles.sh nfs-spray /root/bundles
# 110
bash /root/bundles/extract-bundles.sh harbor /root/bundles
# 105～108
bash /root/bundles/extract-bundles.sh k8s-node /root/bundles
```

109 **不必**放 B06/B08/B09（省空间）。

## 4. 防复发

- 大包用目录 `scp`/`rsync`，少用整包 rar  
- 传完先 `ls -lh` 看 B08 体积再解压  
- B00 更新必须 **连同 CHECKSUMS** 一起传  
- 打包脚本写 CHECKSUMS 禁用 UTF-8 BOM（v1.0.17+）

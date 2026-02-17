# 远程工作站服务器使用说明（Markdown 版）

## 1. 服务器概况
- 系统：Ubuntu Server 24.04 LTS（Headless，无图形界面）
- 主要用途：量化研究、数据处理、模型训练、回测任务
- 长期在线，可远程访问

## 2. 关键配置
- CPU：Intel Xeon W-2145（8C16T，3.70GHz，最高 4.50GHz）
- 内存：64GB DDR4 ECC
- 存储：1TB NVMe SSD（LVM 可扩展）
- GPU：已安装独立显卡（当前未配置 NVIDIA 驱动/CUDA）

## 3. 连接方式
### 3.1 局域网（同一路由器）
- IP：`10.0.0.193`

### 3.2 全球远程访问（推荐）
- Tailscale IP：`100.66.103.44`

## 4. 新用户接入步骤
1. 安装 Tailscale：<https://tailscale.com/download>
2. 使用授权账号登录并加入对应 Tailnet
3. 确认 Tailscale 状态为 `Connected`
4. 在终端执行：

```bash
ssh 用户名@100.66.103.44
```

示例：

```bash
ssh friend1@100.66.103.44
```

首次连接如果出现：

```text
Are you sure you want to continue connecting (yes/no)?
```

输入 `yes` 即可。

登录成功后会看到类似提示符：

```text
friend1@dell5820:~$
```

## 5. 安全机制
- SSH 已启用并开机自启
- 防火墙已开启（仅开放 SSH）
- 通过 Tailscale 私有网络访问，非授权设备不可连接

## 6. 使用规范
- 在个人目录操作：`/home/你的用户名/`
- 不执行高风险系统命令（删除系统目录、格式化磁盘等）
- 不随意使用 `sudo`（除非明确授权）
- 不确定命令作用时先确认

## 7. 连接信息速记
- 远程 IP：`100.66.103.44`
- 登录命令：`ssh 用户名@100.66.103.44`
- 账号密码：单独分发

## 8. 无法连接时排查
1. Tailscale 是否已登录且为 `Connected`
2. 是否已加入正确 Tailnet
3. 用户名/密码是否正确
4. 当前网络是否限制 VPN（部分公司/学校网络会限制）

如果仍失败，请提供终端完整报错信息用于定位。

## 9. 本机与工作站同步规范（建议）
- 代码/文档：使用 Git 同步（更稳、可追溯、可回滚）
- 数据/结果/日志：使用 `rsync` 同步（不建议放入 Git）

推荐流程：
1. 在本机改代码并 `git push`
2. 在工作站项目目录 `git pull`
3. 数据和结果按需用 `rsync` 单独同步

常用命令（本机执行）：

```bash
sync_push "docs: update workstation guide"
sync_pull_ws
sync_all "feat: update configs"
```

若未配置函数，可用基础命令：

```bash
# 本机
cd /Users/hui/quant_score/v4
git add -A
git commit -m "your message"
git push

# 工作站
ssh hui@100.66.103.44
cd ~/projects/hui-wang-multi-factor-research
git pull
```

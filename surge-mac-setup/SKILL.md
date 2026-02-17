---
name: surge-mac-setup
description: 在 Mac 上安装并配置 Surge 企业版翻墙代理。当用户提到"设置Surge"、"安装Surge"、"配置翻墙"、"setup VPN"、"onboarding VPN"、"配置代理"时触发。
allowed-tools: Bash(brew*), Bash(open*), Bash(surge-cli*), Bash(/Applications/Surge.app/*), Bash(pgrep*), Bash(defaults*), Bash(ls*), Bash(cat*), Bash(networksetup*), AskUserQuestion
---

# Surge Mac 企业版安装配置 Skill

## 概述

该 Skill 用于新同事 onboarding 时一键安装和配置 Surge Mac 企业版翻墙代理，流程包括：
1. 检查并安装 Surge
2. 引导用户注册 Surge 账号
3. 引导用户完成企业授权激活（GUI 操作）
4. 验证配置是否正确
5. 常见问题排查

## 工作流程

### 第一步：检查环境

检查 Homebrew 和 Surge 的安装状态：

```bash
# 检查 brew 是否可用
which brew

# 检查 Surge 是否已安装
ls /Applications/Surge.app 2>/dev/null && echo "Surge 已安装" || echo "Surge 未安装"

# 如果已安装，检查 Surge 是否正在运行
pgrep -x "Surge" && echo "Surge 正在运行" || echo "Surge 未运行"
```

### 第二步：安装 Surge

如果 Surge 未安装，通过 Homebrew 安装：

```bash
brew install --cask surge
```

> **重要：** Surge 必须安装在 `/Applications` 目录下，否则可能出现功能异常。Homebrew 默认安装到此目录。

如果 brew 未安装，提示用户先安装 Homebrew，或提供手动下载链接：
- 下载地址：https://dl.nssurge.com/mac/v4/Surge-latest.zip

### 第三步：注册 Surge 账号

使用 AskUserQuestion 询问用户是否已有 Surge 账号：

**选项：**
1. **已有账号** — 跳过注册，进入第四步
2. **没有账号** — 引导注册

如果需要注册，告知用户：
- 访问 https://auth.midway.run/
- 点击「一键注册」
- 记住注册后的用户名和密码

使用 AskUserQuestion 确认用户已完成注册后继续。

### 第四步：启动 Surge 并引导企业授权激活

> **注意：** 企业授权激活必须在 Surge GUI 中完成，无法通过命令行自动化。此步骤需要引导用户手动操作。

首先启动 Surge：

```bash
open -a Surge
```

然后使用 AskUserQuestion 引导用户完成以下 GUI 操作（一步一步来）：

**告知用户操作步骤：**

1. Surge 启动后，在界面中点击「**已经拥有授权？现在激活**」
2. 点击左下角「**企业授权**」
3. 填写激活信息：
   - **公司 ID**：`jike`
   - **用户名**：你的姓名拼音（在 https://auth.midway.run/ 首页查看）
   - **密码**：`jikesurge52202`
4. 点击激活

使用 AskUserQuestion 确认用户是否激活成功：

**选项：**
1. **激活成功** — 继续下一步
2. **提示"配置无效... 请联系管理员"** — 需要升级 Surge，回到第二步重新安装
3. **提示"You can only activate 3 devices at most"** — 引导用户去 https://auth.midway.run/ 清理不用的设备后重试
4. **其他错误** — 让用户描述错误信息，提供排查建议

### 第五步：验证配置

激活成功后，使用 surge-cli 验证配置状态：

```bash
SURGE_CLI="/Applications/Surge.app/Contents/Applications/surge-cli"

# 检查 Surge 是否正在运行
pgrep -x "Surge" && echo "✓ Surge 正在运行" || echo "✗ Surge 未运行"

# 检查当前配置文件
"$SURGE_CLI" dump profile effective 2>/dev/null | head -20

# 检查代理策略
"$SURGE_CLI" dump policy 2>/dev/null

# 检查环境信息
"$SURGE_CLI" environment 2>/dev/null
```

需要验证以下几项：
1. Surge 正在运行
2. 配置文件包含 Enterprise Profile
3. 代理策略列表非空

### 第六步：确认系统代理和出站模式

使用 AskUserQuestion 提醒用户检查状态栏：

**告知用户确认以下设置：**

右击 macOS 状态栏右上角的 Surge 图标，检查：
1. **出站模式** 应为「**规则判定**」
2. **系统代理** 应已开启（菜单中显示勾选）
3. **配置** 应选中「**Enterprise Profile**」

如果以上任一项不正确，指导用户通过 Surge 状态栏图标修改。

### 第七步：测试连接

验证翻墙是否正常工作：

```bash
# 通过 Surge 代理测试 Google 连通性
curl -s --max-time 10 -o /dev/null -w "%{http_code}" https://www.google.com
```

如果返回 200，说明翻墙配置成功。

如果失败，提供排查建议：
1. 检查 Surge 菜单栏 → 「切换配置」→「检查企业配置更新」
2. 使用 Surge 的测速功能检查当前代理节点是否可用
3. 如果当前节点不可用，选择其他代理节点

### 第八步：汇报结果

配置完成后，向用户汇报：
1. Surge 安装状态
2. 企业授权激活状态
3. 系统代理设置状态
4. Google 连通性测试结果

同时告知用户以下日常使用信息：
- **状态栏图标**：点击可快速切换代理开关和出站模式
- **测速**：右击 Surge 图标 → 「Benchmark」可测试所有节点速度
- **配置更新**：定期通过 Surge 图标 → 「切换配置」→「检查企业配置更新」更新配置
- **问题排查**：先确认出站模式为「规则判定」、系统代理已开启、Enterprise Profile 已选中

## 常见问题速查

| 问题 | 解决方案 |
|------|----------|
| 显示"配置无效... 请联系管理员" | 升级 Surge，重新安装最新版 |
| "You can only activate 3 devices at most" | 去 https://auth.midway.run/ 清理不用的设备 |
| 翻墙速度慢 | 1. 检查企业配置更新 2. 测速选择可用节点 3. 切换其他代理节点 |
| 提示不支持 RULE-SET | 这是 Clash X 的问题，需用 Clash X Pro 而非 Clash X |
| brew 命令报错 `brew cask` | 使用 `brew install --cask surge` 而非 `brew cask install surge` |

## 注意事项

- Surge 企业授权激活**只能通过 GUI 完成**，CLI 无法替代
- Surge 必须安装在 `/Applications` 目录下
- surge-cli 路径：`/Applications/Surge.app/Contents/Applications/surge-cli`
- 账号注册地址：https://auth.midway.run/
- 企业公司 ID 固定为 `jike`
- 企业密码固定为 `jikesurge52202`
- 用户名为个人姓名拼音，在 auth center 首页可查看

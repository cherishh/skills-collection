---
name: rime-ice-setup
description: 在 macOS 新机器上安装并配置雾凇拼音（rime_ice）。前提是用户已经自行安装好鼠须管（Squirrel.app）。Skill 负责下载/解压雾凇拼音、写入候选词数量与皮肤等个人定制、重新部署。当用户提到"配 Rime"、"装雾凇"、"装雾凇拼音"、"还原 Rime 配置"、"新机器装 Rime"、"setup rime_ice"、"rime 新机器" 时触发。
allowed-tools: Bash(ls*), Bash(test*), Bash(mkdir*), Bash(cp*), Bash(mv*), Bash(rm*), Bash(git*), Bash(file*), Bash(pgrep*), Bash(/Library/Input Methods/Squirrel.app/Contents/MacOS/Squirrel*), Read, Write, Edit, AskUserQuestion
---

# Rime Ice Setup — macOS 新机器一键还原

## 概述

在 macOS 新机器上重建主理人当前的雾凇拼音（rime_ice）+ 自定义补丁配置。

**前提条件**：用户已自行从 https://rime.im 或 App Store 下载安装鼠须管（Squirrel.app），并在 macOS "键盘 → 输入法" 中至少添加过一次 Squirrel，从而生成 `~/Library/Rime/` 目录。

**最终状态**：
- 雾凇拼音 latest release 已部署
- `default.custom.yaml`：候选词 7 个（`menu/page_size: 7`）
- `squirrel.custom.yaml`：候选横排（`candidate_list_layout: linear`）+ 跟随系统配色（`color_scheme: native` / `color_scheme_dark: native`）
- 输入法已重新部署，可立即使用

## 工作流程

### 第一步：环境检查（前置不齐就停下来，不替用户做）

1. 确认鼠须管已安装：
   ```bash
   test -x "/Library/Input Methods/Squirrel.app/Contents/MacOS/Squirrel" && echo OK
   ```
   如果不存在 → 告诉用户：去 https://rime.im/download/ 下载并安装鼠须管，安装完再来运行此 skill。**终止 skill**，不要自行下载安装。

2. 确认 Rime 用户目录存在：
   ```bash
   test -d "$HOME/Library/Rime" && echo OK
   ```
   如果不存在 → 告诉用户：打开 macOS"系统设置 → 键盘 → 输入法"，添加 Squirrel 并至少切换使用一次，让系统初始化用户目录。**终止 skill**，**不要**用 `mkdir` 自行创建 —— 自建的空目录会让 Squirrel 之后的部署找不到 `installation.yaml` 等系统初始化产物，行为难以预测。

### 第二步：克隆雾凇拼音并铺到用户目录

主理人实际使用的方法是 `git clone` 到临时子目录，然后把内容复制到 `~/Library/Rime/`，再删临时目录。**不**用 README 推荐的 `full.zip` 下载，也**不**用 plum。

```bash
cd "$HOME/Library/Rime"
git clone --depth 1 https://github.com/iDvel/rime-ice.git rime-ice-temp
cp -r rime-ice-temp/* .
rm -rf rime-ice-temp
```

> **为什么 `--depth 1`**：雾凇仓库带百万级词库 + 多年提交历史，全量 clone 几百兆。`--depth 1` 只拉最新 commit，几十兆几秒钟。
>
> **为什么 `cp -r .../*` 而不是直接 clone 到 `~/Library/Rime/`**：直接 clone 要求目标目录为空，但 Squirrel 首次启用后会留下 `installation.yaml` 这类系统文件。先 clone 到临时子目录再用 `*` glob 拷贝可以保留 `installation.yaml`，并且 glob **不**展开隐藏文件 —— `.git/` 不会跟过来，`~/Library/Rime/` 也就不会变成一个 git 工作目录。
>
> 副作用：失去了 `git pull` 增量更新雾凇的能力。下次更新雾凇要重跑此 skill —— 你的 `*.custom.yaml` 不会丢，因为雾凇仓库里没有同名文件，`cp -r` 不会碰它们。

**网络问题**：在中国大陆 `github.com` 直连可能慢。如果 clone 超时或失败：

- 让用户自查 `curl -I https://github.com` 是否通
- 临时走代理：`git -c http.proxy=http://127.0.0.1:7890 clone ...`（端口换成用户的）
- 换镜像：`git clone --depth 1 https://gh-proxy.com/https://github.com/iDvel/rime-ice.git rime-ice-temp`

核验关键文件已就位：

```bash
ls "$HOME/Library/Rime/rime_ice.schema.yaml" \
   "$HOME/Library/Rime/default.yaml" \
   "$HOME/Library/Rime/squirrel.yaml" >/dev/null && echo "雾凇就位 OK"
```

### 第三步：首次部署（让 Rime 认识新方案）

```bash
"/Library/Input Methods/Squirrel.app/Contents/MacOS/Squirrel" --reload
```

> 必须在写自定义补丁**之前**先部署一次，让 Rime 把 `default.yaml`、`squirrel.yaml` 这些"基线文件"识别为有效配置；之后再写 `*.custom.yaml` 补丁，下一次部署时才会被正确合并。
>
> 顺序反过来（先写 custom 再首部署）通常也能 work，但偶发 `build/` 目录半成品导致补丁不生效，强制走"基线 → 补丁 → 再部署"两步法最稳。

### 第四步：写入自定义补丁

**4.1 `default.custom.yaml`** — 候选词数量改成 7：

```yaml
patch:
  menu/page_size: 7
```

**4.2 `squirrel.custom.yaml`** — 横排候选 + 跟随系统配色：

```yaml
patch:
  style/candidate_list_layout: linear
  style/color_scheme: native
  style/color_scheme_dark: native
```

写入路径：`$HOME/Library/Rime/default.custom.yaml`、`$HOME/Library/Rime/squirrel.custom.yaml`。

> **为什么用 `*.custom.yaml` 补丁而不是直接改原文件？**
> 雾凇更新（重跑这个 skill）会覆盖 `default.yaml` / `squirrel.yaml`，但不会动 `*.custom.yaml` —— 因为雾凇仓库里**没有** `*.custom.yaml` 文件，第二步的 `cp -r` 就不会碰它们。补丁文件用 `patch:` + `/` 路径精准覆盖单一字段，不影响周围配置。
>
> **横排候选**用 `candidate_list_layout: linear`，不要写成 `text_orientation: horizontal`（那是文字本身方向，不是布局）。`native` 主题没有定义任何颜色字段，使 Squirrel 回退到 macOS 原生外观，自动跟随浅/深色模式。

### 第五步：重新部署

```bash
"/Library/Input Methods/Squirrel.app/Contents/MacOS/Squirrel" --reload
```

观察输出，如果有 YAML 解析错误会立刻报。

### 第六步：验证

让用户在任意文本框打字（例如 Spotlight 或备忘录），确认：

1. 默认输入方案是雾凇拼音（拼音输入能出中文候选）
2. 候选数量是 7 个（输入一个常见字如 `de` 看候选条）
3. 候选横排排列（不是上下堆叠）
4. 外观是 macOS 原生风格（浅色模式下浅底深字，切到深色模式自动反转）

如果不对：
- 候选数量错 → 检查 `default.custom.yaml` 路径和 YAML 语法
- 还是竖排 → 检查 `squirrel.custom.yaml`，并确认 Squirrel 进程读到了新配置（可以 `pkill Squirrel` 让系统重启输入法进程）
- 配色没切到 native → 同样 `pkill Squirrel`，新进程才会重新加载主题

## 后续维护提示

- 改候选数 / 切皮肤 → 编辑 `~/Library/Rime/*.custom.yaml`，然后 `Squirrel --reload`
- 更新雾凇词库 → 重跑此 skill；它会用 `git clone --depth 1` 拉最新版叠加覆盖到 `~/Library/Rime/`，`*.custom.yaml` 不会被动（雾凇仓库里没有这些文件）
- 备份用户词库（联想/自学习）→ `~/Library/Rime/rime_ice.userdb/` 是 LevelDB，跨机迁移需要先在源机 `Squirrel --sync` 导出到 `sync/` 目录，再拷贝过来 deploy

## 不在此 skill 范围内的事

- 安装鼠须管本体（用户必须先做）
- 配置 iCloud/坚果云等同步
- 调整字体大小、自定义皮肤颜色
- 安装/配置其他输入方案（双拼、五笔、emoji 等）—— 雾凇默认带了多个 schema，按 <kbd>F4</kbd> 切换即可

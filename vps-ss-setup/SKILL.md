# VPS Shadowsocks 部署 Skill（通用 VPS 公共版）

## 概述

该 Skill 用于在一台已有的空白 VPS 上一键部署翻墙服务，流程包括：
1. 通过 SSH 连接到用户提供的 VPS
2. 安装 Shadowsocks-libev 服务并设置开机自启
3. 部署 BBR+CAKE 网络加速 + 系统优化

> **前提条件：** 用户已有一台可通过 SSH 登录的 VPS（Ubuntu/Debian 系统），且具有 root 或 sudo 权限。

## 工作流程

### 第一步：确认连接参数

使用 AskUserQuestion 向用户确认以下参数（提供默认值供参考）：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `host` | VPS 的 IP 地址或域名 | （必填，无默认值） |
| `port` | SSH 端口 | `22` |
| `user` | SSH 登录用户名 | `root` |
| `auth` | 认证方式（密钥/密码） | 密钥（默认） |

> **说明：**
> - 如果用户使用密钥认证，确认是否需要指定密钥路径（`-i /path/to/key`）
> - 如果用户使用密码认证，后续 SSH 命令会提示输入密码
> - 如果用户名不是 root，后续命令会使用 `sudo`

### 第二步：测试 SSH 连接

先测试 SSH 连接是否正常：

```bash
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -p {port} {user}@{host} "echo 'SSH 连接成功' && uname -a && cat /etc/os-release | head -5"
```

如果指定了密钥路径：
```bash
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -i {key_path} -p {port} {user}@{host} "echo 'SSH 连接成功' && uname -a && cat /etc/os-release | head -5"
```

确认连接成功后继续。如果连接失败，提示用户检查 IP、端口、密钥/密码是否正确。

### 第三步：部署 Shadowsocks

构建 SSH 命令前缀（后续步骤复用）：

- 密钥认证：`SSH_CMD="ssh -o StrictHostKeyChecking=accept-new -p {port} -i {key_path} {user}@{host}"`
- 密码认证：`SSH_CMD="ssh -o StrictHostKeyChecking=accept-new -p {port} {user}@{host}"`
- 默认（root + 默认密钥）：`SSH_CMD="ssh -o StrictHostKeyChecking=accept-new {user}@{host}"`

根据用户是否为 root，选择合适的执行方式：
- root 用户：`$SSH_CMD "bash -s" << 'SCRIPT_EOF'`
- 非 root 用户：`$SSH_CMD "sudo bash -s" << 'SCRIPT_EOF'`

执行部署脚本：

```bash
$SSH_CMD "sudo bash -s" << 'SCRIPT_EOF'
#!/bin/bash
set -e

# 更新软件包索引
apt update -y

# 安装 shadowsocks-libev
apt install shadowsocks-libev -y

# 检查安装
dpkg -l | grep shadowsocks

# 配置 shadowsocks
CONFIG_FILE="/etc/shadowsocks-libev/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    touch "$CONFIG_FILE"
fi

cat > "$CONFIG_FILE" << 'CONFIG_EOF'
{
"server":["::0","0.0.0.0"],
"port_password": {
"7000": "Kx9mPqR3vT6wYb",
"7001": "Nf2hLsW8jD4cZa",
"7002": "Bg7nUoE1xQ5rMt",
"7003": "Hy3kVpA9iF6dWc",
"7004": "Jm8sXeG2uL4bRo",
"7005": "Tw6qZnC5yH1fKd",
"7006": "Pv4rMaI7oS3gUx",
"7007": "Wk9tBfJ2eN6hLq",
"7008": "Oc1yDgR5mX8pVs",
"7009": "Fa3wEiT7kQ4nZb",
"7010": "Gu6xHjY9lR2cMd",
"7011": "Ls8aKmV1oW5eNf",
"7012": "Qd4bPnX3rT7gUh",
"7013": "Yf2cSoZ6uI9jWk",
"7014": "Em5dVqA8wL1hXn",
"7015": "Ri7eBsC4xN3kYp",
"7016": "Uj9fDtF2yO6mZq",
"7017": "Wg1hGwH5aP8nAr",
"7018": "Xk3iIxJ7bQ9oCs",
"7019": "Zl5jKyL9cR1pEt",
"7020": "An7kMzN2dS3qFu"
},
"method": "chacha20-ietf-poly1305",
"mode": "tcp_and_udp",
"fast_open": false
}
CONFIG_EOF

# 下载 shadowsocks-manager
wget -O /etc/init.d/shadowsocks-manager https://raw.githubusercontent.com/teddysun/shadowsocks_install/master/shadowsocks-manager
chmod 755 /etc/init.d/shadowsocks-manager

# 创建配置目录并复制配置
mkdir -p /etc/shadowsocks-manager
cp /etc/shadowsocks-libev/config.json /etc/shadowsocks-manager/

# 启动 shadowsocks-manager
/etc/init.d/shadowsocks-manager start

# 设置开机自启
update-rc.d shadowsocks-manager defaults

# 检查服务状态（最多重试3次）
for i in 1 2 3; do
    service_status=$(/etc/init.d/shadowsocks-manager status)
    if [[ $service_status == *"is running..."* ]]; then
        echo "Shadowsocks-manager 正在运行。"
        break
    elif [[ $service_status == *"is stopped"* ]]; then
        if [ $i -eq 3 ]; then
            echo "尝试启动 shadowsocks-manager 3次失败。"
            exit 1
        fi
        echo "尝试重新启动 shadowsocks-manager，尝试次数：$i。"
        /etc/init.d/shadowsocks-manager start
    fi
done

# 下载 tcpx.sh 加速脚本（仅下载，不执行）
cd /root
wget -N --no-check-certificate https://github.000060000.xyz/tcpx.sh
chmod +x tcpx.sh

echo "=== Shadowsocks 安装完成 ==="
SCRIPT_EOF
```

### 第四步：部署 BBR+CAKE 加速

tcpx.sh 是一个交互式脚本，有菜单 UI。需要分两步执行：

**步骤 4a：选择 BBR+CAKE 加速（选项 13）**

```bash
$SSH_CMD "echo '13' | sudo bash /root/tcpx.sh"
```

**步骤 4b：系统配置优化（选项 21）**

选项 21 执行后会自动触发重启。

```bash
$SSH_CMD "echo '21' | sudo bash /root/tcpx.sh"
```

> **执行顺序说明：** 必须先 13 再 21。
> - 选项 13 将 `net.core.default_qdisc=cake` 和 `net.ipv4.tcp_congestion_control=bbr` 追加写入 `/etc/sysctl.d/99-sysctl.conf`
> - 选项 21 将系统优化参数追加写入 `/etc/sysctl.conf`（不同文件），不会覆盖 CAKE 设置
> - 如果改用选项 22（新版优化），它会用 `cat >` 覆盖整个 `/etc/sysctl.d/99-sysctl.conf`，会把 CAKE 重置为 FQ。若要用 22，需要先 22 再 13

> **注意：** 如果管道方式 `echo '13' | bash` 无法正确交互，告知用户需要手动 SSH 登录执行：
> ```bash
> ssh -p {port} {user}@{host}
> sudo su
> bash tcpx.sh
> # 依次选择 13（BBR+CAKE加速）和 21（系统配置优化旧）
> ```

### 第五步：等待重启并验证

选项 21 会触发 VPS 重启。等待约 60-90 秒后重新连接验证。

**重要：** 重启后 SSH host key 可能变化，需要先清除本地已知主机密钥缓存：

```bash
ssh-keygen -R {host} 2>/dev/null
```

如果 SSH 端口不是 22，还需要清除带端口的记录：

```bash
ssh-keygen -R "[{host}]:{port}" 2>/dev/null
```

然后验证服务状态：

```bash
$SSH_CMD "\
  echo '=== 系统信息 ===' && uname -r && \
  echo '=== BBR 状态 ===' && sysctl net.ipv4.tcp_congestion_control && sysctl net.core.default_qdisc && \
  echo '=== Shadowsocks 状态 ===' && sudo /etc/init.d/shadowsocks-manager status && \
  echo '=== 外部 IP ===' && curl -s ifconfig.me"
```

如果 shadowsocks-manager 未自动启动（异常情况），手动启动：

```bash
$SSH_CMD "sudo /etc/init.d/shadowsocks-manager start && sudo /etc/init.d/shadowsocks-manager status"
```

### 第六步：汇报部署结果

完成部署后，向用户汇报以下信息：

1. **VPS IP 地址**
2. **Shadowsocks 连接信息：**
   - 服务器地址：`{host}`
   - 加密方式：`chacha20-ietf-poly1305`
   - 端口与密码：参见配置中的 `port_password`
   - 模式：`tcp_and_udp`
3. **加速状态：** 拥塞控制算法和队列算法
4. **Shadowsocks-manager 服务状态**

## Shadowsocks 服务管理命令

SSH 登录 VPS 后（`sudo su` 切换 root），可使用以下命令管理服务：

```bash
# 启动
/etc/init.d/shadowsocks-manager start
# 停止
/etc/init.d/shadowsocks-manager stop
# 重启
/etc/init.d/shadowsocks-manager restart
# 查看状态
/etc/init.d/shadowsocks-manager status
```

## 注意事项

- VPS 需为 Ubuntu/Debian 系统（脚本使用 apt 包管理器）
- 需要 root 权限或具有 sudo 权限的用户
- VPS 防火墙需放行端口 7000-7020（Shadowsocks 使用的端口范围）
- 如果 VPS 提供商有安全组/防火墙规则，也需要在控制面板中放行对应端口
- shadowsocks-manager 已设置开机自启（`update-rc.d defaults`）
- 选项 21 执行后会触发重启，重启后需等待 60-90 秒再 SSH 连接
- 重启后可能需要 `ssh-keygen -R` 清除旧的 SSH host key 缓存

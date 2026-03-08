---
name: vps-ss-setup
description: 使用 GCloud 创建 VPS 并部署 Shadowsocks 翻墙服务及 BBR+CAKE 加速。当用户提到"搭建翻墙服务"、"创建VPS"、"部署SS"、"部署shadowsocks"、"搭建代理服务器"时触发。
allowed-tools: Bash(gcloud*), Bash(ssh*), Bash(scp*), Bash(cat*), Bash(echo*), Bash(printf*), Bash(mkdir*), Bash(ssh-keygen*), Bash(sleep*), AskUserQuestion
---

# VPS Shadowsocks 部署 Skill

## 概述

该 Skill 用于一键部署翻墙服务，流程包括：
1. 使用 `gcloud` 在 GCP 上创建 VPS 实例
2. SSH 登录到 VPS
3. 安装 Shadowsocks-libev 服务并设置开机自启
4. 部署 BBR+CAKE 网络加速 + 系统优化

## 工作流程

### 第一步：确认参数

使用 AskUserQuestion 向用户确认以下参数（提供默认值供参考）：

| 参数 | 说明 | 默认值示例 |
|------|------|-----------|
| `name` | VPS 实例名称 | `us-papa` |
| `region` | GCP 区域 | `us-west1` |
| `zone` | GCP 可用区 | `us-west1-c` |

选择 region/zone 时采用两轮选择：

**第一轮：选择大洲**（AskUserQuestion，3 个选项）：
1. US（美国）
2. Asia（亚洲）
3. Europe（欧洲）

**第二轮：根据大洲展示具体 region/zone**（AskUserQuestion），从以下完整列表中选取：

US 区域：
| Region | 位置 | 可用区 |
|--------|------|--------|
| `us-west1` | 俄勒冈 | a, b, c |
| `us-west2` | 洛杉矶 | a, b, c |
| `us-west3` | 盐湖城 | a, b, c |
| `us-west4` | 拉斯维加斯 | a, b, c |
| `us-central1` | 爱荷华 | a, b, c, f |
| `us-east1` | 南卡罗来纳 | b, c, d |
| `us-east4` | 弗吉尼亚 | a, b, c |
| `us-east5` | 哥伦布 | a, b, c |
| `us-south1` | 达拉斯 | a, b, c |

Asia 区域：
| Region | 位置 | 可用区 |
|--------|------|--------|
| `asia-east1` | 台湾彰化 | a, b, c |
| `asia-east2` | 香港 | a, b, c |
| `asia-northeast1` | 东京 | a, b, c |
| `asia-northeast2` | 大阪 | a, b, c |
| `asia-northeast3` | 首尔 | a, b, c |
| `asia-south1` | 孟买 | a, b, c |
| `asia-south2` | 德里 | a, b, c |
| `asia-southeast1` | 新加坡 | a, b, c |
| `asia-southeast2` | 雅加达 | a, b, c |
| `asia-southeast3` | 曼谷 | a, b, c |

Europe 区域：
| Region | 位置 | 可用区 |
|--------|------|--------|
| `europe-west1` | 比利时 | b, c, d |
| `europe-west2` | 伦敦 | a, b, c |
| `europe-west3` | 法兰克福 | a, b, c |
| `europe-west4` | 荷兰 | a, b, c |
| `europe-west6` | 苏黎世 | a, b, c |
| `europe-west8` | 米兰 | a, b, c |
| `europe-west9` | 巴黎 | a, b, c |
| `europe-west10` | 柏林 | a, b, c |
| `europe-west12` | 都灵 | a, b, c |
| `europe-southwest1` | 马德里 | a, b, c |
| `europe-north1` | 芬兰 | a, b, c |
| `europe-north2` | 斯德哥尔摩 | a, b, c |
| `europe-central2` | 华沙 | a, b, c |

用户也可以选"Other"自行输入以上未列出的区域。

### 第二步：创建 GCP VPS 实例

使用以下 gcloud 命令创建实例（将 `{name}`、`{region}`、`{zone}` 替换为用户确认的参数）：

```bash
gcloud compute instances create {name} \
  --project=gen-lang-client-0128537500 \
  --zone={zone} \
  --machine-type=e2-small \
  --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
  --metadata=enable-osconfig=TRUE \
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --no-service-account \
  --no-scopes \
  --tags=http-server,https-server \
  --create-disk=auto-delete=yes,boot=yes,device-name={name},disk-resource-policy=projects/gen-lang-client-0128537500/regions/{region}/resourcePolicies/default-schedule-1,image=projects/ubuntu-os-cloud/global/images/ubuntu-2404-noble-amd64-v20260128,mode=rw,size=40,type=pd-balanced \
  --no-shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --labels=goog-ops-agent-policy=v2-x86-template-1-4-0,goog-ec-src=vm_add-gcloud \
  --reservation-affinity=any
```

创建实例后，配置 ops-agent 策略（如果已存在则忽略错误）：

```bash
printf 'agentsRule:\n  packageState: installed\n  version: latest\ninstanceFilter:\n  inclusionLabels:\n  - labels:\n      goog-ops-agent-policy: v2-x86-template-1-4-0\n' > /tmp/ops-agent-config.yaml

gcloud compute instances ops-agents policies create \
  goog-ops-agent-v2-x86-template-1-4-0-{zone} \
  --project=gen-lang-client-0128537500 \
  --zone={zone} \
  --file=/tmp/ops-agent-config.yaml
```

### 第三步：等待实例就绪并获取 IP

创建完成后，等待约 30 秒让实例启动，然后获取外部 IP：

```bash
gcloud compute instances describe {name} \
  --zone={zone} \
  --project=gen-lang-client-0128537500 \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

记录下这个 IP 地址，后续需要告知用户。

### 第四步：SSH 登录并部署 Shadowsocks

通过 gcloud SSH 登录并以 root 身份执行部署脚本。注意脚本末尾包含设置开机自启的命令：

```bash
gcloud compute ssh {name} --zone={zone} --project=gen-lang-client-0128537500 --command="sudo bash -s" << 'SCRIPT_EOF'
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
"9000": "colacolacola",
"9001": "Zqx465gr5snpp",
"9002": "DSxKZggSUaH4Mj",
"9003": "4y5tA47Y1Iu8lo",
"9004": "hE7sAa64",
"9005": "PSjra7lgue+yyO4",
"9006": "i34qDaVCE5aiiDt4",
"9007": "wr4cEtvngfNtA",
"9008": "Dcd98rwpgbOUJuk8qd4A",
"9009": "0DPyZ0m6cdbV7X2OEgc1N",
"9010": "xo1FKrhVo8C9A27QWg",
"9011": "MyUGGGFuZWLjQ2atS9",
"9012": "cdbV7X2OEgc1N",
"9013": "FTiLUTyfZEwNtl",
"9020": "xinzhu",
"9021": "tudou2",
"9022": "yichen2",
"9023": "chacha20"
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

# 创建 user.json
cat > /etc/shadowsocks-manager/user.json << 'USER_EOF'
{
"9000": "home",
"9001": "vic",
"9002": "",
"9003": "",
"9004": "",
"9005": "",
"9006": "",
"9007": "",
"9008_9010": "vit",
"9011": "",
"9012": "",
"9013": "",
"9020": "xinzhu",
"9021": "tudou2",
"9022": "yichen2",
"9023": "huixin"
}
USER_EOF

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

### 第五步：部署 BBR+CAKE 加速

tcpx.sh 是一个交互式脚本，有菜单 UI。需要分两步执行：

**步骤 5a：选择 BBR+CAKE 加速（选项 13）**

```bash
gcloud compute ssh {name} --zone={zone} --project=gen-lang-client-0128537500 --command="echo '13' | sudo bash /root/tcpx.sh"
```

**步骤 5b：系统配置优化（选项 21）**

选项 21 执行后会自动触发重启。

```bash
gcloud compute ssh {name} --zone={zone} --project=gen-lang-client-0128537500 --command="echo '21' | sudo bash /root/tcpx.sh"
```

> **执行顺序说明：** 必须先 13 再 21。
> - 选项 13 将 `net.core.default_qdisc=cake` 和 `net.ipv4.tcp_congestion_control=bbr` 追加写入 `/etc/sysctl.d/99-sysctl.conf`
> - 选项 21 将系统优化参数追加写入 `/etc/sysctl.conf`（不同文件），不会覆盖 CAKE 设置
> - 如果改用选项 22（新版优化），它会用 `cat >` 覆盖整个 `/etc/sysctl.d/99-sysctl.conf`，会把 CAKE 重置为 FQ。若要用 22，需要先 22 再 13

> **注意：** 如果管道方式 `echo '13' | bash` 无法正确交互，告知用户需要手动 SSH 登录执行：
> ```bash
> gcloud compute ssh {name} --zone={zone} --project=gen-lang-client-0128537500
> sudo su
> bash tcpx.sh
> # 依次选择 13（BBR+CAKE加速）和 21（系统配置优化旧）
> ```

### 第六步：等待重启并验证

选项 21 会触发 VPS 重启。等待约 60-90 秒后重新连接验证。

**重要：** 重启后 SSH host key 可能变化，需要先清除本地已知主机密钥缓存：

```bash
ssh-keygen -R {外部IP} 2>/dev/null
```

然后验证服务状态：

```bash
gcloud compute ssh {name} --zone={zone} --project=gen-lang-client-0128537500 --command="\
  echo '=== 系统信息 ===' && uname -r && \
  echo '=== BBR 状态 ===' && sysctl net.ipv4.tcp_congestion_control && sysctl net.core.default_qdisc && \
  echo '=== Shadowsocks 状态 ===' && sudo /etc/init.d/shadowsocks-manager status && \
  echo '=== 外部 IP ===' && curl -s ifconfig.me"
```

如果 shadowsocks-manager 未自动启动（异常情况），手动启动：

```bash
gcloud compute ssh {name} --zone={zone} --project=gen-lang-client-0128537500 --command="sudo /etc/init.d/shadowsocks-manager start && sudo /etc/init.d/shadowsocks-manager status"
```

### 第七步：汇报部署结果

完成部署后，向用户汇报以下信息：

1. **VPS 外部 IP 地址**
2. **Shadowsocks 连接信息：**
   - 服务器地址：`{外部IP}`
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

## 删除 VPS 实例

删除 GCP 实例速度较慢，**必须使用 background task 执行**：

```bash
# 使用 Bash 工具时设置 run_in_background=true
gcloud compute instances delete {name} --zone={zone} --project=gen-lang-client-0128537500 --quiet
```

## 注意事项

- `gcloud` CLI 需要已在本地认证并安装
- 项目 ID 固定为 `gen-lang-client-0128537500`
- 磁盘镜像使用 Ubuntu 24.04 LTS
- 机器类型固定为 `e2-small`
- shadowsocks-manager 已设置开机自启（`update-rc.d defaults`）
- 选项 21 执行后会触发重启，重启后需等待 60-90 秒再 SSH 连接
- 重启后可能需要 `ssh-keygen -R` 清除旧的 SSH host key 缓存
- 删除 GCP VPS 实例时必须使用 background task，因为操作耗时较长

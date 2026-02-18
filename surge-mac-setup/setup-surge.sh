#!/bin/bash
# ============================================================
#  Surge Mac 企业版一键安装脚本
#  用法：bash setup-surge.sh
# ============================================================
set -euo pipefail

# --- 颜色 ---
R='\033[0;31m'   G='\033[0;32m'   Y='\033[1;33m'
B='\033[0;34m'   C='\033[0;36m'   BOLD='\033[1m'
DIM='\033[2m'    NC='\033[0m'

# --- 工具函数 ---
info()  { printf "${B}▸${NC} %s\n" "$*"; }
ok()    { printf "${G}✓${NC} %s\n" "$*"; }
warn()  { printf "${Y}!${NC} %s\n" "$*"; }
fail()  { printf "${R}✗${NC} %s\n" "$*"; exit 1; }
step()  { printf "\n${BOLD}${C}[$1/6]${NC} ${BOLD}%s${NC}\n" "$2"; }
ask()   { printf "${Y}▸${NC} %s" "$1"; read -r "$2" </dev/tty; }
pause() { printf "${DIM}  按回车继续...${NC}"; read -r </dev/tty; }

SURGE_APP="/Applications/Surge.app"
SURGE_CLI="$SURGE_APP/Contents/Applications/surge-cli"
DOWNLOAD_URL="https://dl.nssurge.com/mac/v4/Surge-latest.zip"
TMP_ZIP="/tmp/Surge-latest.zip"

# ============================================================
printf "\n${BOLD}${C}╔══════════════════════════════════════╗${NC}\n"
printf "${BOLD}${C}║   Surge Mac 企业版 · 一键安装脚本   ║${NC}\n"
printf "${BOLD}${C}╚══════════════════════════════════════╝${NC}\n\n"

# ============================================================
step 1 "收集信息"
# ============================================================

ask "请输入你的姓名拼音（如不确定可以登录 https://auth.midway.run/ 查看）: " SURGE_USER

if [ -z "$SURGE_USER" ]; then
  fail "用户名不能为空"
fi

ok "用户名: $SURGE_USER"

# ============================================================
step 2 "检查 Surge 安装状态"
# ============================================================

if [ -d "$SURGE_APP" ]; then
  ok "Surge 已安装在 $SURGE_APP"
else
  info "未检测到 Surge，开始下载安装..."
  info "下载地址: $DOWNLOAD_URL"

  curl -fSL --progress-bar -o "$TMP_ZIP" "$DOWNLOAD_URL" \
    || fail "下载失败，请检查网络连接"

  info "解压到 /Applications ..."
  unzip -o -q "$TMP_ZIP" -d /Applications/ \
    || fail "解压失败"

  rm -f "$TMP_ZIP"

  if [ -d "$SURGE_APP" ]; then
    ok "Surge 安装成功"
  else
    fail "安装后未找到 Surge.app，请检查 zip 包内容"
  fi
fi

# ============================================================
step 3 "启动 Surge"
# ============================================================

if pgrep -x "Surge" >/dev/null 2>&1; then
  ok "Surge 已在运行"
else
  info "正在启动 Surge ..."
  open -a Surge
  sleep 2
  ok "Surge 已启动"
fi

# ============================================================
step 4 "企业授权激活（需手动操作）"
# ============================================================

printf "\n"
printf "  ${BOLD}请在 Surge 窗口中完成以下操作：${NC}\n"
printf "\n"
printf "  ${DIM}┌─────────────────────────────────────────┐${NC}\n"
printf "  ${DIM}│${NC}  1. 点击「已经拥有授权？现在激活」        ${DIM}│${NC}\n"
printf "  ${DIM}│${NC}  2. 点击左下角「企业授权」                ${DIM}│${NC}\n"
printf "  ${DIM}│${NC}  3. 填入以下信息，点击激活：              ${DIM}│${NC}\n"
printf "  ${DIM}│${NC}                                           ${DIM}│${NC}\n"
printf "  ${DIM}│${NC}     公司 ID :  ${G}${BOLD}jike${NC}                      ${DIM}│${NC}\n"
printf "  ${DIM}│${NC}     用户名  :  ${G}${BOLD}%-24s${NC}  ${DIM}│${NC}\n" "$SURGE_USER"
printf "  ${DIM}│${NC}     密码    :  ${G}${BOLD}jikesurge52202${NC}             ${DIM}│${NC}\n"
printf "  ${DIM}│${NC}                                           ${DIM}│${NC}\n"
printf "  ${DIM}└─────────────────────────────────────────┘${NC}\n"
printf "\n"

pause

# ============================================================
step 5 "验证配置"
# ============================================================

ERRORS=0

# 检查 Surge 是否在运行
if pgrep -x "Surge" >/dev/null 2>&1; then
  ok "Surge 正在运行"
else
  warn "Surge 未在运行，请手动启动后重新运行脚本"
  ERRORS=$((ERRORS + 1))
fi

# 用 surge-cli 检查配置
if [ -x "$SURGE_CLI" ]; then
  PROFILE_OUT=$("$SURGE_CLI" dump profile effective 2>/dev/null | head -5 || true)
  if [ -n "$PROFILE_OUT" ]; then
    ok "配置文件已加载"
  else
    warn "无法读取配置文件（可能尚未激活）"
    ERRORS=$((ERRORS + 1))
  fi

  POLICY_OUT=$("$SURGE_CLI" dump policy 2>/dev/null || true)
  if echo "$POLICY_OUT" | grep -qi "proxy\|direct\|reject" 2>/dev/null; then
    ok "代理策略已就绪"
  else
    warn "未检测到代理策略"
    ERRORS=$((ERRORS + 1))
  fi
else
  warn "surge-cli 不可用，跳过详细检查"
fi

# ============================================================
step 6 "测试连接"
# ============================================================

printf "\n"
info "正在测试 Google 连通性..."

HTTP_CODE=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" https://www.google.com 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
  ok "Google 连通性测试通过 (HTTP $HTTP_CODE)"
else
  warn "Google 连通性测试失败 (HTTP $HTTP_CODE)"
  ERRORS=$((ERRORS + 1))
  printf "\n"
  printf "  ${Y}排查建议：${NC}\n"
  printf "  1. 右击状态栏 Surge 图标，确认「设置为系统代理」已勾选\n"
  printf "  2. 确认出站模式为「规则判定」\n"
  printf "  3. 点击「切换配置」→ 确认选中 Enterprise Profile\n"
  printf "  4. 点击「切换配置」→「检查企业配置更新」\n"
  printf "  5. 使用 Surge 测速功能，选择可用的代理节点\n"
fi

# ============================================================
# 结果汇总
# ============================================================
printf "\n"
if [ "$ERRORS" -eq 0 ]; then
  printf "${G}${BOLD}══════════════════════════════════════${NC}\n"
  printf "${G}${BOLD}  ✓ Surge 安装配置完成，翻墙已就绪！${NC}\n"
  printf "${G}${BOLD}══════════════════════════════════════${NC}\n"
else
  printf "${Y}${BOLD}══════════════════════════════════════${NC}\n"
  printf "${Y}${BOLD}  ! 安装完成，但有 $ERRORS 项检查未通过${NC}\n"
  printf "${Y}${BOLD}══════════════════════════════════════${NC}\n"
  printf "\n"
  printf "  如需帮助，请参考以下资源：\n"
  printf "  • 账号注册：${C}https://auth.midway.run/${NC}\n"
  printf "  • 设备清理：${C}https://auth.midway.run/${NC}（最多激活 3 台设备）\n"
fi

printf "\n"

"""全局配置：环境差异只允许改这里，不许改测试代码。

为什么需要 config/：
同一套代码未来要跑两套环境（Demo 线上站 / 本地 Docker 部署），
URL、账号、超时等差异全部收敛到本文件，切换环境靠环境变量，不靠改代码。
"""
import os

# 被测系统地址（默认 Demo 站；M6 本地部署后通过环境变量切换）
BASE_URL = os.getenv("ORANGEHRM_BASE_URL", "https://opensource-demo.orangehrmlive.com")

# Demo 公共凭证（登录页公开展示，非敏感）。
# 生产环境凭证绝不允许硬编码，必须走环境变量。
USERNAME = os.getenv("ORANGEHRM_USERNAME", "Admin")
PASSWORD = os.getenv("ORANGEHRM_PASSWORD", "admin123")

# 全局默认等待秒数。M0 实测 SPA 提交后 1~3 秒重渲染瞬态。
# 2026-09-15 晚高峰实测：Demo 站过载时 goto 连 domcontentloaded 都 >10s，
# 10s 预算不足 → 提到 20s（环境参数按实测校准，非放宽断言标准）。
DEFAULT_TIMEOUT = int(os.getenv("ORANGEHRM_TIMEOUT", "20"))
# 隐含预算（独立复审二轮 P1-2/P2-1）：goto 失败单次重试（pages/base.py）会把单个
# open() 的最坏等待抬到 2×DEFAULT_TIMEOUT（=40s）。这是"吸收环境噪声"的有意代价，
# 重试有模块级计数 + 会话结束输出（conftest pytest_terminal_summary）保证可观测；
# 改 DEFAULT_TIMEOUT 时连带影响该上界。

# 断言层预算（毫秒）——expect() 的 timeout 统一取值处（全面复审 P1-2 修复）。
# 为什么单独存在：Playwright expect 默认 5s 且**不受** set_default_timeout 影响
# （M5 全量实锤、M6 Review 在 Demo 过载时段再次实锤），操作层与断言层的
# 等待预算是两套体系。若各断言点手写 timeout=xx*1000，预算语义会随复制
# 漂移——收敛到这一处，调预算只改一个数字。
ASSERT_TIMEOUT_MS = DEFAULT_TIMEOUT * 1000
# 有头/无头：调试失败用例时 ORANGEHRM_HEADLESS=false 看着浏览器跑，不用改代码
# 解析约定（Review P3-3，M2 Review 已裁定不改代码）：仅接受字符串 "true"，
# 其他值（false/1/yes/0）一律视为 False——首次使用请严格用 true/false
HEADLESS = os.getenv("ORANGEHRM_HEADLESS", "true").lower() == "true"

# ---- M6：本地 Docker 环境的 MySQL 直连配置（DB 校验层专用）----
# 与 docker/docker-compose.yml 保持一致：宿主机经 13306 端口映射访问容器 MySQL。
# 只有本地部署才有库可查——公网 Demo 环境无 DB 权限，DB 用例按环境能力 skip。
# 账号选择：专用只读账号 ohrm_ro（仅 SELECT，M6 Review P2-2 修复）而非应用账号
# ohrm 或 root——校验层只需要「能读」，最小权限在 DB 侧强制而非客户端自律
# （实测：ohrm_ro SELECT 通过、INSERT 被拒）。凭证本地测试环境专用（非生产敏感）。
# 重建环境后需重新创建该账号（一条 GRANT，见 README 本地环境节）。
DB_HOST = os.getenv("ORANGEHRM_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("ORANGEHRM_DB_PORT", "13306"))
DB_USER = os.getenv("ORANGEHRM_DB_USER", "ohrm_ro")
DB_PASSWORD = os.getenv("ORANGEHRM_DB_PASSWORD", "ohrm_ro_password_local")
DB_NAME = os.getenv("ORANGEHRM_DB_NAME", "orangehrm")

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

# 全局默认等待秒数。M0 实测发现 SPA 提交后有 1~3 秒重渲染瞬态，
# Playwright 的自动等待会基于此超时反复探测元素出现，禁止用固定 sleep。
DEFAULT_TIMEOUT = int(os.getenv("ORANGEHRM_TIMEOUT", "10"))

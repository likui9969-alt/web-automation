"""api/client.py — OrangeHRM 内部 API 会话客户端（M4 激活 api/ 层）。

为什么需要"客户端"而不是每条测试裸写 requests：
登录流程（拿 CSRF token → 表单 POST → 会话 Cookie）是所有接口测试的公共
前置，散在各测试里 = 重复 + 改一处要动 N 处（和 POM 同一个道理，只是层次
从页面换成了接口）。

本文件封装的全部行为均经实测验证（2026-09-15，六轮探测）：
1. 登录页 HTML 壳里 <auth-login :token="..."> 携带 Symfony CSRF token
   （HTML 实体编码，需 unescape）——不是表单隐藏字段，正则找错字段名
   会得到 302 回登录页的"静默失败"
2. POST /web/index.php/auth/validate 表单提交（_token/username/password）
3. 内部 API 路径带 /web/index.php 前缀（浏览器抓包容易漏记这一段，
   漏了就是 Apache 层 404）
4. 会话靠 orangehrm Cookie 维持（M0 已实测 HttpOnly）
"""
import html
import os
import re

import requests

from config import settings
from utils.failure_artifacts import record_api_log

_TOKEN_RE = re.compile(r'<auth-login[^>]*:token="([^"]+)"')


class OrangeHRMClient:
    """带会话的 API 客户端。login() 之前是匿名会话（预期 401 行为可测）。"""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.BASE_URL
        self.session = requests.Session()
        self.session.headers["Accept"] = "application/json"
        # 代理策略（M11 全局收口审查 P1-3）：requests 默认 trust_env=True 会遵循
        # HTTP_PROXY/HTTPS_PROXY 环境变量——开发机代理未启动时，同一份代码会从
        # "16 passed" 变成 "5 failed + 11 ProxyError"（审查方 2026-09-16 亲身踩到），
        # 且失败被误记为"公网瞬态"。默认关掉（直连，行为与 CI/容器一致），
        # 需要显式走代理时用 ORANGEHRM_TRUST_ENV=true 打开。
        if not os.getenv("ORANGEHRM_TRUST_ENV", "false").lower() == "true":
            self.session.trust_env = False
        # M7 留痕：每个响应进入全局 API 请求日志（纯记录，不拦截、不改行为）
        self.session.hooks["response"].append(self._log_response)

    @staticmethod
    def _log_response(resp, *args, **kwargs):
        record_api_log(
            resp.request.method,
            resp.request.url,
            resp.status_code,
            int(resp.elapsed.total_seconds() * 1000),
        )

    def login(self, username: str, password: str) -> bool:
        """完整登录流程：提取 token → 表单 POST → 返回是否成功。

        返回 bool 而非抛异常：登录失败本身就是可测场景（错误凭证应失败）。
        """
        page = self.session.get(
            f"{self.base_url}/web/index.php/auth/login",
            timeout=settings.DEFAULT_TIMEOUT,
        )
        m = _TOKEN_RE.search(page.text)
        if not m:  # 页面结构变了，第一时间暴露而不是静默失败
            raise RuntimeError("登录页未找到 <auth-login :token>，页面结构可能已变更")
        token = html.unescape(m.group(1))

        resp = self.session.post(
            f"{self.base_url}/web/index.php/auth/validate",
            data={"_token": token, "username": username, "password": password},
            timeout=settings.DEFAULT_TIMEOUT,
            allow_redirects=False,
        )
        # 实测：成功 302 → /dashboard/index；失败 302 → 回 /auth/login
        return "/dashboard/index" in (resp.headers.get("location") or "")

"""conftest.py — pytest 全局共享 fixture（M2 激活，M1 占位期的承诺兑现）。

M1 裸版（git 历史 c93f61e 可对照）每用例自建浏览器的代价：
3 用例 35.29s，其中 ~6s 是重复的浏览器启停。本文件把启停逻辑收编到一处。

三层 fixture 设计（为什么拆三层而不是一个大 fixture）：
    playwright (session) → browser (session) → page (function)
1. playwright/session：驱动进程整个会话只起一次（最重的资源）
2. browser/session：浏览器进程共享——启动 ~2s 是纯开销，用例之间无差别
3. page/function：每个用例独立 context+page——**隔离的关键**。
   Cookie/localStorage 全挂在 context 上，用例 A 的登录失败状态
   不能泄给用例 B。浏览器共享省钱，页面隔离保命，两者不矛盾。

yield 语义：之前的代码 = setup，之后的 = teardown。
断言失败也会执行 teardown（对比 M1：断言挂了 browser.close() 永远走不到）。
"""
import os
from pathlib import Path

# 必须在任何 Playwright 浏览器启动前执行（M4 全量运行实测咬人：
# 新开终端忘设 PLAYWRIGHT_BROWSERS_PATH → UI 全部 error）。
# setdefault：外部已显式设置（CI 自定义路径）时不覆盖。
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path(__file__).parent / ".playwright-browsers"))

import pytest
from playwright.sync_api import sync_playwright

from config import settings
from pages.login_page import LoginPage


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright):
    browser = playwright.chromium.launch(headless=settings.HEADLESS)
    yield browser
    browser.close()


@pytest.fixture  # 默认 function：每个用例一个干净页面
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(settings.DEFAULT_TIMEOUT * 1000)
    yield page
    context.close()


@pytest.fixture
def login_page(page) -> LoginPage:
    """打开登录页并返回 Page Object——用例从此不知 URL、不知定位器。"""
    return LoginPage(page).open()


# ---- M5：共享会话（API 造数 + UI 免登录）----

@pytest.fixture(scope="session")
def api_client():
    """session 级 API 会话：整个运行登录一次，供 e2e 造数/断言/清理复用。

    与 tests/api/ 的 function 级 pim fixture 有意共存：
    API 层验证登录边界（每用例独立会话，隔离优先），
    e2e 层追求速度（共享会话，登录 ~2s 只付一次）。
    """
    from api.client import OrangeHRMClient

    client = OrangeHRMClient()
    assert client.login(settings.USERNAME, settings.PASSWORD), "session 级 API 登录失败"
    return client


@pytest.fixture(scope="session")
def ui_auth_state(api_client):
    """API 会话 cookie → Playwright storage_state（M4 Review P3-1 的会话复用）。

    为什么 API 登录而不是 UI 登录造 state：
    快（秒级）且不依赖 SPA 渲染——M3 教训：公网过载时 UI 登录的
    goto 可能随机超时，登录态构造不该被页面渲染波动劫持。
    M5 探测实测：注入 orangehrm HttpOnly cookie 后直达 PIM 列表，不跳登录页。
    """
    return {
        "cookies": [
            {
                "name": ck.name,
                "value": ck.value,
                "domain": ck.domain.lstrip("."),
                "path": ck.path or "/",
                "expires": ck.expires if ck.expires else -1,  # -1 = 会话 cookie
                "httpOnly": True,  # M0 实测：orangehrm cookie 为 HttpOnly
                "secure": False,
                "sameSite": "Lax",
            }
            for ck in api_client.session.cookies
        ],
        "origins": [],
    }


@pytest.fixture  # function：每用例独立 context，仅共享登录态 cookie
def ui_auth_page(browser, ui_auth_state):
    """免登录 page：独立 context + 共享登录态。

    与 page fixture 的区别：page 匿名（登录测试专用，登录本身是被测对象时
    绝不能用本 fixture——那等于把被测前提变成了注入的假状态）。
    """
    context = browser.new_context(storage_state=ui_auth_state)
    page = context.new_page()
    page.set_default_timeout(settings.DEFAULT_TIMEOUT * 1000)
    yield page
    context.close()

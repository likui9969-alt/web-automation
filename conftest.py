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

"""M1 裸登录测试 —— 故意不用 fixture、不用 POM。

为什么故意写得"难看"：
1. 每个测试自建浏览器实例 → 重复代码，跑 3 个用例启动 3 次浏览器（先痛后治）
2. 定位器直接散落在测试里 → 前端一改版，每个用例都要改（M3 POM 的重构动机）
3. M2/M3 重构前，这就是"没有工程化"的真实样子，留着对比

测试点来源：homework/M0_登录模块作业.md（全部实测过）
- LOGIN-01 正确凭证 → dashboard
- LOGIN-02 错误密码 → Invalid credentials
- LOGIN-03 空表单 → 两处 Required
"""
import re

import pytest
from playwright.sync_api import expect, sync_playwright

from config import settings

pytestmark = pytest.mark.ui  # 分层 marker：CI 里 pytest -m ui 只跑 UI 层


def test_login_valid_credentials():
    # LOGIN-01：正确账号密码 → 跳转 dashboard
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(settings.DEFAULT_TIMEOUT * 1000)
        page.goto(f"{settings.BASE_URL}/web/index.php/auth/login")

        # M0 实测：输入框只有 placeholder 可语义定位（无 label 绑定）
        page.get_by_placeholder("Username").fill(settings.USERNAME)
        page.get_by_placeholder("Password").fill(settings.PASSWORD)
        page.get_by_role("button", name="Login").click()

        # M0 实测：SPA 提交后有 1~3 秒重渲染瞬态，
        # expect 自带轮询重试，等 URL 而不是 sleep —— 这是等待策略的第一课
        expect(page).to_have_url(re.compile(r"/dashboard/index"))
        browser.close()


def test_login_wrong_password():
    # LOGIN-02：错误密码 → 停留登录页 + 提示 Invalid credentials（实测原文）
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(settings.DEFAULT_TIMEOUT * 1000)
        page.goto(f"{settings.BASE_URL}/web/index.php/auth/login")

        page.get_by_placeholder("Username").fill(settings.USERNAME)
        page.get_by_placeholder("Password").fill("wrongpass123")
        page.get_by_role("button", name="Login").click()

        # M0 实测：错误提示原文 "Invalid credentials"（防用户枚举，统一文案）
        expect(page.get_by_text("Invalid credentials")).to_be_visible()
        assert "/auth/login" in page.url  # 未跳转
        browser.close()


def test_login_empty_fields():
    # LOGIN-03：空表单提交 → 两个字段各自显示 Required（前端校验拦截）
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(settings.DEFAULT_TIMEOUT * 1000)
        page.goto(f"{settings.BASE_URL}/web/index.php/auth/login")

        # 故意不填任何值，直接提交
        page.get_by_role("button", name="Login").click()

        required = page.get_by_text("Required")
        expect(required).to_have_count(2)
        assert "/auth/login" in page.url
        browser.close()

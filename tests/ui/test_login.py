"""M2 登录测试 —— fixture + 参数化版。

对照 M1 裸版（git 历史：c93f61e 的 tests/ui/test_login_bare.py）：
1. 无 sync_playwright/launch/close 样板——conftest.py 三层 fixture 自动注入
2. goto 收进 login_page fixture——用例只写场景，不写导航
3. 错误凭证参数化——M0 实测错误用户名/密码统一提示 "Invalid credentials"
   （防枚举设计），3 组数据一条用例，代替 M1 的 1 组硬编码

测试点来源：homework/M0_登录模块作业.md（全部实测过）
- LOGIN-01 正确凭证 → dashboard
- LOGIN-02 错误凭证（参数化 ×3）→ Invalid credentials
- LOGIN-03 空表单 → 两处 Required
"""
import re

import pytest
from playwright.sync_api import expect

from config import settings

pytestmark = pytest.mark.ui  # 分层 marker：CI 里 pytest -m ui 只跑 UI 层


@pytest.fixture
def login_page(page):
    """每个用例都从登录页开始——导航是前置条件，不是被测行为。"""
    page.goto(f"{settings.BASE_URL}/web/index.php/auth/login")
    return page


def test_login_valid_credentials(login_page):
    # LOGIN-01：正确账号密码 → 跳转 dashboard
    login_page.get_by_placeholder("Username").fill(settings.USERNAME)
    login_page.get_by_placeholder("Password").fill(settings.PASSWORD)
    login_page.get_by_role("button", name="Login").click()

    # M0 实测：SPA 提交后有 1~3 秒重渲染瞬态，expect 自带轮询，不 sleep
    expect(login_page).to_have_url(re.compile(r"/dashboard/index"))


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("Admin", "wrongpass123"),      # 错误密码
        ("nosuchuser", "admin123"),     # 错误用户名
        ("nosuchuser", "wrongpass123"), # 双双错误
    ],
)
def test_login_invalid_credentials(login_page, username, password):
    # LOGIN-02：任何错误组合 → 统一提示（M0 实测：防用户枚举）
    login_page.get_by_placeholder("Username").fill(username)
    login_page.get_by_placeholder("Password").fill(password)
    login_page.get_by_role("button", name="Login").click()

    expect(login_page.get_by_text("Invalid credentials")).to_be_visible()
    assert "/auth/login" in login_page.url  # 未跳转


def test_login_empty_fields(login_page):
    # LOGIN-03：空表单提交 → 两个字段各自显示 Required（前端校验拦截）
    login_page.get_by_role("button", name="Login").click()

    required = login_page.get_by_text("Required")
    expect(required).to_have_count(2)
    assert "/auth/login" in login_page.url

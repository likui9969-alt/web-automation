"""M3 登录测试 —— POM 版：用例即业务文档。

对照 M2 版（git 4a99b8b）：定位器与 URL 从用例中消失。
现在读用例不需要懂 DOM：正确凭证→应登录成功；错误凭证→应报错且不跳转；
空表单→应被前端拦截。改前端定位器只动 pages/login_page.py 一处。

测试点来源：homework/M0_登录模块作业.md（全部实测过）
- LOGIN-01 正确凭证 → dashboard
- LOGIN-02 错误凭证（参数化 ×3）→ Invalid credentials
- LOGIN-03 空表单 → 两处 Required
"""
import pytest
from playwright.sync_api import expect

from config import settings
from data.credentials import INVALID_CREDENTIAL_CASES

pytestmark = pytest.mark.ui  # 分层 marker：CI 里 pytest -m ui 只跑 UI 层


def test_login_valid_credentials(login_page):
    # LOGIN-01：正确账号密码 → 登录成功
    login_page.login(settings.USERNAME, settings.PASSWORD)
    login_page.expect_logged_in()


@pytest.mark.parametrize(("username", "password"), INVALID_CREDENTIAL_CASES)
def test_login_invalid_credentials(login_page, username, password):
    # LOGIN-02：任何错误组合 → 统一报错且不跳转（M0 实测：防用户枚举）
    login_page.login(username, password)
    expect(login_page.error_message).to_be_visible()
    assert "/auth/login" in login_page.url


def test_login_empty_fields(login_page):
    # LOGIN-03：空表单提交 → 前端校验拦截，两个字段各自 Required
    login_page.submit_empty()
    expect(login_page.required_hints).to_have_count(2)
    assert "/auth/login" in login_page.url

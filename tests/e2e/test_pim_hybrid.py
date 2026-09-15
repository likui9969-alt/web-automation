"""tests/e2e — UI+API 混合闭环（M5 激活 e2e/ 层）。

混合用例的分层逻辑（测试金字塔顶层，量少但贵）：
- 造数/清理/存在性验证 → API（快、稳、精确）
- 真实用户关键路径 → UI（浏览器行为本身是被测物）
每条用例自造唯一数据 + teardown 清理：不依赖固定记录、不污染共享环境。
"""
import pytest
from playwright.sync_api import expect

from api.pim import PIMApi
from pages.pim_page import PimPage
from utils.factory import make_employee

pytestmark = pytest.mark.e2e


@pytest.fixture
def pim_api(api_client) -> PIMApi:
    """e2e 走 session 级共享 API 会话（vs tests/api/ 的 function 级独立登录：
    API 层验证登录边界，e2e 追求速度——两种 scope 有意共存，注释见 conftest）。"""
    return PIMApi(api_client)


@pytest.fixture
def api_created_employee(pim_api):
    """API 造数 + 结束清理（M5 核心模式：用例自带数据，用完即删）。"""
    payload = make_employee()
    resp = pim_api.create_employee(
        payload["firstName"], payload["lastName"], payload["middleName"])
    assert resp.ok, f"造数失败: {resp.status_code} {resp.text[:200]}"
    emp_number = resp.json()["data"]["empNumber"]
    yield {"payload": payload, "empNumber": emp_number}
    pim_api.delete_employee(emp_number)


def test_api_created_employee_visible_in_ui(api_created_employee, ui_auth_page):
    """E2E-01：API 造数 → UI 验证（工业界标准组合）。

    断言自己造的唯一名，不碰固定记录——共享环境数据再变也不影响。
    """
    name = api_created_employee["payload"]["lastName"]
    pim = PimPage(ui_auth_page).open()
    pim.search(name)
    # expect 自动轮询：搜索请求返回 + 行渲染完成即通过，无需手动等待
    expect(pim.result_rows.filter(has_text=name).first).to_be_visible()


def test_ui_created_employee_exists_via_api(ui_auth_page, pim_api):
    """E2E-02：UI 操作 → API 验证（UI 只做关键路径，落库交给 API 断言）。"""
    emp = make_employee()
    try:
        PimPage(ui_auth_page).open().add_employee(
            emp["firstName"], emp["lastName"], emp["middleName"])
        # API 权威断言：按唯一 lastName 精确匹配（模糊搜索结果里挑自己的）
        resp = pim_api.search_by_name(emp["lastName"])
        assert resp.ok, f"API 查询失败: {resp.status_code}"
        matched = [e for e in resp.json()["data"] if e["lastName"] == emp["lastName"]]
        assert matched, "UI 提交完成后，API 却搜不到该员工——落库失败"
    finally:
        # 失败安全清理（Review P2-1）：断言失败时员工已创建，同样要清。
        # 重新搜索（而非依赖 matched）：失败路径上 matched 可能未定义/为空。
        resp = pim_api.search_by_name(emp["lastName"])
        if resp.ok:
            for e in resp.json()["data"]:
                if e["lastName"] == emp["lastName"]:
                    pim_api.delete_employee(e["empNumber"])

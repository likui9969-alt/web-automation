"""M4 首批 API 测试 —— PIM 员工列表接口 + 会话鉴权。

对照 UI 层（test_login.py）：本文件没有浏览器、没有定位器、没有页面等待——
同环境实测下每条用例只需 1~3 个 HTTP 往返，这就是测试金字塔"API 层做主力"
的原因：快、稳、直接验证业务规则。

全部断言依据 2026-09-15 六轮探测实测（MODULE_FEEDBACK 验证记录），
无一条"理论上应该如此"。

测试点：
- API-01 正确凭证登录成功（302 → dashboard）
- API-02 错误凭证登录失败（302 回登录页，不建立会话）
- API-03 未登录调业务接口 → 401 "Session expired"（会话校验）
- API-04 登录后员工列表 → 200 + JSON 结构 + 关键字段
- API-05 limit 分页语义：返回条数受控、total 不受影响
"""
import pytest

from api.client import OrangeHRMClient
from api.pim import PIMApi
from config import settings

pytestmark = pytest.mark.api  # 分层 marker：CI 里 pytest -m api 先跑快的接口层


@pytest.fixture
def pim() -> PIMApi:
    """已登录的 PIM API（登录失败会让 fixture 直接报错，快速暴露环境问题）。"""
    client = OrangeHRMClient()
    assert client.login(settings.USERNAME, settings.PASSWORD), "前置登录失败"
    return PIMApi(client)


def test_login_success():
    # API-01：正确凭证 → 会话建立
    client = OrangeHRMClient()
    assert client.login(settings.USERNAME, settings.PASSWORD) is True


def test_login_wrong_password():
    # API-02：错误凭证 → 登录失败（M0 UI 实测同源结论的接口层验证）
    client = OrangeHRMClient()
    assert client.login(settings.USERNAME, "wrongpass123") is False


def test_employees_requires_session():
    # API-03：匿名会话调业务接口 → 401（实测文案 "Session expired"）
    pim = PIMApi(OrangeHRMClient())  # 不 login，保持匿名
    resp = pim.list_employees(limit=1)
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Session expired"


def test_employees_list_structure(pim):
    # API-04：登录后 → 200 + 结构三件套 + 员工关键字段
    resp = pim.list_employees()
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["data"], list)
    assert body["meta"]["total"] > 0  # 共享环境实测 331+ 条，恒大于 0
    # 首条记录关键字段（实测字段名，M5 数据工厂依赖 employeeId 等）
    first = body["data"][0]
    for field in ("empNumber", "lastName", "firstName", "employeeId"):
        assert field in first


def test_employees_pagination_limit(pim):
    # API-05：limit=1 只返回 1 条，但 meta.total 与全量一致（分页不改总数）
    resp = pim.list_employees(limit=1)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 1
    full = pim.list_employees().json()
    assert body["meta"]["total"] == full["meta"]["total"]

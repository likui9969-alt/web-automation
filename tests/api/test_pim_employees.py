"""M4 首批 API 测试 —— PIM 员工列表接口 + 会话鉴权。

对照 UI 层（test_login.py）：本文件没有浏览器、没有定位器、没有页面等待——
同环境实测下每条用例只需 1~3 个 HTTP 往返，这就是测试金字塔"API 层做主力"
的原因：快、稳、直接验证业务规则。

全部断言依据 2026-09-15 六轮探测实测（MODULE_FEEDBACK 验证记录），
无一条"理论上应该如此"。

测试点：
- API-01 正向登录成功（302 → dashboard）
- API-02 错误凭证登录失败（302 回登录页，不建立会话）
- API-03 未登录调业务接口 → 401 "Session expired"（会话校验）
- API-04 登录后员工列表 → 200 + JSON 结构 + 关键字段
- API-05 limit 分页语义：返回条数受控、total 不受影响
- API-06/07 用户名大小写与空格的服务端规则（LOGIN-07/08，M0 指派 API 层）
- API-08 无效查询参数 → 422（M5 探测实证，Review 整改 R-01 落地）
- API-09 删除不存在的记录 → 404（M5 探测实证，Review 整改 R-01 落地）
"""
import allure
import pytest

from api.client import OrangeHRMClient
from api.pim import PIMApi
from config import settings
from data.credentials import WRONG_PASSWORD
from utils.factory import make_employee

pytestmark = [
    pytest.mark.api,  # 分层 marker：CI 里 pytest -m api 先跑快的接口层
    allure.feature("PIM 接口（API 层主力）"),  # M8：报告按业务模块归类
]


@pytest.fixture
def pim() -> PIMApi:
    """已登录的 PIM API（登录失败会让 fixture 直接报错，快速暴露环境问题）。"""
    client = OrangeHRMClient()
    assert client.login(settings.USERNAME, settings.PASSWORD), "前置登录失败"
    return PIMApi(client)


@allure.title("正确凭证登录建立会话")
@allure.severity(allure.severity_level.CRITICAL)
def test_login_success():
    # API-01：正确凭证 → 会话建立
    client = OrangeHRMClient()
    assert client.login(settings.USERNAME, settings.PASSWORD) is True


@allure.title("错误凭证登录失败且不建立会话")
@allure.severity(allure.severity_level.NORMAL)
def test_login_wrong_password():
    # API-02：错误凭证 → 登录失败（M0 UI 实测同源结论的接口层验证）
    client = OrangeHRMClient()
    assert client.login(settings.USERNAME, WRONG_PASSWORD) is False


@allure.title("匿名会话访问业务接口被拒绝（401）")
@allure.severity(allure.severity_level.CRITICAL)
def test_employees_requires_session():
    # API-03：匿名会话调业务接口 → 401（实测文案 "Session expired"）
    pim = PIMApi(OrangeHRMClient())  # 不 login，保持匿名
    resp = pim.list_employees(limit=1)
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Session expired"


@allure.title("登录后员工列表结构与关键字段完整")
@allure.severity(allure.severity_level.CRITICAL)
def test_employees_list_structure(pim):
    # API-04：登录后 → 200 + 结构三件套 + 员工关键字段。
    # 结构断言不依赖环境既有数据（全面复审 P2-2）：自造一条唯一员工——
    # total >= 1 由"刚创建"保证（设计保证，非"环境里恰好有人"的运气），
    # 关键字段断言取 search_by_name 命中的自己那条，不碰 data[0]
    # （list 默认 limit=50，自己的记录未必在第一页；唯一名搜索则必然命中）
    emp = make_employee()
    resp = pim.create_employee(emp["firstName"], emp["lastName"], emp["middleName"])
    assert resp.ok, f"造数失败: {resp.status_code} {resp.text[:200]}"
    emp_number = resp.json()["data"]["empNumber"]
    try:
        resp = pim.list_employees()
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["data"], list)
        assert body["meta"]["total"] >= 1
        # 关键字段（实测字段名，M5 数据工厂依赖 employeeId 等）：
        # 模糊搜索唯一 lastName 后按主键精确过滤出自己那条
        matched = pim.search_by_name(emp["lastName"]).json()["data"]
        mine = [e for e in matched if e["empNumber"] == emp_number]
        assert mine, "刚创建的员工搜不到——落库失败或搜索接口异常"
        for field in ("empNumber", "lastName", "firstName", "employeeId"):
            assert field in mine[0]
    finally:
        # 清理校验（独立复审二轮 P2-3）：同仓标准统一——DB 用例已校验，
        # API 用例同样要校验清理结果，失败即报 error（残留可见，非静默）
        resp = pim.delete_employee(emp_number)
        assert resp.ok, f"清理失败（emp_number={emp_number} 残留）: {resp.status_code}"


@allure.title("分页参数控制返回条数且不影响总数")
@allure.severity(allure.severity_level.NORMAL)
def test_employees_pagination_limit(pim):
    # API-05：limit=1 只返回 1 条；total 恒 >= 返回条数（分页不改总数语义）。
    # 独立复审二轮 P2-3：不再比较两次调用的 total——共享环境毫秒窗口内他人
    # 造数会造成偶发不等（假红）。语义断言：total 是总数，必然 >= 本页条数。
    resp = pim.list_employees(limit=1)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 1
    assert body["meta"]["total"] >= 1
    assert body["meta"]["total"] >= len(body["data"])


@allure.title("用户名大小写不敏感（服务端规则）")
@allure.severity(allure.severity_level.NORMAL)
def test_login_username_case_insensitive():
    # API-06 / LOGIN-07：用户名不区分大小写（M0 Demo UI 实测，接口层回归）。
    # 用户名取 settings 而非硬编码 "Admin"——Demo 与本地 Docker 双环境通用
    # （本地行为 2026-09-15 实测与 Demo 一致：upper() 登录成功）
    client = OrangeHRMClient()
    assert client.login(settings.USERNAME.upper(), settings.PASSWORD) is True


@allure.title("用户名首尾空格不被忽略（服务端规则）")
@allure.severity(allure.severity_level.NORMAL)
def test_login_username_whitespace_rejected():
    # API-07 / LOGIN-08：用户名不做 trim（M0 Demo 实测" Admin "登录失败）。
    # 带空格用户名 + 正确密码 → 拒绝：证明服务端不自动去首尾空格
    # （本地行为 2026-09-15 实测一致：False）
    client = OrangeHRMClient()
    assert client.login(f" {settings.USERNAME} ", settings.PASSWORD) is False


@allure.title("无效查询参数被服务端拒绝（422）")
@allure.severity(allure.severity_level.NORMAL)
def test_employees_invalid_param_rejected(pim):
    # API-08：无效查询参数 → 422（M5 探测实证，响应体结构本地实测）。
    # 断言两层：error.message 文案 + invalidParamKeys 指明被拒参数名——
    # 后者是服务端参数校验的精确信号（比单纯文案断言业务价值更高）
    resp = pim.list_employees_by_last_name("nonexistent")
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["message"] == "Invalid Parameter"
    assert "lastName" in error["data"]["invalidParamKeys"]


@allure.title("删除不存在的记录返回 404")
@allure.severity(allure.severity_level.NORMAL)
def test_delete_missing_employee_404(pim):
    # API-09：删除不存在的记录 → 404（M5 探测实证）。
    # empNumber 用远超自增范围的值——共享环境他人数据再多也不误伤；
    # 不存在 → 不产生数据，无需清理
    resp = pim.delete_employee(999_999_999)
    assert resp.status_code == 404
    assert resp.json()["error"]["message"] == "Records Not Found"
"""M6 DB 校验用例 —— API 操作与数据库持久化的一致性验证。

本层回答的核心问题（M6 面试主题）：
API 返回 200、UI 显示 "Successfully Saved"，数据就真的持久化正确了吗？
应用层的一切"成功"都只是声明；DB 行是最终事实源。

分层定位：DB 校验不是独立于 api/ui 的平行层，而是对既有操作的
「验证增强」——当被测点是数据一致性时，直接查库比"再用 API 查一遍"
更可靠（API 可能命中缓存，DB 不会）。所以本文件的操作全部复用 api 层，
只在验证环节下沉到 DB。

断言时机：操作返回后立即查库。若业务是异步落库，这个时机必然测出
竞态（先查不到后查到）——OrangeHRM 同步写库，2026-09-15 探测实测为
操作返回即可查到，无等待窗口。

实测依据（2026-09-15 _probe_m6.py 探测 + 独立复审双向对照，非推测）：
- API 创建 → 行存在，emp_firstname/emp_lastname 与提交一致，purged_at NULL
- API 删除 → 行物理消失（硬删，purged_at 未被使用），API 搜索同步归零
- 硬删 vs 软删才是「DB 校验层的真实价值」：软删时行仍在 + 标记位，API 视角
  无法区分（API 会过滤软删行），只有查库知道。employee_id 在创建后为 NULL
  属 API 响应可见事实（响应体含 employeeId: None），不构成 DB 层论据——
  M6 独立复审 P2-2 修正，代码注释同步改正
"""
import allure
import pytest

from api.pim import PIMApi
from utils.factory import make_employee

pytestmark = [
    pytest.mark.db,
    allure.feature("DB 持久化校验（M6，仅本地环境）"),  # M8：报告按业务模块归类
]

_ROW_BY_EMP_NUMBER = (
    "SELECT emp_number, emp_firstname, emp_lastname, purged_at "
    "FROM hs_hr_employee WHERE emp_number = %s"
)


@pytest.fixture
def pim_api(api_client) -> PIMApi:
    """复用 session 级 api_client（与 e2e 同模式）：造数/清理走共享会话。"""
    return PIMApi(api_client)


@allure.title("API 创建员工 → 数据库中行存在且字段一致")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_created_employee_persisted_in_db(db_client, pim_api):
    """API 创建员工 → hs_hr_employee 行存在且字段一致。

    这是「页面/接口显示成功 ≠ 成功」的最直接反例构造：
    如果应用存在异步写失败/字段截断/触发器改写，本用例会当场暴露。

    参数序（P1-1 修复）：db_client 在签名首位——pytest 按参数从左到右
    实例化 fixture，门控（skip/raise）先于 pim_api → api_client 求值，
    保证非本地环境"不产生任何网络调用就 skip"，而非先公网登录再 skip。
    """
    emp = make_employee()
    resp = pim_api.create_employee(emp["firstName"], emp["lastName"], emp["middleName"])
    assert resp.ok, f"API 创建失败：{resp.status_code}"
    emp_number = resp.json()["data"]["empNumber"]
    try:
        row = db_client.query_one(_ROW_BY_EMP_NUMBER, (emp_number,))
        assert row is not None, "API 返回成功但库中无行——持久化失败"
        assert row["emp_firstname"] == emp["firstName"], "落库 firstName 与提交值不一致"
        assert row["emp_lastname"] == emp["lastName"], "落库 lastName 与提交值不一致"
        assert row["purged_at"] is None, "新建记录不应处于软删状态"
    finally:
        # 失败安全清理（M5 Review P2-1 同款教训）：断言挂了也要删数据
        pim_api.delete_employee(emp_number)


@allure.title("API 删除员工 → 数据库中行物理消失（硬删）")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_deleted_employee_removed_from_db(db_client, pim_api):
    """API 删除员工 → DB 行物理移除（硬删）。

    删除验证的价值：M5 只从 API 搜索归零推断"删干净了"，本用例下沉到
    行级确认——如果 OrangeHRM 实际是软删（行还在 + 标记位），API 视角
    看不出来，只有查库知道。实测为硬删，断言按真实行为写。

    失败安全清理（独立复审 P2-1 修复）：delete 断言失败时员工已创建，
    finally 兜底删除——否则残留永久行，破坏"DB 零残留"基线；
    容忍 404 = 员工已被删（幂等，重复删无害）。
    """
    emp = make_employee()
    resp = pim_api.create_employee(emp["firstName"], emp["lastName"], emp["middleName"])
    assert resp.ok, f"前置创建失败：{resp.status_code}"
    emp_number = resp.json()["data"]["empNumber"]
    try:
        assert pim_api.delete_employee(emp_number).ok, "API 删除失败"
        row = db_client.query_one(
            "SELECT emp_number FROM hs_hr_employee WHERE emp_number = %s",
            (emp_number,),
        )
        assert row is None, "API 已删但行仍留在库中（实测为硬删，应物理移除）"
    finally:
        cleanup = pim_api.delete_employee(emp_number)
        assert cleanup.status_code in (200, 404), \
            f"失败安全清理异常（emp_number={emp_number} 可能残留）: {cleanup.status_code}"

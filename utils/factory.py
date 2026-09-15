"""utils/factory.py — 测试数据工厂（M5 激活 utils/ 层）。

为什么必须唯一命名（C2 约束的工程对策）：
M0 实证员工总数 3 分钟内 315→316（他人同时造数）；
M5 探测时段列表 total 331→363。共享环境里固定命名必撞车：
断言"存在"分不清是自己的还是别人的，清理还可能误删他人数据。

设计：时间戳（肉眼可读，排障时认得出是自动化产物）
+ 随机后缀（同秒并发唯一）。不依赖外部状态，无清理负担。
"""
import random
import time


def unique_tag() -> str:
    """MMddHHmmss + 3 位随机数。跨运行唯一。"""
    return time.strftime("%m%d%H%M%S") + f"{random.randint(0, 999):03d}"


def make_employee() -> dict:
    """PIM 员工造数模板（字段与 api/pim.py 的 create_employee 对齐）。"""
    tag = unique_tag()
    return {
        "firstName": f"Auto{tag}",
        "middleName": "",
        "lastName": f"M5{tag}",
    }

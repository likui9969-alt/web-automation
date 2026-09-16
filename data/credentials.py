"""data/credentials.py — 登录模块测试数据（M2 激活 data/ 层）。

为什么外置：参数组是"数据"，测试文件是"逻辑"。
加一组错误凭证不需要碰测试代码；非开发同事也能看懂改哪里。

为什么是 Python 模块而不是 YAML/JSON：
当前只有 3 组元组，引入解析依赖不划算（KISS）。
M5 数据工厂需要生成"唯一命名数据"时再考虑结构化格式。
"""

# LOGIN-02 参数组：M0 实测防枚举设计——任意错误组合统一提示
# "Invalid credentials"，所以三组共用一条断言（见 test_login_invalid_credentials）
INVALID_CREDENTIAL_CASES = [
    ("Admin", "wrongpass123"),      # 错误密码
    ("nosuchuser", "admin123"),     # 错误用户名
    ("nosuchuser", "wrongpass123"), # 双双错误
]

# 错误密码（API 层 API-02 单独用，与上面参数组同源语义——Review 整改 R-06：
# 此前 API 测试内联硬编码 "wrongpass123"，与数据分离原则不一致，同仓库两种做法）
WRONG_PASSWORD = "wrongpass123"

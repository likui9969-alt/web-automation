# M10：测试执行环境容器化（被测系统部署见 docker/docker-compose.yml，M6）
#
# 为什么需要本 Dockerfile（M10 主题，interview-ready）：
#   M1–M9 的测试在宿主机 venv 跑，环境一致性只靠 requirements.txt + README 步骤
#   保证。Docker 把「测试代码 + Python + Playwright + Chromium」固化为一个不可变
#   镜像：换机器 / CI / 面试演示，一条 docker compose 命令即得一致测试环境。
#
# 为什么不能一开始就用 Docker（PLAN M10 面试题反向）：
#   M1 起就是先本地跑通再容器化——先痛后治。容器化有真实成本（镜像体积、
#   构建时间、网络依赖、调试链路加长），只有当"环境不一致"成为真痛点
#   （换机器、CI、交付演示）才值得引入。这也是"M10 才做"的原因。

FROM python:3.11-slim

# Playwright Chromium 运行所需系统库（--with-deps 会自动 apt-get，先 root）
# 注意 fontconfig + fonts-liberation 必不可少（M10 容器内实测踩坑）：
# 缺字体时 Chromium 渲染文本即崩——FATAL SkFontMgr_FontConfigInterface
# "Not implemented" + "Cannot load default config file"，浏览器进程直接退出
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
        libxrandr2 libgbm1 libasound2 \
        fontconfig fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依赖先 COPY（利用层缓存：requirements 不变则 pip 层不重建）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium 装进项目内路径（与 conftest setdefault 的约定一致：项目 .playwright-browsers）
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers
RUN python -m playwright install chromium

# 项目代码（.dockerignore 已排除 venv/browsers/reports/git）
COPY . .

# 非 root 运行：chromium 在容器内以 root 跑需要 --no-sandbox，
# 用非 root 用户既安全又避免该问题（image 默认用户）
RUN useradd -m tester && chown -R tester:tester /app
USER tester

# 默认入口：分层执行（与 CI workflow 一致：API 快先反馈）
# 覆盖方式：docker compose run --rm test python -m pytest
ENTRYPOINT ["python", "-m", "pytest"]
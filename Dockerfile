# PipelinePilot backend - FastAPI app + MCP pipeline server, one image.
#
# Mirrors the local two-venv setup (.venv-sdk / .venv) exactly, because the
# OpenAI Agents SDK pins mcp<2 while the FastMCP server needs mcp 2.x - the
# two can't share one environment. The app venv spawns the server venv's
# interpreter as a subprocess over stdio at runtime (same as SERVER_PYTHON
# does locally), so BOTH venvs have to exist side by side in the running
# container, not just at build time.
#
# cryptography and pydantic/pydantic-core both ship prebuilt wheels for
# 3.14 (cryptography via its cp311-abi3 stable-ABI wheel, which covers any
# CPython 3.11+), so no compiler toolchain is needed here - keeps the image
# small and the build fast, which matters on a t3.micro.

FROM python:3.14-slim-bookworm

WORKDIR /app

# --- Server venv (FastMCP + mcp 2.x) ---
COPY requirements.server.txt ./
RUN python -m venv /opt/venv-server \
    && /opt/venv-server/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv-server/bin/pip install --no-cache-dir -r requirements.server.txt

# --- App venv (FastAPI + openai-agents + mcp<2) ---
COPY requirements.app.txt ./
RUN python -m venv /opt/venv-app \
    && /opt/venv-app/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv-app/bin/pip install --no-cache-dir -r requirements.app.txt

# --- Application code ---
# frontend/ is built separately and served by Nginx, not by this
# container - intentionally not copied in. agent/ (the v1 hand-built CLI)
# is also not part of the deployed web service - not copied in either.
COPY web/ web/
COPY agent_sdk/ agent_sdk/
COPY server/ server/
COPY db/ db/
COPY data/ data/

# SERVER_PYTHON mirrors the local-dev env var exactly: the app venv spawns
# the MCP server as a subprocess using the SERVER venv's interpreter.
ENV SERVER_PYTHON=/opt/venv-server/bin/python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD /opt/venv-app/bin/python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=3).status == 200 else 1)"

CMD ["/opt/venv-app/bin/python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8001"]
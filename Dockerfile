FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY src/ src/
COPY migrations/ migrations/

RUN uv pip install --system .

EXPOSE 8000

ENV FASTMCP_STATELESS_HTTP=true

CMD ["uvicorn", "tastebud.main:app", "--host", "0.0.0.0", "--port", "8000"]

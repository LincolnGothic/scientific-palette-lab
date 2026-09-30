FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY palette_lab ./palette_lab
RUN pip install --no-cache-dir .

CMD ["python", "-m", "palette_lab", "serve"]

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1 \
		PIP_NO_CACHE_DIR=1 \
		STREAMLIT_SERVER_HEADLESS=true \
		STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Copy dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application files.
COPY . .

EXPOSE 8501

# Use Python for healthcheck because curl is not installed in slim images.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
	CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3); sys.exit(0)"

# Support cloud platforms that inject PORT while keeping 8501 as local default.
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]

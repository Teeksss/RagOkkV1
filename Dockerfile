FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install language models
RUN python -m spacy download en_core_web_sm
RUN python -m nltk.downloader punkt stopwords averaged_perceptron_tagger wordnet

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/data

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "rag_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
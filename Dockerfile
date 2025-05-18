FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libgl1 \
    libsm6 \
    libxrender1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*
	
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p results

EXPOSE 5000

CMD ["python", "entity_detection.py"]
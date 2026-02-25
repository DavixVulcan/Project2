FROM python:3.11-slim
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY python-webapp/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy your webapp code first
COPY python-webapp /app

# Copy proto and generate AFTER, so it overwrites anything copied in
COPY proto /proto
RUN python -m grpc_tools.protoc -I /proto \
    --python_out=/app --grpc_python_out=/app \
    /proto/auth.proto

EXPOSE 5000
CMD ["python", "app.py"]
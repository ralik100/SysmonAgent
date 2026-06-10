FROM python:3.11-slim

WORKDIR /client

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY /src/agent .

ENTRYPOINT ["python","main.py"]
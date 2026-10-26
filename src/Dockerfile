FROM python:3.14.8-slim

WORKDIR /client

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY agent filehandler.py ./src/

ENTRYPOINT ["python","src/client.py"]
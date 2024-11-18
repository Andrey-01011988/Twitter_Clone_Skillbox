FROM python:3.11

RUN apt-get update && apt-get install -y python3-dev && rm -rf /var/lib/apt/lists/*

COPY /project/server /server
RUN pip install -r /server/requirements.txt

WORKDIR /server

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
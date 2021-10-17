FROM ubuntu:20.04

RUN apt update -y
RUN apt install python3-pip libolm-dev libolm3 -y

COPY requirements.txt /requirements.txt
RUN python3 -m pip install -r requirements.txt

VOLUME ["/nio_store"]
VOLUME ["/src"]

COPY credentials.json /credentials.json

CMD ["python3", "src/main.py"]

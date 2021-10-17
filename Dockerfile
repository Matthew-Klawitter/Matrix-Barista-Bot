FROM ubuntu:20.04

COPY requirements.txt /requirements.txt
COPY credentials.json /credentials.json

RUN apt update -y
RUN apt install python3-pip libolm-dev libolm3 -y
RUN python3 -m pip install -r requirements.txt

VOLUME ["/nio_store"]
VOLUME ["/src"]

CMD ["python3", "src/main.py"]

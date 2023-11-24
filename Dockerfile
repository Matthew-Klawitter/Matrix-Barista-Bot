FROM ubuntu:20.04

RUN apt update -y
RUN apt install python3-pip libolm-dev libolm3 -y
RUN apt install libopus0 -y

ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt update -y && apt install ffmpeg -yq


COPY requirements.txt /requirements.txt
RUN python3 -m pip install -r requirements.txt

VOLUME ["/nio_store"]
VOLUME ["/src"]

CMD ["python3", "src/main.py"]

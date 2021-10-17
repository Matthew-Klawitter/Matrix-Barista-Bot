FROM ubuntu:20.04

COPY . .
RUN apt update -y
RUN apt install python3-pip libolm-dev libolm3 -y
RUN python3 -m pip install -r requirements.txt

CMD ["python3", "src/main.py"]

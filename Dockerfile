FROM ubuntu:22.04

ENV TZ=Asia/Tokyo
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y language-pack-ja
RUN apt-get install -y python3 python3-pip

RUN apt-get install -y python3-yaml python3-coloredlogs
RUN apt-get install -y python3-pil python3-matplotlib python3-pandas
RUN apt-get install -y python3-paramiko

RUN apt-get clean

RUN pip3 install 'influxdb-client[ciso]'

WORKDIR /opt/kindle_power
COPY . .

CMD ["./src/display_image.py"]

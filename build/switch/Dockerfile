FROM golang:1.20 AS build

WORKDIR /usr/src/l2sm-switch

COPY ./src/switch/ ./build/switch/build-go.sh ./

RUN chmod +x ./build-go.sh && ./build-go.sh

#We install the Python dependencies
FROM python:3.12 AS python

WORKDIR /usr/src/app

COPY ./src/switch/requirements.txt ./

RUN pip install -r requirements.txt

FROM ubuntu:latest

WORKDIR /usr/local/bin

COPY ./src/switch/vswitch.ovsschema /tmp/

COPY --from=build /usr/local/bin/ ./

RUN apt-get update && \
  apt-get install -y net-tools iproute2 netcat-openbsd dnsutils curl iputils-ping iptables nmap tcpdump openvswitch-switch && \
  mkdir /var/run/openvswitch && mkdir -p /etc/openvswitch && ovsdb-tool create /etc/openvswitch/conf.db /tmp/vswitch.ovsschema

COPY ./src/switch/setup_switch.sh ./

RUN chmod +x ./setup_switch.sh && \
    mkdir /etc/l2sm/

# Copy Python binaries and libraries from the Python stage
COPY --from=python /usr/local/lib /usr/local/lib
COPY --from=python /usr/local/include /usr/local/include
COPY --from=python /usr/local/bin /usr/local/bin

# Copy the Python script
COPY ./src/switch/l2sm-switch.py ./

CMD ["python3", "l2sm-switch.py"]

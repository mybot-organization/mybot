FROM ubuntu:latest as base
WORKDIR /tmp
COPY ./install.sh ./
RUN sh install.sh
CMD ["xgettext"]

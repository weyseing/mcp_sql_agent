FROM python:3.13.3

COPY ./ /app
WORKDIR /app

CMD ["tail", "-f", "/dev/null"]
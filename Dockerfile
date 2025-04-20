FROM python:3.13.3

# copy app files
COPY ./ /app
WORKDIR /app

# python packages
RUN pip install uv
RUN uv sync

# entrypoint
CMD ["tail", "-f", "/dev/null"]
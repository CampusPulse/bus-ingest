FROM python:3.9.2-buster
LABEL name=bus-data-ingest

RUN useradd -m scraper && mkdir bus-data-ingest && chown scraper:scraper bus-data-ingest

COPY ./ /bus-data-ingest/

USER scraper

WORKDIR /bus-data-ingest

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
ENV PATH "/home/vaccine/.poetry/bin:$PATH"
RUN /home/vaccine/.poetry/bin/poetry config virtualenvs.create false && \
    /home/vaccine/.poetry/bin/poetry install --extras lint --no-interaction --no-ansi

CMD ["bash"]

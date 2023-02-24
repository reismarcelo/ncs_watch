FROM python:3.11-alpine AS build

WORKDIR /build

RUN apk update && apk upgrade && apk add --no-cache git && \
    pip install --no-cache-dir --upgrade pip setuptools wheel build && \
    git clone https://github.com/reismarcelo/ncs_watch.git && \
    python3 -m build ncs_watch

FROM python:3.11-alpine

COPY --from=build /build/ncs_watch/dist /ncs_watch_wheel

RUN apk update && apk upgrade && apk add --no-cache openssh bash && \
    pip install --no-cache-dir --upgrade pip setuptools netmiko PyYAML pydantic && \
    pip install --no-cache-dir --upgrade --no-index --find-links /ncs_watch_wheel ncs_watch

VOLUME /shared-data

WORKDIR /shared-data

CMD ["/bin/bash"]

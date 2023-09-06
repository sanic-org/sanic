ARG BASE_IMAGE_ORG
ARG BASE_IMAGE_NAME
ARG BASE_IMAGE_TAG

FROM ${BASE_IMAGE_ORG}/${BASE_IMAGE_NAME}:${BASE_IMAGE_TAG}

RUN apk update
RUN update-ca-certificates

ARG SANIC_PYPI_VERSION

RUN pip install -U pip && pip install sanic==${SANIC_PYPI_VERSION}
RUN apk del build-base

# docker build -t vocabai/baserow-clt:1.26.1-11.3.2-a -f baserow_clt.Dockerfile .
# docker push vocabai/baserow-clt:1.26.1-11.3.2-a

ARG BASEROW_IMAGE_VERSION=1.33.4
FROM baserow/baserow:${BASEROW_IMAGE_VERSION}

# arguments
ARG CLT_VERSION
ARG CLT_REQUIREMENTS_VERSION

# install packages first
RUN apt-get update -y && apt-get install -y libasound2 wget procps iproute2 nano

RUN . /baserow/venv/bin/activate && pip3 install clt_requirements==${CLT_REQUIREMENTS_VERSION} && pip3 cache purge
RUN . /baserow/venv/bin/activate && pip3 install cloudlanguagetools==${CLT_VERSION} && pip3 cache purge


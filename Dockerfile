# docker build -t vocabai/baserow-vocabai-plugin:20220910-1 -f Dockerfile .
# docker push vocabai/baserow-vocabai-plugin:20220910-1

ARG BASE_BASEROW_CLT_IMAGE=vocabai/baserow-clt:1.33.4-11.3.2-a
FROM ${BASE_BASEROW_CLT_IMAGE}

ARG SENTRY_RELEASE
ENV SENTRY_RELEASE=${SENTRY_RELEASE:-baserow-vocabai@0.0.0}

COPY ./plugins/baserow_vocabai_plugin/ /baserow/plugins/baserow_vocabai_plugin/
RUN /baserow/plugins/install_plugin.sh --folder /baserow/plugins/baserow_vocabai_plugin

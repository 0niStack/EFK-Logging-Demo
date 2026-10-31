ARG FLUENTD_IMAGE=fluent/fluentd:v1.16-debian-1
FROM ${FLUENTD_IMAGE}

USER root
RUN gem install fluent-plugin-elasticsearch --no-document --version 5.4.3
USER fluent

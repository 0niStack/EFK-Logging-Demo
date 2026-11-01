ARG FLUENTD_IMAGE=fluent/fluentd:v1.16-debian-1
FROM ${FLUENTD_IMAGE}

USER root

RUN gem install elasticsearch -v 8.15.0 --no-document \
 && gem install fluent-plugin-elasticsearch -v 5.4.3 --no-document \
 && gem uninstall elasticsearch -I -v '>= 9' || true
 
USER fluent

#!/usr/bin/env bash
IMAGE="ncs-watch:latest"
WORKDIR="ncs-watch-data"

ENV_VARS=( \
  "NCS_WATCH_USER" \
  "NCS_WATCH_PASSWORD"
)

ENV_PARAM=""
for ENV_VAR in ${ENV_VARS[*]}; do
  if [[ ! -z "${!ENV_VAR}" ]]; then
    ENV_PARAM="$ENV_PARAM --env $ENV_VAR=${!ENV_VAR}"
  fi
done

if [[ ! -d "$WORKDIR" ]]; then
  mkdir "$WORKDIR"
fi

docker run -it --rm --hostname ncs_watch $ENV_PARAM --mount type=bind,source="$(pwd)"/"$WORKDIR",target=/shared-data $IMAGE ncs_watch "$@"

#!/usr/bin/env bash
set -Eeuo pipefail

# prepare destination
DIRNAME=`dirname $(readlink -f $0)`
mkdir -p $DIRNAME/dist
test "$(ls -A $DIRNAME/dist/)" && rm -r $DIRNAME/dist/*

# extract PROJ version from Dockerfile
PROJ_VERSION=`cat $DIRNAME/Dockerfile | sed -n 's/^FROM .*:\(.*\)$/\1/p'`
echo "PROJ_VERSION=$PROJ_VERSION"

# extract PYPROJ version from requirements.txt
PYPROJ_VERSION=`cat $DIRNAME/requirements.txt | sed -n 's/^pyproj==\(.*\)$/\1/p'`
echo "PYPROJ_VERSION=$PYPROJ_VERSION"

DOCKER_TAG="crs-explorer:$PROJ_VERSION"
STOP_COUNTER="${1:-0}"

# build container
docker build --pull --platform=linux/amd64 --build-arg PYPROJ_VERSION=$PYPROJ_VERSION --tag $DOCKER_TAG $DIRNAME

# execute container
docker run --user $(id -u):$(id -g) -e STOP_COUNTER=$STOP_COUNTER --rm -v "$DIRNAME/dist:/home/dist" $DOCKER_TAG

# done
echo .
echo Enjoy the generated code at $DIRNAME/dist/

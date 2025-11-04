#!/bin/bash
set -e

export DOCKER_BUILDKIT=1

# Build depending on input argument
if [ "$1" == "yum" ]; then
    build_file="debug/Dockerfile.yum"
    tag="custom-manylinux_2_28_x86_64"
    cache=""
elif [ "$1" == "cmake" ]; then
    build_file="debug/Dockerfile.cmake"
    tag="custom-manylinux_2_28_x86_64-epigeec-built"
    cache="--no-cache"
else
    echo "Usage: $0 [yum|cmake]"
    exit 1
fi

docker build $cache --build-arg USER_UID=$(id -u) --build-arg USER_GID=$(id -g) -f $build_file -t $tag .

echo "Custom manylinux image '$tag' built successfully."
echo "You can now use this image in cibuildwheel or run it directly."
echo "To debug cibuildwheel builds using this image, run debug/debug_cibuildwheel.sh $tag"
echo "To enter the image interactively, run:"
echo "docker run -it --rm -v [root-of-project]:/io $tag bash"


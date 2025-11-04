# syntax=docker/dockerfile:1
FROM custom-manylinux_2_28_x86_64

LABEL description="Building epigeec binaries into custom-manylinux_2_28_x86_64 image."

# Create a non-root user to match host user IDs

ARG USER_UID
ARG USER_GID

RUN groupadd --gid ${USER_GID} dockeruser && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m dockeruser

# Create work directory and copy source tree from build context
# Docker always does COPY as root
WORKDIR /project
COPY . .
RUN chown -R ${USER_UID}:${USER_GID} /project

# Switch to non-root user, so cmake and make do not create root-owned files
# Switch to non-root user
USER dockeruser

# Build in a separate 'build/' directory (does not require .git, can't run git clean)
RUN mkdir -p build && \
    cd build && \
    cmake .. && \
    make -j "$(nproc --all)"

# Default entrypoint
CMD ["/bin/bash"]

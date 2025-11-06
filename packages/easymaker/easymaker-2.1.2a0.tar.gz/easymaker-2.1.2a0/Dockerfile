FROM 47a6bb45-kr1-registry.container.nhncloud.com/docker.io/library/python:3.10-slim AS python
# 사내에 nexus로 미러링해서 제공하고 있지만 EasyMaker도 자체적으로 이미지 캐시를 사용하고 있으므로 EasyMaker 이미지 캐시를 사용

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /usr/build

ENV UV_LINK_MODE=copy

ARG MOUNT_OPTIONS=""
# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock${MOUNT_OPTIONS} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml${MOUNT_OPTIONS} \
    uv sync --frozen --no-install-project --no-editable --no-dev

COPY . .

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable --no-dev

# Build the project
RUN uv build

CMD ["ls", "-l", "dist"]

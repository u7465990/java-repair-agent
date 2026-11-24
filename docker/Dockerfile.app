# Self-contained agent image (for release / GHCR).
# Requires d4j-runner:2.0 to exist locally or in a registry.
FROM d4j-runner:2.0

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY skills ./skills
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["java-agent"]

# Immutable minimal Python, no dependencies resolved and no wallet executor.
# Runtime is always network-isolated by deploy/paper/docker-compose.yml.
FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337

ARG ARZ_SOURCE_REVISION=unrecorded
LABEL org.opencontainers.image.title="Arz paper operations (offline only)" \
      org.opencontainers.image.source="https://github.com/DashSaman/Arz" \
      org.opencontainers.image.revision="${ARZ_SOURCE_REVISION}"

ENV PYTHONPATH=/app:/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY LICENSE /app/LICENSE
COPY src/arz/__init__.py src/arz/data.py src/arz/strategies.py /app/src/arz/
COPY scripts/strat01_multi_paper.py \
     scripts/strat01_paper_sbom.py \
     scripts/strat01_paper_runtime.py \
     scripts/strat01_base_identity_forward.py \
     scripts/strat01_capture_slot_preflight.py \
     scripts/strat01_independent_collector.py \
     scripts/strat01_investment_readiness.py \
     scripts/strat01_local_monitor.py /app/scripts/
RUN sha256sum /app/src/arz/*.py /app/scripts/*.py > /app/source-sha256.txt
USER 65534:65534
CMD ["python", "-m", "scripts.strat01_paper_runtime", "serve", "--source-root", "/collector", "--paper-root", "/paper"]

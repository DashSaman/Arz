# The collector uses only the standard library from this immutable base.
# No dependency resolver, credentials, wallet or trading executor is included.
# CI exports this separate target to verify the actual filtered build context.
FROM scratch AS context-audit
COPY . /context/

FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337

ARG ARZ_SOURCE_REVISION=unrecorded
LABEL org.opencontainers.image.title="Arz read-only observation collector" \
      org.opencontainers.image.source="https://github.com/DashSaman/Arz" \
      org.opencontainers.image.revision="${ARZ_SOURCE_REVISION}" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ARZ_COLLECTOR_NETWORK=disabled
WORKDIR /app
COPY LICENSE /app/LICENSE
COPY scripts/strat01_base_identity_forward.py \
     scripts/strat01_capture_slot_preflight.py \
     scripts/strat01_investment_readiness.py \
     scripts/strat01_independent_collector.py \
     scripts/strat01_local_monitor.py \
     scripts/strat01_collector_backup.py /app/scripts/
RUN sha256sum /app/scripts/*.py > /app/source-sha256.txt
USER 65534:65534
CMD ["python", "-m", "scripts.strat01_independent_collector", "serve", "--data-root", "/data"]

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --chown=10001:10001 gridcourier ./gridcourier
COPY --chown=10001:10001 data ./data
COPY --chown=10001:10001 tests ./tests
COPY --chown=10001:10001 README.md SCOPE.md RESULTS.md AI_TOOLS.md WALKTHROUGH.md PORTFOLIO_NOTE.md LICENSE ./
USER 10001:10001
CMD ["python", "-m", "gridcourier.demo"]

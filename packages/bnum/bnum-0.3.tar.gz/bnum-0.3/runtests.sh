uv run ruff check --fix --unsafe-fixes --ignore T100  --ignore ERA001
uv run ruff format
uv run mypy src tests
uv run pytest \
    --cov=bnum \
    --no-cov-on-fail \
    --cov-branch \
    $@

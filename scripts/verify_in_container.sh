#!/usr/bin/env bash
# Copyright (c) 2026 Santiago Hofwimmer
# Run both tutorial suites in the installed IIC-OSIC-TOOLS image.
set -euo pipefail

examples_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
chipify_source="${CHIPIFY_SOURCE:-${examples_root}/../chipify}"
iic_image="${CHIPIFY_IIC_IMAGE:-hpretl/iic-osic-tools:latest}"

if [[ ! -f "${chipify_source}/chipify/__init__.py" ]]; then
    echo "Set CHIPIFY_SOURCE to your Chipify checkout (tested: 1960c81)." >&2
    exit 1
fi
chipify_source="$(cd -- "${chipify_source}" && pwd)"
# --pull=never uses the installed image and makes a missing image explicit.
docker run --rm --pull=never \
    --mount "type=bind,src=${examples_root},dst=/review/examples,readonly" \
    --mount "type=bind,src=${chipify_source},dst=/review/chipify,readonly" \
    --entrypoint /bin/bash "${iic_image}" -lc '
        set -e
        cd /tmp
        python3 -m pip install --disable-pip-version-check --target /tmp/chipify-test-deps pypdf
        export PYTHONPATH="/review/chipify:/tmp/chipify-test-deps:${PYTHONPATH:-}"
        export MPLBACKEND=Agg QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
        python3 -c "import chipify; print(chipify.version_info())"
        python3 /review/examples/scripts/verify_examples.py
        python3 /review/examples/scripts/verify_vacask.py "$@"
    ' bash "$@"

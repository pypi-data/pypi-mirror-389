#!/usr/bin/env bash
# Build the BridgeIt Docker image and launch an interactive Jupyter Lab session
# inside the container with port forwarding for manual testing.
#
# Optional environment variables:
#   IMAGE_NAME          - Tag for the Docker image (default: bridgeit-integration)
#   JUPYTER_PORT        - Host port to expose Jupyter Lab on (default: 9000)
#   JUPYTER_TOKEN       - Token used to authenticate to Jupyter (default: test)
#   JUPYTER_PASSWORD    - Pre-hashed password string for Jupyter ServerApp
#                          (default: sha1 hash for password 'test')
#   JUPYTER_EXTRA_ARGS  - Additional args appended to the jupyter lab command
#   EXTRA_DOCKER_ARGS   - Extra args forwarded to docker run

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-bridgeit-integration}"
JUPYTER_PORT="${JUPYTER_PORT:-9000}"
JUPYTER_TOKEN="${JUPYTER_TOKEN:-test}"
JUPYTER_PASSWORD="${JUPYTER_PASSWORD:-sha1:7465737473616c74:73fa078cf4bb0f67258d55623c7ca488b5e4bdd6}"  # password='test'
JUPYTER_EXTRA_ARGS="${JUPYTER_EXTRA_ARGS:-}"

if [[ ! -f "${ROOT_DIR}/docker/mojo-kernelspec/kernel.json" ]]; then
  cat >&2 <<'EOF'
[warning] Mojo kernelspec not found at docker/mojo-kernelspec/kernel.json.
          Jupyter will start, but bridgeit.install_lang("mojo") will require a
          kernelspec to be copied into that directory.
EOF
fi

echo "Building ${IMAGE_NAME} image ..."
"${ROOT_DIR}/docker-build.sh"

echo "Starting Jupyter Lab inside ${IMAGE_NAME} (port ${JUPYTER_PORT}) ..."

RUN_ENVS=(
  "-e" "MOJO_KERNELSPEC_DIR=/workspace/docker/mojo-kernelspec"
  "-e" "JUPYTER_TOKEN=${JUPYTER_TOKEN}"
  "-e" "JUPYTER_PASSWORD=${JUPYTER_PASSWORD}"
  "-e" "JUPYTER_EXTRA_ARGS=${JUPYTER_EXTRA_ARGS}"
)

RUN_MOUNTS=(
  "-v" "${ROOT_DIR}:/workspace"
  "-v" "${ROOT_DIR}:/usr/local/lib/python3.12/site-packages/bridgeit-src:ro"
)

RUN_ARGS=(
  "-p" "${JUPYTER_PORT}:8888"
  "-it"  # interactive to view logs / interrupt
)

if [[ -n "${EXTRA_DOCKER_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  RUN_ARGS+=( ${EXTRA_DOCKER_ARGS} )
fi

CMD=(docker run --rm)
CMD+=( "${RUN_ARGS[@]}" )
CMD+=( "${RUN_MOUNTS[@]}" )
CMD+=( "${RUN_ENVS[@]}" )
CMD+=( "${IMAGE_NAME}" )
CMD+=( bash -lc 'cd /workspace && export PATH="$HOME/.local/bin:$PATH" && export BRIDGEIT_DEV_PATH=/usr/local/lib/python3.12/site-packages/bridgeit-src && exec jupyter lab --ip=0.0.0.0 --no-browser --allow-root --ServerApp.token="$JUPYTER_TOKEN" --ServerApp.password="$JUPYTER_PASSWORD" $JUPYTER_EXTRA_ARGS' )

"${CMD[@]}"

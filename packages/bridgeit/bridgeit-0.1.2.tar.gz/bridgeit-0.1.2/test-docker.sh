#!/usr/bin/env bash
# Build the BridgeIt Docker image and execute the integration notebooks inside it.
#
# Optional environment variables:
#   IMAGE_NAME        - Name for the built image (default: bridgeit-integration)
#   SKIP_DOCKER_BUILD - Set to "1" to skip building and use existing image
#   EXTRA_DOCKER_ARGS - Additional arguments forwarded to docker run.
#
# The script expects a Mojo kernelspec under docker/mojo-kernelspec/ and relies on
# `bridgeit.install("mojo")` to install the Mojo toolchain via pixi.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-bridgeit-integration}"

if [[ "${SKIP_DOCKER_BUILD:-}" != "1" ]]; then
  echo "Building ${IMAGE_NAME} image from ${ROOT_DIR} ..."
  docker build -f "${ROOT_DIR}/docker/Dockerfile" -t "${IMAGE_NAME}" "${ROOT_DIR}"
else
  echo "Skipping Docker build (SKIP_DOCKER_BUILD=1), using existing image..."
fi

declare -a RUN_ENVS=( "-e" "MOJO_KERNELSPEC_DIR=/workspace/docker/mojo-kernelspec" )
declare -a RUN_MOUNTS=( "-v" "${ROOT_DIR}:/workspace" )
declare -a RUN_ARGS=()

if [[ ! -f "${ROOT_DIR}/docker/mojo-kernelspec/kernel.json" ]]; then
  cat >&2 <<'EOF'
[warning] Mojo kernelspec not found at docker/mojo-kernelspec/kernel.json.
          bridgeit.install_lang("mojo") will fall back to the pixi environment.
EOF
else
  echo "Mojo kernelspec found in docker/mojo-kernelspec/" >&2
fi

if [[ -n "${EXTRA_DOCKER_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  RUN_ARGS+=( ${EXTRA_DOCKER_ARGS} )
fi

echo "Executing notebooks inside ${IMAGE_NAME} ..."
CMD=(docker run --rm)
CMD+=( "${RUN_MOUNTS[@]}" )
CMD+=( "${RUN_ENVS[@]}" )
if (( ${#RUN_ARGS[@]} )); then
  CMD+=( "${RUN_ARGS[@]}" )
fi
CMD+=( "${IMAGE_NAME}" bash docker/run_integration.sh )
"${CMD[@]}"

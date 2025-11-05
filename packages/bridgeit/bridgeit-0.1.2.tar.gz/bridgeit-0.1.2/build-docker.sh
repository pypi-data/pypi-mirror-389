#!/usr/bin/env bash
# Build the BridgeIt Docker image.
#
# Optional environment variables:
#   IMAGE_NAME - Tag to use for the built image (default: bridgeit-integration)
#   BUILD_ARGS - Extra arguments passed to docker build (quoted string)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-bridgeit-integration}"

CMD=(docker build -f "${ROOT_DIR}/docker/Dockerfile" -t "${IMAGE_NAME}")

if [[ -n "${BUILD_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  CMD+=( ${BUILD_ARGS} )
fi

CMD+=( "${ROOT_DIR}" )

echo "Building ${IMAGE_NAME} from ${ROOT_DIR} ..."
"${CMD[@]}"

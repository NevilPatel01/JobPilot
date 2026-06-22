#!/usr/bin/env bash
# Download Tectonic for local PDF compilation when not installed system-wide.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT_DIR/backend/.bin"
TECTONIC="$BIN_DIR/tectonic"
TECTONIC_VERSION="${TECTONIC_VERSION:-0.16.9}"

if command -v tectonic >/dev/null 2>&1; then
  echo "Tectonic: $(command -v tectonic)"
  exit 0
fi

if [[ -x "$TECTONIC" ]]; then
  echo "Tectonic: $TECTONIC"
  exit 0
fi

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$OS-$ARCH" in
  darwin-arm64)  TECTONIC_ARCH="aarch64-apple-darwin" ;;
  darwin-x86_64) TECTONIC_ARCH="x86_64-apple-darwin" ;;
  linux-x86_64)  TECTONIC_ARCH="x86_64-unknown-linux-gnu" ;;
  linux-aarch64) TECTONIC_ARCH="aarch64-unknown-linux-musl" ;;
  *)
    echo "Error: No bundled Tectonic binary for $OS/$ARCH." >&2
    echo "Install manually: https://tectonic-typesetting.github.io/" >&2
    exit 1
    ;;
esac

URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-${TECTONIC_ARCH}.tar.gz"

mkdir -p "$BIN_DIR"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading Tectonic ${TECTONIC_VERSION} (${TECTONIC_ARCH})..."
curl -fsSL -o "$TMP/tectonic.tar.gz" "$URL"
tar -xzf "$TMP/tectonic.tar.gz" -C "$BIN_DIR" tectonic
chmod +x "$TECTONIC"
echo "Tectonic installed: $TECTONIC"

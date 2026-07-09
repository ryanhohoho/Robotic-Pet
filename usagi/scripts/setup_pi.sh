#!/usr/bin/env bash
# one-shot setup for a fresh Raspberry Pi OS (Bookworm) install.
# enables interfaces, installs system libs, builds the venv, installs deps.
# run from the repo root:  bash scripts/setup_pi.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "==> usagi setup, repo at $REPO_DIR"

# system packages: picamera2/opencv/portaudio are best from apt on the pi
echo "==> installing system packages (sudo)"
sudo apt-get update
sudo apt-get install -y \
  python3-venv python3-picamera2 python3-opencv libportaudio2 python3-smbus i2c-tools

# enable i2c and camera non-interactively
echo "==> enabling I2C + camera"
sudo raspi-config nonint do_i2c 0 || true
sudo raspi-config nonint do_camera 0 || true

# venv with system site packages so picamera2 (apt) is visible
if [ ! -d .venv ]; then
  echo "==> creating venv (.venv, --system-site-packages)"
  python3 -m venv --system-site-packages .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "==> installing python deps"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> validating config"
python -c "from usagi import config; config.validate(config.load()); print('config OK')"

echo
echo "setup done. next steps:"
echo "  source .venv/bin/activate"
echo "  python scripts/selftest.py        # verify hardware"
echo "  python -m usagi.sim               # or dry-run the behavior"
echo "  python -m usagi.main              # run for real"
echo
echo "to autostart on boot, install the service:"
echo "  sudo cp scripts/usagi.service /etc/systemd/system/"
echo "  sudo systemctl enable --now usagi"

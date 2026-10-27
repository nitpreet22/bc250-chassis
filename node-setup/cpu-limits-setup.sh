#!/usr/bin/env bash
# Lets a BC-250 node cap its CPU clock and lower the SMU's CPU temperature
# limit, so it can hold full load around the clock. Also caps the GPU at 1500 MHz.
#
# Run on the node from your admin account, with bc250-cpu-limits next to it:
#     sudo bash cpu-limits-setup.sh
# Safe to re-run. Installs:
#   /opt/bc250-smu                         the bc250_smu library (pinned commit below)
#   /usr/local/sbin/bc250-cpu-limits       set / apply / show the limits
#   /etc/bc250-cpu-limits.conf             the limits; starts at stock (3500 MHz, 100 °C)
#   bc250-cpu-limits.service               applies the config at boot, before the GPU governor
#   /etc/sudoers.d/50-bc250-cpu-limits     lets you run the helper without a password
#                                          (it only accepts limits at or below stock).
#                                          Delete this file once the limits are tuned.
set -euo pipefail

# github.com/bc250-collective/bc250_smu_oc (MIT), main as of 2026-09-27.
readonly SMU_LIBRARY_COMMIT=327014d6515d7108b1144adfa7203b4cc2eefd0b
readonly SMU_LIBRARY_URL=https://github.com/bc250-collective/bc250_smu_oc/archive/$SMU_LIBRARY_COMMIT.tar.gz
readonly SMU_VENV=/opt/bc250-smu
readonly HELPER_SOURCE="$(dirname "$0")/bc250-cpu-limits"
readonly HELPER=/usr/local/sbin/bc250-cpu-limits
readonly LIMITS_CONFIG=/etc/bc250-cpu-limits.conf
readonly GPU_GOVERNOR_CONFIG=/etc/cyan-skillfish-governor-smu/config.toml
readonly GPU_MAX_MHZ=1500

step() { printf '\n==> %s\n' "$*"; }

require_sudo_from_user_account() {
  if [[ $EUID -ne 0 || -z ${SUDO_USER:-} ]]; then
    echo "Run this with sudo from your normal user account: sudo bash $0" >&2
    exit 1
  fi
}

require_sudo_from_user_account
if [[ ! -f $HELPER_SOURCE ]]; then
  echo "Missing $HELPER_SOURCE (copy it next to this script)" >&2
  exit 1
fi

step "Installing the bc250_smu library into $SMU_VENV"
python3 -m venv "$SMU_VENV"
"$SMU_VENV/bin/pip" install --quiet --upgrade "$SMU_LIBRARY_URL"

step "Installing $HELPER"
install -m 0755 "$HELPER_SOURCE" "$HELPER"
if [[ ! -f $LIMITS_CONFIG ]]; then
  cat > "$LIMITS_CONFIG" <<'EOF'
# Written by bc250-cpu-limits; applied at boot by bc250-cpu-limits.service.
[cpu]
max_clock_mhz = 3500
max_temp_c = 100
EOF
fi

step "Applying the limits at every boot"
# The GPU governor talks to the SMU through the same registers, so this runs first.
cat > /etc/systemd/system/bc250-cpu-limits.service <<EOF
[Unit]
Description=BC-250 CPU clock cap and SMU temperature limit
Before=cyan-skillfish-governor-smu.service

[Service]
Type=oneshot
ExecStart=$HELPER apply

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable bc250-cpu-limits.service

step "Letting $SUDO_USER run bc250-cpu-limits without a password"
sudoers_file=/etc/sudoers.d/50-bc250-cpu-limits
echo "$SUDO_USER ALL=(root) NOPASSWD: $HELPER" > "$sudoers_file.new"
chmod 0440 "$sudoers_file.new"
visudo -cqf "$sudoers_file.new"
mv "$sudoers_file.new" "$sudoers_file"

step "Capping the GPU at $GPU_MAX_MHZ MHz (BUILD.md: raise it only after measuring)"
sed -i "/^\[frequency-range\]/,/^\[/ s/^max *= *[0-9]\+/max = $GPU_MAX_MHZ/" "$GPU_GOVERNOR_CONFIG"
grep -A3 '^\[frequency-range\]' "$GPU_GOVERNOR_CONFIG"
systemctl restart cyan-skillfish-governor-smu.service

step "Done. Check it with: bc250-cpu-limits show"

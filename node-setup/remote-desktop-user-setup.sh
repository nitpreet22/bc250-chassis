#!/usr/bin/env bash
# Per-user half of the remote desktop: Sunshine's settings and service, and
# Plasma settings that keep the virtual monitor streamable.
#
# Run on the node as the desktop user (no sudo), after remote-desktop-setup.sh:
#     bash remote-desktop-user-setup.sh
# Safe to re-run.
set -euo pipefail

readonly SUNSHINE_UNIT=app-dev.lizardbyte.app.Sunshine.service
readonly SUNSHINE_CONF=~/.config/sunshine/sunshine.conf

step() { printf '\n==> %s\n' "$*"; }

step "Configuring Sunshine: CPU encoding (no hardware encoder on the BC-250), KMS capture"
mkdir -p "$(dirname "$SUNSHINE_CONF")"
touch "$SUNSHINE_CONF"
set_sunshine_option() {
  local key=$1 value=$2
  if grep -q "^$key *=" "$SUNSHINE_CONF"; then
    sed -i "s|^$key *=.*|$key = $value|" "$SUNSHINE_CONF"
  else
    echo "$key = $value" >> "$SUNSHINE_CONF"
  fi
}
set_sunshine_option encoder software
set_sunshine_option capture kms

step "Allowing the web UI at this node's own LAN addresses (otherwise its CSRF check blocks logins)"
# Sunshine only trusts https://localhost-style origins by default, but the web UI is
# opened from another PC as https://<node IP>:47990. Re-run this script if the IP changes.
readonly WEB_UI_PORT=47990
web_ui_origins="https://$(hostname):$WEB_UI_PORT"
for ipv4 in $(hostname -I | tr ' ' '\n' | grep -E '^[0-9.]+$'); do
  web_ui_origins+=",https://$ipv4:$WEB_UI_PORT"
done
set_sunshine_option csrf_allowed_origins "$web_ui_origins"
# Pick up the new settings if Sunshine is already running.
systemctl --user try-restart "$SUNSHINE_UNIT"

step "Starting Sunshine with every Plasma session"
systemctl --user enable "$SUNSHINE_UNIT"

step "Keeping the virtual monitor on (a monitor in power-save stops the stream)"
kwriteconfig6 --file powerdevilrc --group AC --group Display --key DimDisplayWhenIdle false
kwriteconfig6 --file powerdevilrc --group AC --group Display --key TurnOffDisplayWhenIdle false
kwriteconfig6 --file powerdevilrc --group AC --group SuspendAndShutdown --key AutoSuspendAction 0

step "Turning off KWin overlays, which make windows flicker in KMS capture (Sunshine docs)"
mkdir -p ~/.config/plasma-workspace/env
echo 'export KWIN_USE_OVERLAYS=0' > ~/.config/plasma-workspace/env/sunshine-kms.sh

step "Done. Start the desktop with: desktop-on"

#!/usr/bin/env bash
# Adds an on-demand remote desktop to a BC-250 node: KDE Plasma on a virtual
# 1080p monitor, streamed by Sunshine to a Moonlight client.
#
# Run on the node from your admin account, with bc250-1080p.bin next to it:
#     sudo bash remote-desktop-setup.sh
# Then reboot. Safe to re-run: each step checks the current state or is idempotent.
#
# Afterwards the node still boots to text mode. The desktop only runs between
# `desktop-on` and `desktop-off` (no sudo needed), so it holds no memory during
# compute jobs. The BC-250 has no hardware video encoder, so Sunshine encodes
# on the CPU (x264).
set -euo pipefail

readonly SUNSHINE_COPR=lizardbyte/stable
readonly EDID_NAME=bc250-1080p.bin
readonly EDID_SOURCE="$(dirname "$0")/$EDID_NAME"
readonly EDID_INSTALLED=/usr/lib/firmware/edid/$EDID_NAME
# The nodes have two DisplayPorts and nothing plugged in; the virtual monitor goes on DP-1.
readonly VIRTUAL_CONNECTOR=DP-1
readonly PLASMA_SESSION=/usr/share/wayland-sessions/plasma.desktop

step() { printf '\n==> %s\n' "$*"; }

require_sudo_from_user_account() {
  if [[ $EUID -ne 0 || -z ${SUDO_USER:-} ]]; then
    echo "Run this with sudo from your normal user account: sudo bash $0" >&2
    exit 1
  fi
}

require_sudo_from_user_account
if [[ ! -f $EDID_SOURCE ]]; then
  echo "Missing $EDID_SOURCE (make it with: python make_edid.py $EDID_NAME)" >&2
  exit 1
fi

step "Installing KDE Plasma, SDDM and Sunshine"
dnf copr enable -y "$SUNSHINE_COPR"
dnf install -y sddm plasma-workspace plasma-desktop kwin kscreen powerdevil \
  xdg-desktop-portal-kde konsole dolphin pipewire-pulseaudio wireplumber Sunshine
if [[ ! -f $PLASMA_SESSION ]]; then
  echo "Expected the Plasma Wayland session at $PLASMA_SESSION; check the plasma-workspace package." >&2
  exit 1
fi

step "Installing the virtual monitor's EDID (also into the initramfs, in case amdgpu loads early)"
install -D -m 0644 "$EDID_SOURCE" "$EDID_INSTALLED"
echo "install_items+=\" $EDID_INSTALLED \"" > /etc/dracut.conf.d/bc250-virtual-monitor.conf
dracut -f

step "Setting kernel arguments for the virtual monitor on $VIRTUAL_CONNECTOR"
# edid_firmware supplies the monitor's description; ':e' forces the empty port on.
grubby --update-kernel=ALL --args="drm.edid_firmware=$VIRTUAL_CONNECTOR:edid/$EDID_NAME video=$VIRTUAL_CONNECTOR:e"

step "Keeping text-mode boot; the desktop starts only on demand"
systemctl set-default multi-user.target
systemctl disable sddm.service 2>/dev/null || true
# A cluster node must never go to sleep, and Plasma's power manager would otherwise suspend it when idle.
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

step "Logging $SUDO_USER straight into Plasma when SDDM starts"
mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/50-bc250-autologin.conf <<EOF
[Autologin]
User=$SUDO_USER
Session=$(basename "$PLASMA_SESSION")
EOF

step "Letting $SUDO_USER start and stop SDDM without a password"
cat > /etc/polkit-1/rules.d/50-bc250-desktop.rules <<EOF
// Lets $SUDO_USER run desktop-on / desktop-off: start, stop or restart sddm.service only.
polkit.addRule(function (action, subject) {
  if (action.id === "org.freedesktop.systemd1.manage-units" &&
      action.lookup("unit") === "sddm.service" &&
      ["start", "stop", "restart"].indexOf(action.lookup("verb")) !== -1 &&
      subject.user === "$SUDO_USER") {
    return polkit.Result.YES;
  }
});
EOF

step "Installing the desktop-on and desktop-off commands"
cat > /usr/local/bin/desktop-on <<'EOF'
#!/usr/bin/env bash
# Starts Plasma on the virtual monitor and waits for Sunshine to accept Moonlight connections.
set -euo pipefail
readonly SUNSHINE_HTTP_PORT=47989

systemctl start sddm.service
for _ in $(seq 60); do
  if ss -ltnH "sport = :$SUNSHINE_HTTP_PORT" | grep -q .; then
    echo "Desktop is up on $(hostname). Connect with Moonlight."
    exit 0
  fi
  sleep 1
done
echo "Sunshine did not start within 60 s. Check: journalctl --user -u app-dev.lizardbyte.app.Sunshine -b" >&2
exit 1
EOF
cat > /usr/local/bin/desktop-off <<'EOF'
#!/usr/bin/env bash
# Ends the Plasma session and Sunshine, and stops SDDM, so the desktop frees its memory.
set -euo pipefail

# Sunshine's unit is only "wanted" by the session, so it outlives it unless stopped.
systemctl --user stop app-dev.lizardbyte.app.Sunshine.service 2>/dev/null || true
# Plasma 6 runs KWin, plasmashell and the portals as systemd user services that are
# PartOf graphical-session.target. Ending the login session alone leaves them
# running (an ssh login keeps the user manager alive), and the next desktop-on stalls.
systemctl --user stop graphical-session.target
for session in $(loginctl list-sessions --no-legend | awk -v user="$USER" '$3 == user {print $1}'); do
  if [[ $(loginctl show-session "$session" -p Type --value) == wayland ]]; then
    loginctl terminate-session "$session"
  fi
done
systemctl stop sddm.service
echo "Desktop is off on $(hostname)."
EOF
chmod 0755 /usr/local/bin/desktop-on /usr/local/bin/desktop-off

step "Opening Sunshine's ports in the firewall"
# From Sunshine's source (base port 47989): HTTPS -5, HTTP 0, web UI +1, RTSP +21 (TCP);
# video +9, control +10, audio +11 (UDP).
if ! firewall-cmd --permanent --get-services | tr ' ' '\n' | grep -qx sunshine; then
  firewall-cmd --permanent --new-service=sunshine
  firewall-cmd --permanent --service=sunshine --set-description="Sunshine game streaming (Moonlight host)"
  for port in 47984/tcp 47989/tcp 47990/tcp 48010/tcp 47998/udp 47999/udp 48000/udp; do
    firewall-cmd --permanent --service=sunshine --add-port="$port"
  done
fi
firewall-cmd --permanent --add-service=sunshine
firewall-cmd --reload

step "Adding $SUDO_USER to the input group (Sunshine's virtual mouse and keyboard)"
usermod -aG input "$SUDO_USER"

step "Done. Reboot now so the virtual monitor appears: sudo reboot"

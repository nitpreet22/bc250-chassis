#!/usr/bin/env bash
# Prepares a fresh Fedora Server 44 install on an AMD BC-250 for headless Vulkan compute.
#
# Run on the node from your admin account:  sudo bash bc250-fedora-setup.sh
# Then reboot. Safe to re-run: each step checks the current state or is idempotent.
#
# Assumes the modded P3.00 BIOS with UMA Frame Buffer Size = 512 MB, so model memory
# reaches the GPU through GTT (shared system RAM) rather than a fixed VRAM carve-out.
set -euo pipefail

# Let the GPU map up to 11.5 GiB of the shared 16 GB GDDR6 (3014656 pages x 4 KiB).
# This leaves roughly 2.5 GiB for Fedora itself; raise it only after checking free RAM under load.
readonly TTM_PAGES=3014656
readonly GOVERNOR_COPR=filippor/bazzite
readonly GOVERNOR_PACKAGE=cyan-skillfish-governor-smu
# The installer defaulted to America/New_York; the nodes live in Melbourne.
readonly TIME_ZONE=Australia/Melbourne

step() { printf '\n==> %s\n' "$*"; }

require_sudo_from_user_account() {
  if [[ $EUID -ne 0 || -z ${SUDO_USER:-} ]]; then
    echo "Run this with sudo from your normal user account: sudo bash $0" >&2
    exit 1
  fi
}

grow_root_filesystem() {
  # Fedora Server's installer caps the root LV at 15 GB and leaves the rest of the SSD unallocated.
  local root_source vg_name vg_free_bytes
  root_source=$(findmnt -no SOURCE /)
  vg_name=$(lvs --noheadings -o vg_name "$root_source" | xargs)
  vg_free_bytes=$(vgs --noheadings --units b --nosuffix -o vg_free "$vg_name" | xargs)
  if (( vg_free_bytes > 1024 ** 3 )); then
    lvextend --resizefs -l +100%FREE "$root_source"
  else
    echo "Root filesystem already fills the volume group."
  fi
}

warn_if_kernel_is_known_bad() {
  # 6.15.0-6.15.6 and 6.17.8-6.17.10 break the BC-250 GPU driver (amd-bc250-docs).
  local default_kernel version major minor patch
  default_kernel=$(grubby --default-kernel)
  version=${default_kernel#/boot/vmlinuz-}
  IFS='.-' read -r major minor patch _ <<<"$version"
  if [[ "$major.$minor" == 6.15 && $patch -le 6 ]] ||
     [[ "$major.$minor" == 6.17 && $patch -ge 8 && $patch -le 10 ]]; then
    echo "WARNING: default kernel $version is in a range known to break the BC-250 GPU." >&2
  else
    echo "Default kernel $version is not in a known-bad range."
  fi
}

require_sudo_from_user_account

step "Setting the time zone to $TIME_ZONE (the clock itself stays synced by chronyd)"
timedatectl set-timezone "$TIME_ZONE"

step "Updating the system"
dnf upgrade --refresh -y

step "Growing the root filesystem to fill the SSD"
grow_root_filesystem

step "Installing the Vulkan driver, tools and llama.cpp build dependencies"
# dnf5-plugins provides 'dnf copr', used in the next step.
dnf install -y mesa-vulkan-drivers vulkan-tools lm_sensors dnf5-plugins \
  git cmake gcc-c++ glslc vulkan-headers vulkan-loader-devel libcurl-devel

step "Installing the GPU clock governor (otherwise the GPU stays at 1500 MHz)"
dnf copr enable -y "$GOVERNOR_COPR"
dnf install -y "$GOVERNOR_PACKAGE"
systemctl enable --now "$GOVERNOR_PACKAGE"

step "Enabling the Nuvoton temperature sensor driver"
echo nct6683 > /etc/modules-load.d/99-bc250-sensors.conf
echo 'options nct6683 force=true' > /etc/modprobe.d/99-bc250-sensors.conf
modprobe nct6683 force=true || echo "nct6683 did not load now; it will be retried at boot."

step "Giving $SUDO_USER access to the GPU (takes effect at next login)"
usermod -aG render,video "$SUDO_USER"

step "Setting kernel arguments for GPU memory"
grubby --update-kernel=ALL --args="ttm.pages_limit=$TTM_PAGES ttm.page_pool_size=$TTM_PAGES"
grubby --update-kernel=ALL --remove-args="nomodeset"

step "Checking the kernel version"
warn_if_kernel_is_known_bad

step "Done. Reboot now: sudo reboot"

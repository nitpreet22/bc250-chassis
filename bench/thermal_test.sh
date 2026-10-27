#!/usr/bin/env bash
# thermal_test.sh: idle baseline, then full CPU + GPU load, then cooldown,
# logging the board's sensors every few seconds. Runs on one BC-250 node.
#
# Usage:   ./thermal_test.sh [load_s=900] [idle_s=60] [cooldown_s=180]
# Output:  ~/bench/results/<host>-<timestamp>/
#            sensors.csv  one row per sample (see header)
#            gflops.txt   "<unix time> <GFLOPS>" from gpu_burn every ~5 s
#            cpu_gflops.txt  the same from cpu_burn
#            limits.txt   the CPU and GPU limits in force for the run
#            status.txt   RUNNING, then DONE or ABORTED: <reason>
#          Set RUN_LABEL to add a suffix to the directory name.
# Safety:  if GPU edge or CPU Tctl reaches ABORT_AT_C, both loads are killed
#          at once and the run carries on logging the cooldown.
#
# Start it detached so a dropped ssh session can't strand a node at full load:
#   nohup setsid ~/bench/thermal_test.sh >/dev/null 2>&1 &

set -euo pipefail

LOAD_S=${1:-900}
IDLE_S=${2:-60}
COOLDOWN_S=${3:-180}
# Tctl can climb 10 °C in a few seconds at full load, so sample often.
SAMPLE_S=2
ABORT_AT_C=90

BENCH_DIR=$(cd "$(dirname "$0")" && pwd)
RUN_DIR=~/bench/results/$(hostname)-$(date +%Y%m%d-%H%M%S)${RUN_LABEL:+-$RUN_LABEL}
mkdir -p "$RUN_DIR"
echo RUNNING > "$RUN_DIR/status.txt"

# Record what the node was limited to (both files are written by node-setup/ scripts).
{
    cat /etc/bc250-cpu-limits.conf 2>/dev/null || echo "no CPU limits installed (stock: 3500 MHz, 100 °C)"
    grep -A2 '^\[frequency-range\]' /etc/cyan-skillfish-governor-smu/config.toml
} > "$RUN_DIR/limits.txt"

# Build the load generators on this node (no-op when already built).
cd "$BENCH_DIR"
[ gpu_burn -nt gpu_burn.c ] || gcc -O2 -o gpu_burn gpu_burn.c -lvulkan
[ gpu_burn.spv -nt gpu_burn.comp ] || glslc -O gpu_burn.comp -o gpu_burn.spv
[ cpu_burn -nt cpu_burn.c ] || gcc -O2 -mavx2 -mfma -pthread -o cpu_burn cpu_burn.c

# hwmon numbers differ between boots and boards, so find each chip by name.
hwmon_dir() {
    for dir in /sys/class/hwmon/hwmon*; do
        if [ "$(cat "$dir/name")" = "$1" ]; then echo "$dir"; return; fi
    done
    echo "thermal_test: no hwmon chip named $1" >&2
    exit 1
}
GPU=$(hwmon_dir amdgpu)
CPU=$(hwmon_dir k10temp)
BOARD=$(hwmon_dir nct6686)
NVME=$(hwmon_dir nvme)

milli_to_c()   { echo $(( $(cat "$1") / 1000 )); }
micro_to_w()   { echo $(( $(cat "$1") / 1000000 )); }
hz_to_mhz()    { echo $(( $(cat "$1") / 1000000 )); }
# Average current clock over all threads (measured by the kernel; there's no cpufreq driver).
cpu_mhz_avg()  { awk '/^cpu MHz/ { sum += $4; count++ } END { printf "%d", sum / count }' /proc/cpuinfo; }

# nct6686 sensors: temp1 = AMD TSI (APU, read over SMBus), temp2/temp3 = board thermistors,
# fan2 = the board's fan header (the hub reports one fan's speed), pwm2 = the duty the board
# drives that header at (0-255; the nct6683 driver can read it but not set it).
echo "unix_time,phase,gpu_edge_c,cpu_tctl_c,apu_tsi_c,board_therm1_c,board_therm2_c,nvme_c,gpu_ppt_w,gpu_sclk_mhz,cpu_mhz_avg,fan2_rpm,fan2_pwm" \
    > "$RUN_DIR/sensors.csv"

GPU_PID=""
CPU_PID=""
stop_loads() {
    [ -n "$GPU_PID" ] && kill "$GPU_PID" 2>/dev/null || true
    [ -n "$CPU_PID" ] && kill "$CPU_PID" 2>/dev/null || true
}
trap stop_loads EXIT

# Logs samples for $2 seconds under phase name $1. During the load phase it
# also enforces the temperature limit.
log_phase() {
    local phase=$1 seconds=$2
    local end=$(( $(date +%s) + seconds ))
    while [ "$(date +%s)" -lt "$end" ]; do
        local edge tctl
        edge=$(milli_to_c "$GPU/temp1_input")
        tctl=$(milli_to_c "$CPU/temp1_input")
        echo "$(date +%s),$phase,$edge,$tctl,$(milli_to_c "$BOARD/temp1_input"),$(milli_to_c "$BOARD/temp2_input"),$(milli_to_c "$BOARD/temp3_input"),$(milli_to_c "$NVME/temp1_input"),$(micro_to_w "$GPU/power1_average"),$(hz_to_mhz "$GPU/freq1_input"),$(cpu_mhz_avg),$(cat "$BOARD/fan2_input"),$(cat "$BOARD/pwm2")" \
            >> "$RUN_DIR/sensors.csv"

        if [ "$phase" = load ] && { [ "$edge" -ge "$ABORT_AT_C" ] || [ "$tctl" -ge "$ABORT_AT_C" ]; }; then
            stop_loads
            echo "ABORTED: edge ${edge} C, Tctl ${tctl} C at $(date +%T) (limit ${ABORT_AT_C} C)" > "$RUN_DIR/status.txt"
            return 1
        fi
        sleep "$SAMPLE_S"
    done
}

log_phase idle "$IDLE_S"

./gpu_burn "$LOAD_S" gpu_burn.spv > "$RUN_DIR/gflops.txt" 2> "$RUN_DIR/gpu_burn.err" &
GPU_PID=$!
./cpu_burn "$LOAD_S" > "$RUN_DIR/cpu_gflops.txt" &
CPU_PID=$!

if log_phase load "$LOAD_S"; then
    echo DONE > "$RUN_DIR/status.txt"
fi
stop_loads
wait 2>/dev/null || true

log_phase cooldown "$COOLDOWN_S"

#!/usr/bin/env bash
# summarize_runs.sh: one line per thermal_test.sh run, for comparing settings.
#
# Usage:  ./summarize_runs.sh ~/bench/results/<run dir>...
# Columns (load phase only):
#   peak    hottest Tctl / GPU edge seen
#   last60  averages over the final 60 s of load (close to steady state)
#   CPU and GPU GFLOPS averaged over the whole load phase

set -euo pipefail

printf '%-34s %-9s %5s %5s | %-6s %5s %5s %5s %6s %6s | %7s %7s\n' \
    run status peakC edgeC last60 tctl edge ppt_w cpuMHz gpuMHz cpuGF gpuGF
for run in "$@"; do
    status=$(cut -d: -f1 "$run/status.txt")
    # sensors.csv columns: 1 time, 2 phase, 3 edge, 4 tctl, 9 ppt, 10 sclk, 11 cpu MHz
    awk -F, -v run="$(basename "$run")" -v status="$status" '
        $2 == "load" { rows[++n] = $0; t[n] = $1; if ($4 > peak) peak = $4; if ($3 > edge_peak) edge_peak = $3 }
        END {
            last = 0; cutoff = t[n] - 60
            for (i = 1; i <= n; i++) {
                if (t[i] < cutoff) continue
                split(rows[i], f, ","); last++
                tctl += f[4]; edge += f[3]; ppt += f[9]; sclk += f[10]; mhz += f[11]
            }
            printf "%-34s %-9s %5d %5d | %-6s %5.1f %5.1f %5.0f %6.0f %6.0f | ", run, status, peak, edge_peak, "", tctl / last, edge / last, ppt / last, mhz / last, sclk / last
        }' "$run/sensors.csv"
    # Runs from before cpu_burn reported throughput have no cpu_gflops.txt.
    average_gflops() {
        if [ -f "$1" ]; then
            awk '{ sum += $2; n++ } END { if (n) printf "%7.0f", sum / n; else printf "%7s", "-" }' "$1"
        else
            printf '%7s' -
        fi
    }
    printf '%s %s\n' "$(average_gflops "$run/cpu_gflops.txt")" "$(average_gflops "$run/gflops.txt")"
done

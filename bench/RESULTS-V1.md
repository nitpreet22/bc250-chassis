# Thermal results: Version 1 case (stock heatsinks)

Measured 2026-10-25 to 2026-10-27 on the three nodes in the V1 case: stock uncut heatsinks, and per
node a Teucer AF-12025 and an Arctic P12 Silent on the fins plus a BB7515 blower on the backplate
(see `BUILD.md`, Version 1). Version 2 (AIO water cooling) will be measured the same way and compared
against these numbers.

**Outcome:** with these caps, all three nodes hold a worst-case 100 % CPU + GPU load for 30 minutes
below 80 °C, with the fans on the BIOS's quiet default curve. The cap (not the chip's emergency
throttle) sets the clock:

| Node | CPU cap | GPU cap | Tctl, last 5 min of 30 | Peak | CPU GFLOPS | GPU GFLOPS |
|---|---|---|---|---|---|---|
| 1 | 3000 MHz | 1500 MHz | 71 °C | 72 °C | 208 | 3875 |
| 2 | 2300 MHz | 1500 MHz | 78 °C | 79 °C | 159 | 3867 |
| 3 | 2800 MHz | 1500 MHz | 75 °C | 75 °C | 194 | 3871 |

These are the caps in force from 2026-10-27 ([run 5](#5-final-caps-30-minute-confirm-run-2026-10-27)).
Lower clocks were chosen over the BIOS's Full Speed fan mode to keep the case quiet. The SMU's own
CPU limit stays at 85 °C on every node as a safety net.

## Method

- **Load:** `thermal_test.sh` runs `cpu_burn` (AVX2 FMAs on all 12 threads, the hottest common Zen 2
  instruction mix) and `gpu_burn` (Vulkan compute) together, after an idle baseline and before a
  cooldown. It samples every 2 s and kills the load if Tctl or GPU edge reaches 90 °C.
- **All three nodes load at the same time**, so the shared case air heats up as it would in use.
- **This is a worst case.** The nodes are meant for 24/7 agent sandboxes plus background services,
  which load the CPU in bursts and the GPU lightly. Real temperatures should sit lower.
- **Room temperature was not logged.** Board thermistors read 32–36 °C at idle. Log the room
  temperature for the V2 runs so the two sets can be compared fairly.

## How the limits are set

- **GPU:** the clock governor's `[frequency-range]` max is 1500 MHz
  (`/etc/cyan-skillfish-governor-smu/config.toml`).
- **CPU:** the BC-250's BIOS has no ACPI frequency tables, so Linux has no cpufreq driver and
  `cpupower`/`tuned` can't cap it. `node-setup/cpu-limits-setup.sh` installs `bc250-cpu-limits`,
  which sends the cap to the SMU directly (max boost clock, and the CPU temperature at which the SMU
  throttles). A systemd unit reapplies `/etc/bc250-cpu-limits.conf` at every boot; this was confirmed
  after a full power cycle.

```bash
sudo bc250-cpu-limits set 3000 85   # max CPU clock (MHz), SMU throttle temperature (°C)
bc250-cpu-limits show
```

## Results

### 1. No caps (2026-10-25): aborted within a minute

Stock CPU (3500 MHz) and the GPU governor up to 2000 MHz (1850 MHz reached):

| Node | Aborted after | At |
|---|---|---|
| 1 | 31 s | Tctl 90 °C |
| 2 | 5 s | Tctl 96 °C |
| 3 | 51 s | Tctl 90 °C |

### 2. CPU cap sweep, 5 min each (2026-10-26), GPU at 1500 MHz

Average over the last 60 s of load. "SMU" means the SMU's 85 °C limit was throttling the CPU below
its cap.

| CPU cap | Node 1 Tctl / edge / CPU MHz | Node 2 | Node 3 | CPU GFLOPS (per node) |
|---|---|---|---|---|
| 3500 | 85 / 66 / 3352 SMU | 85 / 80 / 2782 SMU | 85 / 73 / 3228 SMU | 205–236 |
| 3000 | 69 / 60 / 2993 | 85 / 80 / 2778 SMU | 77 / 71 / 2993 | 200–208 |
| 2500 | 60 / 59 / 2494 | 78 / 78 / 2495 | 69 / 69 / 2494 | 173 |

GPU throughput was the same at every step (about 3870 GFLOPS), and power was 80–102 W per node.

### 3. Node 2 runs hot

Node 2 was the hottest node on every sensor, idle and loaded, at the same power draw. The giveaway is
how fast it heats: its GPU edge rises 17 °C in the first 3 s of load against 10–11 °C on the others,
and the SMU throttles it within 3 s while Tctl still reads 72 °C. A jump that fast points to the
die-to-heatsink interface rather than airflow.

On 2026-10-27 node 2 was repasted, and the case fans were rewired so each node's fans plug into the
hub that belongs to that node (they had been mixed between hubs). Afterwards every board reports a
fan speed on the nct6686's `fan2`; node 1 had read 0 before. The 5-minute stock-clock test, repeated
with all three loaded together:

| | Node 2 before | Node 2 after | Nodes 1 / 3 after |
|---|---|---|---|
| Sustained CPU clock (SMU-throttled) | 2782 MHz | 2949 MHz | 3366 / 3246 MHz |
| GPU edge, last 60 s | 79.7 °C | 77.9 °C | 66.5 / 72.6 °C |
| GPU edge rise at the first load sample (2–3 s) | +17 °C | +19 °C | +10 / +8 °C |

A small gain, but the fast rise is unchanged, so the old paste was not the main cause.

### 4. 30-minute confirm run (2026-10-27)

Caps 3000 / 2500 / 3000 MHz, SMU limit 85 °C, GPU 1500 MHz. Tctl / GPU edge averaged per 5 minutes:

| Minutes | Node 1 | Node 2 | Node 3 |
|---|---|---|---|
| 0–5 | 69.2 / 60.5 | 73.0 / 73.1 | 72.8 / 66.8 |
| 5–10 | 70.7 / 61.6 | 78.3 / 78.1 | 78.3 / 71.9 |
| 10–15 | 71.0 / 61.9 | 79.2 / 79.1 | 79.0 / 72.7 |
| 15–20 | 71.0 / 62.0 | 80.0 / 79.6 | 79.0 / 73.1 |
| 20–25 | 71.9 / 63.2 | 80.8 / 80.7 | 79.9 / 73.4 |
| 25–30 | 71.2 / 62.6 | 80.3 / 80.2 | 80.0 / 73.5 |
| Peak Tctl | 72 | 81 | 80 |

Every node held its cap for the whole run; the SMU limit never engaged. Node 1 is flat. Node 2
levels off after about 20 minutes. Node 3 is still creeping up by about 1 °C per 15 minutes.

That left no margin on nodes 2 and 3 for a hotter room, so their caps came down 200 MHz each.

### 5. Final caps: 30-minute confirm run (2026-10-27)

Caps 3000 / 2300 / 2800 MHz, everything else as run 4. Tctl / GPU edge, and the fan duty the BIOS
chose (0–255), averaged per 5 minutes:

| Minutes | Node 1 | Node 2 | Node 3 |
|---|---|---|---|
| 0–5 | 68.6 / 59.9, duty 193 | 72.0 / 72.1, duty 204 | 68.3 / 65.8, duty 188 |
| 5–10 | 70.6 / 62.0, duty 205 | 77.6 / 77.5, duty 223 | 73.9 / 70.8, duty 213 |
| 10–15 | 71.5 / 62.9, duty 208 | 79.0 / 79.0, duty 227 | 75.0 / 71.6, duty 217 |
| 15–20 | 71.0 / 62.0, duty 207 | 79.0 / 78.3, duty 226 | 75.0 / 71.6, duty 217 |
| 20–25 | 71.0 / 62.0, duty 207 | 78.0 / 78.0, duty 224 | 75.0 / 71.4, duty 217 |
| 25–30 | 71.0 / 62.1, duty 207 | 78.0 / 78.0, duty 224 | 75.0 / 71.4, duty 217 |
| Peak Tctl | 72 | 79 | 75 |

All three are flat after 10–15 minutes. Node 3 gained 5 °C of margin for 7 % less CPU throughput.
Node 2 gained only 2 °C for 8 % less: its GPU edge now runs as hot as Tctl, so at full GPU load the
GPU, not the CPU cap, sets its temperature. A lower GPU cap on node 2 alone would be the next lever if
it ever needs more margin. The sandboxes load the GPU lightly, so in normal use it runs cooler than
this.

## Still open

- **Node 2's summer margin is 2 °C** under the worst-case load (78 °C against the 80 °C target).
  Its next lever is a lower GPU cap, since its CPU cap barely moves its temperature now.
- **Node 2's heat transfer.** Repasting didn't fix the fast rise. Remaining suspects: uneven
  spring-screw pressure, a heatsink base that isn't flat, or a fault in the heatsink itself. Swapping
  node 2's heatsink with node 1's would show whether the problem follows the heatsink.
- **Fans follow the BIOS curve, not full speed.** The hubs' inputs are on the boards' fan headers, so
  the 4-pin fans and blowers follow the BIOS's default fan curve. A 3-minute load on 2026-10-27
  (`fancheck` runs; `thermal_test.sh` now logs `fan2_rpm` and `fan2_pwm`) showed the duty at 50 %
  (127) when idle, rising with temperature to 80–85 % (204–217) by Tctl 70–75 °C. The hub's reported
  speed rose from about 2700–3100 RPM to 3700–4600 RPM. The duty during the 30-minute runs wasn't
  logged, but at 80 °C it was at least that high; run 5 logged 81–89 % (207–227). Setting the BIOS
  fan mode to **Full Speed** would add the rest: it could buy some margin instead of lower clocks,
  but lower clocks were chosen to keep the noise down. The in-kernel `nct6683` driver can only read the duty; setting it
  from Linux needs the out-of-tree `nct6687` driver.

## For Version 2

Rerun the same tests with the same commands so the numbers compare directly: the uncapped test, the
5-minute sweep at 3500 / 3000 / 2500 MHz, and the 30-minute confirm run, all three nodes together.
Log the room temperature. The aim is to raise the caps (CPU towards 3500 MHz, GPU above 1500 MHz)
while holding the same 80 °C target.

## Reproduce

On each node, from `~/bench` (copy of this folder):

```bash
sudo bc250-cpu-limits set 3000 85
RUN_LABEL=confirm30 nohup setsid ./thermal_test.sh 1800 30 180 </dev/null >/dev/null 2>&1 &
# afterwards
./summarize_runs.sh results/*-confirm30
```

Arguments: load seconds, idle seconds, cooldown seconds. Start the three nodes within a few seconds
of each other.

## Raw data

`results/v1/` holds every run quoted above, one folder per node and run
(`<host>-<date>-<time>-<label>`, node local time, which was America/New_York at the time):

| Label | Test |
|---|---|
| (none), 2026-10-25 | 1. No caps |
| `cpu3500`, `cpu3000`, `cpu2500` | 2. Sweep |
| `cpu3500post` | 3. Node 2 after the repaste |
| `confirm30` | 4. 30-minute confirm |
| `confirm30-quiet` | 5. Final caps |
| `fancheck` | 3-minute load to see whether the fans ramp ([Still open](#still-open)); node time is Melbourne from here on |

Each folder has `sensors.csv` (one row per sample: time, phase, GPU edge, Tctl, AMD TSI, two board
thermistors, NVMe, GPU power, GPU clock, average CPU clock, and from the `fancheck` runs on, fan
speed and fan duty), `gflops.txt` and `cpu_gflops.txt` (throughput every 5 s), `limits.txt` and
`status.txt`. The no-cap runs predate the CPU clock column, `cpu_gflops.txt` and `limits.txt`.

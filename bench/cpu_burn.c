// cpu_burn: keep every CPU thread busy with AVX2 FMAs (the hottest common
// instruction mix on Zen 2) for a set time.
//
// Usage:   cpu_burn <seconds>
// Output:  one line every ~5 s:  "<unix time> <GFLOPS>" (all threads together)
// Build:   gcc -O2 -mavx2 -mfma -pthread -o cpu_burn cpu_burn.c

#include <immintrin.h>
#include <pthread.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

#define REPORT_INTERVAL_S 5
#define REPS_PER_BLOCK 1000000
#define ACCUMULATORS 8
// Each rep: 8 FMAs on 8 floats, 2 flops each.
#define FLOPS_PER_BLOCK ((double)REPS_PER_BLOCK * ACCUMULATORS * 8 * 2)

static volatile sig_atomic_t stop_requested = 0;
static double deadline;
static atomic_long blocks_done = 0;

static void on_signal(int signal_number) {
    (void)signal_number;
    stop_requested = 1;
}

static double now_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static void *burn_thread(void *unused) {
    (void)unused;
    // Eight independent accumulators cover the FMA latency on both FMA pipes.
    __m256 acc[ACCUMULATORS];
    for (int i = 0; i < ACCUMULATORS; i++) acc[i] = _mm256_set1_ps((float)i * 0.1f);
    const __m256 multiplier = _mm256_set1_ps(0.999999f);
    const __m256 addend = _mm256_set1_ps(1e-6f);

    while (!stop_requested && now_seconds() < deadline) {
        for (int rep = 0; rep < REPS_PER_BLOCK; rep++) {
            for (int i = 0; i < ACCUMULATORS; i++) acc[i] = _mm256_fmadd_ps(acc[i], multiplier, addend);
        }
        atomic_fetch_add_explicit(&blocks_done, 1, memory_order_relaxed);
    }

    // Use the result so the compiler keeps the loop.
    float sink[8];
    _mm256_storeu_ps(sink, acc[0]);
    return (void *)(long)(sink[0] > 1e30f);
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s <seconds>\n", argv[0]);
        return 2;
    }
    signal(SIGTERM, on_signal);
    signal(SIGINT, on_signal);
    deadline = now_seconds() + atof(argv[1]);

    long thread_count = sysconf(_SC_NPROCESSORS_ONLN);
    pthread_t *threads = calloc(thread_count, sizeof(pthread_t));
    for (long i = 0; i < thread_count; i++) pthread_create(&threads[i], NULL, burn_thread, NULL);

    // Report throughput from the main thread while the workers run.
    long blocks_at_last_report = 0;
    double last_report = now_seconds();
    while (!stop_requested && now_seconds() < deadline) {
        sleep(REPORT_INTERVAL_S);
        long blocks = atomic_load_explicit(&blocks_done, memory_order_relaxed);
        double now = now_seconds();
        if (stop_requested || now > deadline) break;  // the workers stopped partway through this interval
        double gflops = (blocks - blocks_at_last_report) * FLOPS_PER_BLOCK / (now - last_report) / 1e9;
        printf("%ld %.0f\n", (long)time(NULL), gflops);
        fflush(stdout);
        blocks_at_last_report = blocks;
        last_report = now;
    }

    for (long i = 0; i < thread_count; i++) pthread_join(threads[i], NULL);
    free(threads);
    return 0;
}

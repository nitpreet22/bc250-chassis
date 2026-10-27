// gpu_burn: keep the BC-250 GPU at full compute load for a set time and
// report throughput, so a drop in GFLOPS shows thermal or power throttling.
//
// Usage:   gpu_burn <seconds> <shader.spv>
// Output:  one line every ~5 s:  "<unix time> <GFLOPS>"
// Exit:    0 when the time is up, 1 on any Vulkan error, 0 early on SIGTERM.
//
// Build:   gcc -O2 -o gpu_burn gpu_burn.c -lvulkan
//          glslc -O gpu_burn.comp -o gpu_burn.spv

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <vulkan/vulkan.h>

// Work per dispatch: 64k workgroups x 256 invocations x 4096 iterations
// x 4 vec4 FMAs (16 lanes x 2 flops) is ~1.1 TFLOP, about 0.1-0.2 s on this
// GPU: long enough to stay busy, short enough to stop promptly.
#define WORKGROUPS 65536u
#define LOCAL_SIZE 256u
#define ITERATIONS 4096u
#define FLOPS_PER_ITERATION 32.0  // 4 vec4 FMAs = 16 FMAs = 32 flops
#define REPORT_INTERVAL_S 5.0

static volatile sig_atomic_t stop_requested = 0;

static void on_signal(int signal_number) {
    (void)signal_number;
    stop_requested = 1;
}

static void check(VkResult result, const char *what) {
    if (result != VK_SUCCESS) {
        fprintf(stderr, "gpu_burn: %s failed (VkResult %d)\n", what, result);
        exit(1);
    }
}

static double now_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static void *read_file(const char *path, size_t *size_out) {
    FILE *file = fopen(path, "rb");
    if (!file) {
        perror(path);
        exit(1);
    }
    fseek(file, 0, SEEK_END);
    long size = ftell(file);
    fseek(file, 0, SEEK_SET);
    void *data = malloc(size);
    if (fread(data, 1, size, file) != (size_t)size) {
        fprintf(stderr, "gpu_burn: short read on %s\n", path);
        exit(1);
    }
    fclose(file);
    *size_out = size;
    return data;
}

// Picks the first discrete or integrated GPU, so the llvmpipe CPU device that
// Mesa also exposes is never chosen.
static VkPhysicalDevice pick_gpu(VkInstance instance) {
    uint32_t count = 0;
    vkEnumeratePhysicalDevices(instance, &count, NULL);
    VkPhysicalDevice devices[8];
    if (count > 8) count = 8;
    vkEnumeratePhysicalDevices(instance, &count, devices);
    for (uint32_t i = 0; i < count; i++) {
        VkPhysicalDeviceProperties props;
        vkGetPhysicalDeviceProperties(devices[i], &props);
        if (props.deviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU ||
            props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) {
            fprintf(stderr, "gpu_burn: using %s\n", props.deviceName);
            return devices[i];
        }
    }
    fprintf(stderr, "gpu_burn: no hardware GPU found\n");
    exit(1);
}

static uint32_t find_compute_queue_family(VkPhysicalDevice gpu) {
    uint32_t count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, NULL);
    VkQueueFamilyProperties families[16];
    if (count > 16) count = 16;
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, families);
    for (uint32_t i = 0; i < count; i++) {
        if (families[i].queueFlags & VK_QUEUE_COMPUTE_BIT) return i;
    }
    fprintf(stderr, "gpu_burn: no compute queue\n");
    exit(1);
}

static uint32_t find_host_visible_memory(VkPhysicalDevice gpu, uint32_t allowed_types) {
    VkPhysicalDeviceMemoryProperties memory;
    vkGetPhysicalDeviceMemoryProperties(gpu, &memory);
    for (uint32_t i = 0; i < memory.memoryTypeCount; i++) {
        if ((allowed_types & (1u << i)) &&
            (memory.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)) {
            return i;
        }
    }
    fprintf(stderr, "gpu_burn: no host-visible memory type\n");
    exit(1);
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s <seconds> <shader.spv>\n", argv[0]);
        return 2;
    }
    double duration_s = atof(argv[1]);
    signal(SIGTERM, on_signal);
    signal(SIGINT, on_signal);

    // Instance, device and queue.
    VkApplicationInfo app = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
                             .pApplicationName = "gpu_burn",
                             .apiVersion = VK_API_VERSION_1_1};
    VkInstanceCreateInfo instance_info = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                                          .pApplicationInfo = &app};
    VkInstance instance;
    check(vkCreateInstance(&instance_info, NULL, &instance), "vkCreateInstance");

    VkPhysicalDevice gpu = pick_gpu(instance);
    uint32_t queue_family = find_compute_queue_family(gpu);

    float priority = 1.0f;
    VkDeviceQueueCreateInfo queue_info = {.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
                                          .queueFamilyIndex = queue_family,
                                          .queueCount = 1,
                                          .pQueuePriorities = &priority};
    VkDeviceCreateInfo device_info = {.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
                                      .queueCreateInfoCount = 1,
                                      .pQueueCreateInfos = &queue_info};
    VkDevice device;
    check(vkCreateDevice(gpu, &device_info, NULL, &device), "vkCreateDevice");
    VkQueue queue;
    vkGetDeviceQueue(device, queue_family, 0, &queue);

    // Output buffer: one float per invocation.
    VkDeviceSize buffer_size = (VkDeviceSize)WORKGROUPS * LOCAL_SIZE * sizeof(float);
    VkBufferCreateInfo buffer_info = {.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
                                      .size = buffer_size,
                                      .usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT};
    VkBuffer buffer;
    check(vkCreateBuffer(device, &buffer_info, NULL, &buffer), "vkCreateBuffer");
    VkMemoryRequirements needs;
    vkGetBufferMemoryRequirements(device, buffer, &needs);
    VkMemoryAllocateInfo alloc_info = {.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
                                       .allocationSize = needs.size,
                                       .memoryTypeIndex = find_host_visible_memory(gpu, needs.memoryTypeBits)};
    VkDeviceMemory memory;
    check(vkAllocateMemory(device, &alloc_info, NULL, &memory), "vkAllocateMemory");
    check(vkBindBufferMemory(device, buffer, memory, 0), "vkBindBufferMemory");

    // Pipeline: one storage buffer binding plus the iteration count as a push constant.
    size_t code_size;
    void *code = read_file(argv[2], &code_size);
    VkShaderModuleCreateInfo shader_info = {.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
                                            .codeSize = code_size,
                                            .pCode = code};
    VkShaderModule shader;
    check(vkCreateShaderModule(device, &shader_info, NULL, &shader), "vkCreateShaderModule");

    VkDescriptorSetLayoutBinding binding = {.binding = 0,
                                            .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                                            .descriptorCount = 1,
                                            .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT};
    VkDescriptorSetLayoutCreateInfo set_layout_info = {.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
                                                       .bindingCount = 1,
                                                       .pBindings = &binding};
    VkDescriptorSetLayout set_layout;
    check(vkCreateDescriptorSetLayout(device, &set_layout_info, NULL, &set_layout), "vkCreateDescriptorSetLayout");

    VkPushConstantRange push_range = {.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT,
                                      .size = sizeof(uint32_t)};
    VkPipelineLayoutCreateInfo layout_info = {.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
                                              .setLayoutCount = 1,
                                              .pSetLayouts = &set_layout,
                                              .pushConstantRangeCount = 1,
                                              .pPushConstantRanges = &push_range};
    VkPipelineLayout pipeline_layout;
    check(vkCreatePipelineLayout(device, &layout_info, NULL, &pipeline_layout), "vkCreatePipelineLayout");

    VkComputePipelineCreateInfo pipeline_info = {
        .sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
        .stage = {.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                  .stage = VK_SHADER_STAGE_COMPUTE_BIT,
                  .module = shader,
                  .pName = "main"},
        .layout = pipeline_layout};
    VkPipeline pipeline;
    check(vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &pipeline_info, NULL, &pipeline),
          "vkCreateComputePipelines");

    VkDescriptorPoolSize pool_size = {.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, .descriptorCount = 1};
    VkDescriptorPoolCreateInfo pool_info = {.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
                                            .maxSets = 1,
                                            .poolSizeCount = 1,
                                            .pPoolSizes = &pool_size};
    VkDescriptorPool pool;
    check(vkCreateDescriptorPool(device, &pool_info, NULL, &pool), "vkCreateDescriptorPool");
    VkDescriptorSetAllocateInfo set_alloc = {.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
                                             .descriptorPool = pool,
                                             .descriptorSetCount = 1,
                                             .pSetLayouts = &set_layout};
    VkDescriptorSet set;
    check(vkAllocateDescriptorSets(device, &set_alloc, &set), "vkAllocateDescriptorSets");
    VkDescriptorBufferInfo buffer_ref = {.buffer = buffer, .range = VK_WHOLE_SIZE};
    VkWriteDescriptorSet write = {.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
                                  .dstSet = set,
                                  .dstBinding = 0,
                                  .descriptorCount = 1,
                                  .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                                  .pBufferInfo = &buffer_ref};
    vkUpdateDescriptorSets(device, 1, &write, 0, NULL);

    // One command buffer, recorded once and resubmitted for the whole run.
    VkCommandPoolCreateInfo command_pool_info = {.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                                                 .queueFamilyIndex = queue_family};
    VkCommandPool command_pool;
    check(vkCreateCommandPool(device, &command_pool_info, NULL, &command_pool), "vkCreateCommandPool");
    VkCommandBufferAllocateInfo command_alloc = {.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
                                                 .commandPool = command_pool,
                                                 .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                                                 .commandBufferCount = 1};
    VkCommandBuffer commands;
    check(vkAllocateCommandBuffers(device, &command_alloc, &commands), "vkAllocateCommandBuffers");

    VkCommandBufferBeginInfo begin = {.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    check(vkBeginCommandBuffer(commands, &begin), "vkBeginCommandBuffer");
    vkCmdBindPipeline(commands, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline);
    vkCmdBindDescriptorSets(commands, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline_layout, 0, 1, &set, 0, NULL);
    uint32_t iterations = ITERATIONS;
    vkCmdPushConstants(commands, pipeline_layout, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(iterations), &iterations);
    vkCmdDispatch(commands, WORKGROUPS, 1, 1);
    check(vkEndCommandBuffer(commands), "vkEndCommandBuffer");

    VkFenceCreateInfo fence_info = {.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    VkFence fence;
    check(vkCreateFence(device, &fence_info, NULL, &fence), "vkCreateFence");
    VkSubmitInfo submit = {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
                           .commandBufferCount = 1,
                           .pCommandBuffers = &commands};

    // Main loop: submit, wait, and print throughput every REPORT_INTERVAL_S.
    double flops_per_dispatch = (double)WORKGROUPS * LOCAL_SIZE * ITERATIONS * FLOPS_PER_ITERATION;
    double start = now_seconds();
    double report_start = start;
    unsigned dispatches_since_report = 0;

    while (!stop_requested && now_seconds() - start < duration_s) {
        check(vkQueueSubmit(queue, 1, &submit, fence), "vkQueueSubmit");
        check(vkWaitForFences(device, 1, &fence, VK_TRUE, UINT64_MAX), "vkWaitForFences");
        check(vkResetFences(device, 1, &fence), "vkResetFences");
        dispatches_since_report++;

        double now = now_seconds();
        if (now - report_start >= REPORT_INTERVAL_S) {
            double gflops = dispatches_since_report * flops_per_dispatch / (now - report_start) / 1e9;
            printf("%ld %.0f\n", (long)time(NULL), gflops);
            fflush(stdout);
            report_start = now;
            dispatches_since_report = 0;
        }
    }

    vkDeviceWaitIdle(device);
    vkDestroyDevice(device, NULL);
    vkDestroyInstance(instance, NULL);
    free(code);
    return 0;
}

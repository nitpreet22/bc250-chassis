"""Write the EDID for the BC-250's virtual 1920x1080 @ 60 Hz monitor.

The nodes run headless, but Sunshine needs a display to capture. The kernel
option drm.edid_firmware=DP-1:edid/bc250-1080p.bin makes the GPU treat this
EDID as a monitor plugged into DP-1 (together with video=DP-1:e, which forces
the port on with nothing attached).

Layout: a single 128-byte EDID 1.3 base block, no extension blocks. The one
detailed timing is the standard CEA-861 1080p60 mode (148.5 MHz pixel clock).

Usage:  python make_edid.py bc250-1080p.bin
"""

import sys

EDID_HEADER = bytes([0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])


def manufacturer_id(letters: str) -> bytes:
    """Pack three letters A-Z into EDID's 5-bits-per-letter big-endian code."""
    a, b, c = (ord(letter) - ord("A") + 1 for letter in letters)
    return ((a << 10) | (b << 5) | c).to_bytes(2, "big")


def detailed_timing_1080p60() -> bytes:
    """CEA-861 VIC 16: 1920x1080 progressive, 60 Hz, positive syncs."""
    pixel_clock_10khz = 14850
    h_active, h_blank, h_sync_offset, h_sync_width = 1920, 280, 88, 44
    v_active, v_blank, v_sync_offset, v_sync_width = 1080, 45, 4, 5
    width_mm, height_mm = 527, 296  # a 24-inch 16:9 panel
    digital_separate_sync_both_positive = 0x1E

    return bytes([
        pixel_clock_10khz & 0xFF, pixel_clock_10khz >> 8,
        h_active & 0xFF, h_blank & 0xFF, ((h_active >> 8) << 4) | (h_blank >> 8),
        v_active & 0xFF, v_blank & 0xFF, ((v_active >> 8) << 4) | (v_blank >> 8),
        h_sync_offset & 0xFF, h_sync_width & 0xFF,
        ((v_sync_offset & 0x0F) << 4) | (v_sync_width & 0x0F),
        ((h_sync_offset >> 8) << 6) | ((h_sync_width >> 8) << 4)
        | ((v_sync_offset >> 4) << 2) | (v_sync_width >> 4),
        width_mm & 0xFF, height_mm & 0xFF, ((width_mm >> 8) << 4) | (height_mm >> 8),
        0, 0,  # no borders
        digital_separate_sync_both_positive,
    ])


def range_limits_descriptor() -> bytes:
    """50-75 Hz vertical, 30-83 kHz horizontal, pixel clock up to 150 MHz."""
    return bytes([0, 0, 0, 0xFD, 0, 50, 75, 30, 83, 150 // 10, 0x00, 0x0A]) + b" " * 6


def name_descriptor(name: str) -> bytes:
    """Monitor name: up to 13 characters, ended by a newline and space padding."""
    text = name.encode("ascii")[:13]
    if len(text) < 13:
        text = (text + b"\n").ljust(13, b" ")
    return bytes([0, 0, 0, 0xFC, 0]) + text


def dummy_descriptor() -> bytes:
    return bytes([0, 0, 0, 0x10, 0]) + bytes(13)


def build_edid() -> bytes:
    block = bytearray()
    block += EDID_HEADER
    block += manufacturer_id("LNX")                     # the code the kernel's own test EDIDs used
    block += (1080).to_bytes(2, "little")               # product code
    block += bytes(4)                                   # serial number: none
    block += bytes([1, 2026 - 1990])                    # week 1, 2026
    block += bytes([1, 3])                              # EDID version 1.3
    block += bytes([0x80])                              # digital input
    block += bytes([52, 29])                            # image size 52 x 29 cm
    block += bytes([220 - 100])                         # gamma 2.20
    block += bytes([0x0A])                              # RGB colour; first timing is preferred
    block += bytes([0xEE, 0x91, 0xA3, 0x54, 0x4C, 0x99, 0x26, 0x0F, 0x50, 0x54])  # sRGB primaries
    block += bytes([0x21, 0x08, 0x00])                  # established: 640x480, 800x600, 1024x768 @ 60
    block += bytes([0x81, 0xC0])                        # standard timing: 1280x720 @ 60
    block += bytes([0x01, 0x01] * 7)                    # remaining standard timings unused
    block += detailed_timing_1080p60()
    block += range_limits_descriptor()
    block += name_descriptor("BC250 Virtual")
    block += dummy_descriptor()
    block += bytes([0])                                 # no extension blocks
    block += bytes([(-sum(block)) % 256])               # checksum: all 128 bytes sum to 0 mod 256

    assert len(block) == 128, len(block)
    return bytes(block)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"usage: python {sys.argv[0]} <output.bin>")
    with open(sys.argv[1], "wb") as output:
        output.write(build_edid())

"""Print calibration for the V1 case parts, measured with fit_coupon.py (2026-10-15).

Printer: Bambu Lab A1, 0.4 mm nozzle, textured PEI plate.
Filament: white Bambu PLA Matte. The coupon was sliced with the PLA *Basic* profile by mistake;
the profile is now PLA Matte. The first part printed with the Matte profile (frame_test_strip.py)
re-checks the tight fits (square key, fan grip) before any large part is printed.

How the numbers are used:
  * Every exported STL is scaled by XY_SCALE in X and Y to cancel the measured shrink.
    The coupon came out 0.4-0.6 % small: plate 111.5 x 65.6 (designed 112 x 66), fan gauge 125.9
    (designed 126.4).
  * The coupon's winning sizes were printed WITHOUT that scale. coupon_fit() converts each one
    back, so that after the export scale the feature is exactly the size that was tested.
    It only matters for the long fits (0.6 mm on the fan grip); on an M3 hole it is 0.02 mm.
"""

XY_SCALE = 1.005                  # mean of 112/111.5, 66/65.6, 126.4/125.9
Z_SCALE = 1.0                     # not measured; layer heights are exact enough for these parts

# Bed placement: each plate is centred on the A1's 256 x 256 bed. Its edges are kept clear because
# the A1 draws a purge line along the front edge and the parts print best away from the corners.
BED_SIZE = 256.0
BED_EDGE_MARGIN = 10.0            # minimum gap from any part to the bed edge (the side-wall pieces are 235 tall)


def coupon_fit(coupon_size):
    """Design size that prints like `coupon_size` did on the coupon, once XY_SCALE is applied."""
    return coupon_size / XY_SCALE


# Coupon results (coupon sizes, i.e. as they were drawn on the coupon).
M3_CLEARANCE_HOLE = coupon_fit(3.4)       # M3 slides through without wobble (3.2 too tight)
M3_NUT_POCKET_FLATS = coupon_fit(5.7)     # nut presses in, stays upside down, doesn't spin
M3_NUT_POCKET_DEPTH = 2.6
M4_CLEARANCE_HOLE = coupon_fit(4.5)       # the rack's handle screws (M4, 3.8 mm measured) pass
M6_CLEARANCE_HOLE = coupon_fit(6.5)       # the rack's M6 cage-nut screws pass
RACK_SQUARE_KEY = coupon_fit(9.0)         # drops into the frame's 9.1 mm square holes
FAN_GRIP_GAP = coupon_fit(120.4)          # held a fan on the coupon (Basic profile); 120.8 was loose
# With the Matte profile the frame test strip's 120.4 gauge (tall thin lips) was loose. The stiff
# fan_grip_gauge.py bars both held a fan (2026-10-15): the 120.4 gap with crush ribs is used,
# because the ribs squash to take up print error. Fans are retained by clips, not by this grip.
FAN_GRIP_RIB_RADIUS = 0.8
FAN_GRIP_RIB_PROTRUSION = 0.35            # into the gap on each side

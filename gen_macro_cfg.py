#!/usr/bin/env python
from os import path
import yaml

MACRO_CFG_PATH = path.join(
    path.dirname(__file__), "openlane/user_project_wrapper/macro.cfg"
)

with open(path.join(path.dirname(__file__), "tt_user_module.yaml")) as fh:
    slots = yaml.safe_load(fh)

ROWS = 1
MUX_COLS = 8
ROW_SPACING = 544
FIRST_ROW_Y = 897.6
LEFT_MUX_X = 46
RIGHT_MUX_X = 2707.10

def get_macro_size(name):
    with open(f"lef/tt_um_{name}.lef") as f:
        for line in f:
            lineparts = line.strip().split()
            if lineparts[0] == "SIZE" and lineparts[2] == "BY":
                return [float(lineparts[1]), float(lineparts[3])]


def validate_slot_height(y, x, valid_heights):
    slot_index = f"{y}.{x}"
    if not slot_index in slots:
        return False

    slot_name = slots[slot_index]['name']
    width, height = get_macro_size(slot_name)
    if not height in valid_heights:
        raise Exception(
            f"Slot height mismatch for ${y+1}.{x} (${slot_name}): ${height} not in ${valid_heights}"
        )
    return height


macrofile = open(MACRO_CFG_PATH, "w")
macrofile.write(f"# Controller\n")
macrofile.write("tt_top1.ctrl_I 1367.12 108.8 N\n")
macrofile.write("\n")

macrofile.write(f"# Muxes\n")
for y in range(ROWS):
    row_y = FIRST_ROW_Y + y * ROW_SPACING
    macrofile.write(f"tt_top1.branch\[{y*2}\].mux_I {LEFT_MUX_X}    {row_y}   N\n")
    macrofile.write(f"tt_top1.branch\[{y*2+1}\].mux_I 1512  {row_y}   FN\n")
macrofile.write("\n")

for y in range(ROWS):
    bottom_y = FIRST_ROW_Y + y * ROW_SPACING - 111.52
    top_y = FIRST_ROW_Y + y * ROW_SPACING + 57.12
    mux_idx = y * 2
    macrofile.write(f"# Row {y}\n")

    for x in range(MUX_COLS):
        # Left branch
        pos_x = LEFT_MUX_X + x * 170.66
        if validate_slot_height(y + 1, x, valid_heights=[108.800, 220.320]):
            macrofile.write(
                f"tt_top1.branch\[{mux_idx}\].col_um\[{x}\].um_top_I.block_{mux_idx+1}_{x}.tt_um_I  {pos_x: <7.2f} {top_y:.2f}   FS\n"
            )
        slot_height = validate_slot_height(y, x, valid_heights=[108.800, 220.320])
        if slot_height:
            pos_y = bottom_y - slot_height + 108.8
            if x == 0 and slot_height > 108.800: # as1802 - 8 slot wide, so put it below the others
                pos_y -= slot_height
            macrofile.write(
                f"tt_top1.branch\[{mux_idx}\].col_um\[{x}\].um_bot_I.block_{mux_idx}_{x}.tt_um_I  {pos_x: <7.2f} {pos_y:.2f}   N\n"
            )

        # Right branch
        pos_x = RIGHT_MUX_X - x * 170.66
        if validate_slot_height(y + 1, x + 16, valid_heights=[108.800, 220.320]):
            macrofile.write(
                f"tt_top1.branch\[{mux_idx+1}\].col_um\[{x}\].um_top_I.block_{mux_idx+1}_{x+16}.tt_um_I {pos_x: <7.2f} {top_y:.2f}   S\n"
            )
        slot_height = validate_slot_height(y, x + 16, valid_heights=[108.800, 220.320])
        if slot_height:
            pos_y = bottom_y - slot_height + 108.8
            macrofile.write(
                f"tt_top1.branch\[{mux_idx+1}\].col_um\[{x}\].um_bot_I.block_{mux_idx}_{x+16}.tt_um_I {pos_x: <7.2f} {pos_y:.2f}   FN\n"
            )
    macrofile.write(f"\n")

macrofile.write(f"# SRAM\n")
for slot in slots.values():
    if slot.get('sram', False):
        # hard-coded for now: SRAM macro, right above urish_sram_poc
        macrofile.write(f'tt_top1.branch\[1\].col_um\[7\].um_top_I.block_1_23.sram 1512.48 1200        N\n')

macrofile.close()

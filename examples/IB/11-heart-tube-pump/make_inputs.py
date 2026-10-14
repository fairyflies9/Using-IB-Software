"""make_inputs.py: writes the four other input files of example IB/11 from input2d.

Each variant changes only two things: the ACTUATION key and the structure_names
line with its sub-blocks, so that the driving structure comes first.
Run it in the example folder after editing input2d: python3 make_inputs.py
"""
import re

base = open("input2d", encoding="utf-8").read()

variants = {
    "input2d.force-vp": ("FORCE_VP", ["vp_aforce_512", "heart_tube_512", "heart_peri_512", "heart_race_512", "markers_512"]),
    "input2d.force-peri": ("FORCE_PERI", ["peri_aforce_512", "heart_tube_stiff_512", "heart_peri_512", "heart_race_512", "markers_512"]),
    "input2d.stiffness-peri": ("STIFFNESS_PERI", ["peri_kwave_512", "heart_tube_512", "heart_peri_512", "heart_race_512", "markers_512"]),
    "input2d.target-peri": ("TARGET_PERI", ["pperi_top_512", "pperi_bot_512", "heart_tube_512", "heart_peri_512", "heart_race_512", "markers_512"]),
}

block_re = re.compile(r"IBStandardInitializer \{.*?\n\}\n", re.S)
for name, (mode, structures) in variants.items():
    text = base.replace('ACTUATION = "TARGET_VP"', 'ACTUATION = "%s"' % mode)
    text = text.replace("moving target points (this file)", "moving target points (input2d)")
    text = text.replace("(input2d.%s)" % name.split(".")[1], "(this file)")
    if mode == "FORCE_PERI":
        # the stiff tube needs a shorter step (chapter 8a: ten times the stiffness, a quarter of the step at most)
        old_dt = "DT                  = 5.0e-5                   // maximum timestep size (s); the course version used 1.0e-5 (see README.md)\n"
        assert text.count(old_dt) == 1
        text = text.replace(old_dt, "DT                  = 2.5e-5                   // maximum timestep size (s): the stiff tube of this mode needs half the step of the others (see README.md)\n")
    block = "IBStandardInitializer {\n   max_levels = MAX_LEVELS\n   structure_names = " + \
        ", ".join('"%s"' % s for s in structures) + "\n"
    for k, s in enumerate(structures):
        block += "   %s {\n      level_number = MAX_LEVELS - 1%s\n   }\n" % (
            s, "        // put the structure on the finest grid level" if k == 0 else "")
    block += "}\n"
    text, n = block_re.subn(block, text, count=1)
    assert n == 1, name
    open(name, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote", name, "with ACTUATION =", mode, "and", len(structures), "structures")

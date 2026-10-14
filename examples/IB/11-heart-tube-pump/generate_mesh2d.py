"""generate_mesh2d.py: writes the structure files for example IB/11 (heart-tube pump,
Using IB Software). A line-by-line port of generate_mesh2d.m (UNC, 2014).

Structures (each a .vertex file, with .spring, .beam and .target files where needed):
  heart_tube_512     the elastic section of the tube: two straight walls with springs, beams,
                     and target points on the rigid ends
  heart_race_512     the racetrack that closes the loop (target points only)
  heart_peri_512     the pericardium, a rigid box around the elastic section (target points only)
  markers_512        121 passive points inside the tube that move with the fluid
  actuator_top_512, actuator_bot_512   short pieces of wall driven by moving target points
                     (valveless suction pumping, mode TARGET_VP)
  pperi_top_512, pperi_bot_512         longer pieces driven by a travelling wave of target points
                     (prescribed peristalsis, mode TARGET_PERI)
  vp_aforce_512      the same short piece as the actuators, with "springs" across the tube that
                     carry an applied sinusoidal force (force function 1, mode FORCE_VP)
  peri_aforce_512    a long piece with springs across the tube carrying a travelling Gaussian
                     force (force function 2, mode FORCE_PERI)
  peri_kwave_512     the same long piece with ordinary springs of zero stiffness and rest length
                     (1 - percont)*diameter, whose stiffness the program raises where a wave
                     passes (mode STIFFNESS_PERI, the 2014 code's version)
Run it in the example folder: python3 generate_mesh2d.py
"""
import math

L = 1.0                                 # length of computational domain (m)
N = 512                                 # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                              # Cartesian mesh width (m)
ds = L / (2 * N)                        # space between boundary points in straight tube

# Parameters for the racetrack
Let = 0.4                               # Length of elastic tube (m)
Nend = 10                               # Number of rigid points on each end of elastic section
Lt = Let + 2 * Nend * ds                # Length of straight section with rigid points on each end

diameter = 0.1                          # diameter of the tube
R2 = 0.1                                # radius of inner wall
R1 = R2 + diameter                      # radius of outer wall
percont = 0.5                           # contraction of the stiffness-wave peristalsis: rest length (1 - percont)*diameter; the 2014 code used 0.8 (see README.md)

Nstraight = 2 * math.ceil(Lt / ds)      # number of points along each straight section
Ncurve = 2 * math.ceil(math.pi * R1 / ds)   # number of points along each curved section
Nrace = Nstraight + 2 * Ncurve          # number of points making up the racetrack part
dtheta = math.pi / (Ncurve / 2)         # angle increment for drawing curved edges

mesh_name = "heart_"                    # structure name

centery = 0                             # y-position of center of curved sections
centerx1 = -0.5 * Lt                    # x-position of center of left curved section
centerx2 = 0.5 * Lt                     # x-position of center of right curved section

# Parameters for the pericardium
Dp = 2 * diameter                       # diameter of the pericardium
Nperi = 2 * math.ceil((Dp - diameter) / ds)   # number of boundary points along the sides of the pericardium
Nperitot = Nperi + Nstraight            # total number of pericardium points

# Parameters for the actuator
La = 0.04                               # length of the actuator section
NLa = math.ceil(La / ds)                # number of points along each actuator
Ca = 0.25 * Lt                          # center of the actuator section
NCa = math.ceil(math.ceil(Nstraight / 2) * Ca / Lt)   # index of the center point
Na1 = NCa - math.ceil(NLa / 2)          # index of the starting point with respect to the elastic section
Na2 = Na1 + NLa - 1                     # index of the ending point with respect to the elastic section

# Parameters for the prescribed peristalsis
Lap = 0.3                               # length of the actuator section
NLap = math.ceil(Lap / ds)              # number of points along each actuator
Cap = 0.5 * Lt                          # center of the actuator section
NCap = math.ceil(math.ceil(Nstraight / 2) * Cap / Lt)  # index of the center point
Na1p = NCap - math.ceil(NLap / 2)       # index of the starting point with respect to the elastic section
Na2p = Na1p + NLap - 1                  # index of the ending point with respect to the elastic section

# Parameters for applied force peristalsis
Lnperi = 0.05                           # length of the end of the flexible tube without peristalsis
Lperi = Lt - 2 * Lnperi                 # length of the peristalsis section of tube
Nperist = math.ceil(Lperi / ds)         # number of peristaltic points on top or bottom of tube
NCent = math.ceil(Nstraight / 4)        # index of center of elastic tube
Nperi1 = NCent - math.ceil(0.5 * Nperist)   # index of the starting point with respect to the elastic section
Nperi2 = Nperi1 + Nperist - 1           # index of the ending point with respect to the elastic section

# parameters for markers
Nmarkersx = 11                          # number of columns of markers
Nmarkersy = 11                          # number of markers in each column
Nmarkers = Nmarkersx * Nmarkersy        # total number of markers
dmx = Let / (Nmarkersx - 1)             # space between markers in x-direction
dmy = diameter / (Nmarkersy - 1)        # space between markers in y-direction

# material parameters
kappa_spring = 2.0e0                    # spring constant (Newton); the file stores kappa_spring/ds
kappa_beam = 1.0e-2                     # beam stiffness constant (Newton m^2); the file stores kappa_beam/ds^3
stiff_factor = 10.0                     # heart_tube_stiff_512: the same tube with beams this many times stiffer, for mode FORCE_PERI (see README.md)
kappa_target = kappa_spring             # target point penalty spring constant (Newton); the file stores kappa_target/ds
Fmag = 1.0e0                            # applied force per cross-tube "spring" of the travelling wave (mode FORCE_PERI); the 2014 code used 4.0 ("my best guess at a reasonable applied force"), which closes the tube (see README.md)
Fmag_vp = 0.25e0                        # the same for the suction actuator (mode FORCE_VP): 0.5 and above close the tube (see README.md)
phase = 0                               # initial phase of the oscillating force, F = Fmag*phase; the program updates it every step


def fopen(name):
    return open(name, "w", newline="\n")


# Make the elastic section of the tube: top wall then bottom wall, left to right
with fopen(f"{mesh_name}tube_{N}.vertex") as f:
    f.write("%d\n" % Nstraight)
    for i in range(1, math.ceil(Nstraight / 2) + 1):
        ytop = centery - R2
        xtop = -Lt / 2 + (i - 1) * ds
        f.write("%1.16e %1.16e\n" % (xtop, ytop))
    for i in range(math.ceil(Nstraight / 2) + 1, Nstraight + 1):
        ybot = centery - R1
        xbot = -Lt / 2 + (i - math.ceil(Nstraight / 2) - 1) * ds
        f.write("%1.16e %1.16e\n" % (xbot, ybot))

# Make markers as vertices with no material properties
with fopen(f"markers_{N}.vertex") as f:
    f.write("%d\n" % Nmarkers)
    for i in range(0, Nmarkersx):
        for j in range(0, Nmarkersy):
            y = centery - R2 - j * dmy
            x = -Let / 2 + i * dmx
            f.write("%1.16e %1.16e\n" % (x, y))

# actuator part (valveless suction pumping with target points)
with fopen(f"actuator_top_{N}.vertex") as f:
    f.write("%d\n" % NLa)
    for i in range(Na1, Na2 + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2 + i * ds, centery - R2))
with fopen(f"actuator_bot_{N}.vertex") as f:
    f.write("%d\n" % NLa)
    for i in range(Na1, Na2 + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2 + i * ds, centery - R1))

# prescribed peristalsis part (a travelling wave of target points)
with fopen(f"pperi_top_{N}.vertex") as f:
    f.write("%d\n" % NLap)
    for i in range(Na1p, Na2p + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2 + i * ds, centery - R2))
with fopen(f"pperi_bot_{N}.vertex") as f:
    f.write("%d\n" % NLap)
    for i in range(Na1p, Na2p + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2 + i * ds, centery - R1))

# valveless pumping applied force: the actuator's points, top then bottom, in one structure
with fopen(f"vp_aforce_{N}.vertex") as f:
    f.write("%d\n" % (2 * NLa))
    for i in range(Na1, Na2 + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2 + i * ds, centery - R2))
    for i in range(Na1, Na2 + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2 + i * ds, centery - R1))

# peristalsis applied force and stiffness wave: the long section's points, top then bottom
for name in (f"peri_aforce_{N}.vertex", f"peri_kwave_{N}.vertex"):
    with fopen(name) as f:
        f.write("%d\n" % (2 * Nperist))
        for i in range(Nperi1, Nperi2 + 1):
            f.write("%1.16e %1.16e\n" % (-Lt / 2 + i * ds, centery - R2))
        for i in range(Nperi1, Nperi2 + 1):
            f.write("%1.16e %1.16e\n" % (-Lt / 2 + i * ds, centery - R1))

# race track part
with fopen(f"{mesh_name}race_{N}.vertex") as f:
    f.write("%d\n" % Nrace)
    # right curved part of racetrack
    for i in range(1, math.ceil(Ncurve / 2) + 1):
        theta = (i - 1) * dtheta - math.pi / 2
        f.write("%1.16e %1.16e\n" % (Lt / 2 + R2 * math.cos(theta), centery + R2 * math.sin(theta)))
    for i in range(math.ceil(Ncurve / 2) + 1, Ncurve + 1):
        theta = (i - Ncurve / 2 - 1) * dtheta - math.pi / 2
        f.write("%1.16e %1.16e\n" % (Lt / 2 + R1 * math.cos(theta), centery + R1 * math.sin(theta)))
    # straight section on the top
    for i in range(Ncurve + 1, Ncurve + math.ceil(Nstraight / 2) + 1):
        f.write("%1.16e %1.16e\n" % (centerx2 - (i - Ncurve - 1) * ds, centery + R2))
    for i in range(Ncurve + math.ceil(Nstraight / 2) + 1, Ncurve + Nstraight + 1):
        f.write("%1.16e %1.16e\n" % (centerx2 - (i - Ncurve - math.ceil(Nstraight / 2) - 1) * ds, centery + R1))
    # left curved part of racetrack
    for i in range(Ncurve + Nstraight + 1, Ncurve + Nstraight + math.ceil(Ncurve / 2) + 1):
        theta = math.pi / 2 + (i - Ncurve - Nstraight - 1) * dtheta
        f.write("%1.16e %1.16e\n" % (centerx1 + R2 * math.cos(theta), centery + R2 * math.sin(theta)))
    for i in range(Ncurve + Nstraight + math.ceil(Ncurve / 2) + 1, 2 * Ncurve + Nstraight + 1):
        theta = math.pi / 2 + (i - Ncurve - Nstraight - math.ceil(Ncurve / 2) - 1) * dtheta
        f.write("%1.16e %1.16e\n" % (centerx1 + R1 * math.cos(theta), centery + R1 * math.sin(theta)))

# Pericardium
with fopen(f"{mesh_name}peri_{N}.vertex") as f:
    f.write("%d\n" % Nperitot)
    # the top and bottom of the pericardium
    for i in range(1, math.ceil(Nstraight / 2) + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2 + (i - 1) * ds, centery - (R2 - (Dp - diameter) / 2)))
    for i in range(math.ceil(Nstraight / 2) + 1, Nstraight + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2 + (i - math.ceil(Nstraight / 2) - 1) * ds, centery - R1 - (Dp - diameter) / 2))
    # the four side pieces
    for i in range(Nstraight + 1, Nstraight + math.ceil(Nperi / 4) + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2, centery - (R1 + (Dp - diameter) / 2) + (i - Nstraight - 1) * ds))
    for i in range(Nstraight + math.ceil(Nperi / 4) + 1, Nstraight + math.ceil(Nperi / 2) + 1):
        f.write("%1.16e %1.16e\n" % (-Lt / 2, centery - R2 + (i - Nstraight - math.ceil(Nperi / 4) - 1) * ds))
    for i in range(Nstraight + math.ceil(Nperi / 2) + 1, Nstraight + math.ceil(3 * Nperi / 4) + 1):
        f.write("%1.16e %1.16e\n" % (Lt / 2, centery - (R1 + (Dp - diameter) / 2) + (i - Nstraight - math.ceil(Nperi / 2) - 1) * ds))
    for i in range(Nstraight + math.ceil(3 * Nperi / 4) + 1, Nperitot + 1):
        f.write("%1.16e %1.16e\n" % (Lt / 2, centery - R2 + (i - Nstraight - math.ceil(3 * Nperi / 4) - 1) * ds))

# Springs along the elastic section (file value kappa_spring/ds, rest length ds)
with fopen(f"{mesh_name}tube_{N}.spring") as f:
    f.write("%d\n" % (Nstraight - 2))
    for i in range(0, math.ceil(Nstraight / 2) - 1):
        f.write("%d %d %1.16e %1.16e\n" % (i, i + 1, kappa_spring * ds / (ds ** 2), ds))
    for i in range(math.ceil(Nstraight / 2), Nstraight - 1):
        f.write("%d %d %1.16e %1.16e\n" % (i, i + 1, kappa_spring * ds / (ds ** 2), ds))

# "Springs" across the tube that carry the applied valveless-pumping force:
# parameters Fmag and phase, force function 1 (applied_force in main.cpp: T = Fmag*phase)
with fopen(f"vp_aforce_{N}.spring") as f:
    f.write("%d\n" % NLa)
    for i in range(0, NLa):
        f.write("%d %d %1.16e %1.16e %d\n" % (i, i + NLa, Fmag_vp, phase, 1))

# "Springs" across the tube that carry the applied peristaltic force: force function 2
# (the 2014 lecture's version; the 2014 code shipped the stiffness-wave version below instead)
with fopen(f"peri_aforce_{N}.spring") as f:
    f.write("%d\n" % Nperist)
    for i in range(0, Nperist):
        f.write("%d %d %1.16e %1.16e %d\n" % (i, i + Nperist, Fmag, phase, 2))

# Ordinary springs across the tube with zero stiffness and a short rest length: the program
# raises the stiffness where the wave passes, so the walls are pulled to (1-percont)*diameter
with fopen(f"peri_kwave_{N}.spring") as f:
    f.write("%d\n" % Nperist)
    for i in range(0, Nperist):
        f.write("%d %d %1.16e %1.16e\n" % (i, i + Nperist, 0, (1 - percont) * diameter))

# Beams along the elastic section (file value kappa_beam/ds^3)
with fopen(f"{mesh_name}tube_{N}.beam") as f:
    f.write("%d\n" % (Nstraight - 4))
    for i in range(0, math.ceil(Nstraight / 2) - 2):
        f.write("%d %d %d %1.16e\n" % (i, i + 1, i + 2, kappa_beam * ds / (ds ** 4)))
    for i in range(math.ceil(Nstraight / 2), Nstraight - 2):
        f.write("%d %d %d %1.16e\n" % (i, i + 1, i + 2, kappa_beam * ds / (ds ** 4)))

# The stiff tube for mode FORCE_PERI: the same points, springs and targets, beams stiff_factor times stiffer.
import shutil
for ext in ("vertex", "spring"):
    shutil.copyfile(f"{mesh_name}tube_{N}.{ext}", f"{mesh_name}tube_stiff_{N}.{ext}")
with fopen(f"{mesh_name}tube_stiff_{N}.beam") as f:
    f.write("%d\n" % (Nstraight - 4))
    for i in range(0, math.ceil(Nstraight / 2) - 2):
        f.write("%d %d %d %1.16e\n" % (i, i + 1, i + 2, stiff_factor * kappa_beam * ds / (ds ** 4)))
    for i in range(math.ceil(Nstraight / 2), Nstraight - 2):
        f.write("%d %d %d %1.16e\n" % (i, i + 1, i + 2, stiff_factor * kappa_beam * ds / (ds ** 4)))

# Target points on the rigid ends of the elastic tube (Nend points at each of the four ends)
with fopen(f"{mesh_name}tube_{N}.target") as f:
    f.write("%d\n" % (4 * Nend))
    for i in range(0, Nend):
        f.write("%d %1.16e\n" % (i, kappa_target * ds / (ds ** 2)))
    for i in range(math.ceil(Nstraight / 2) - Nend, math.ceil(Nstraight / 2)):
        f.write("%d %1.16e\n" % (i, kappa_target * ds / (ds ** 2)))
    for i in range(math.ceil(Nstraight / 2), math.ceil(Nstraight / 2) + Nend):
        f.write("%d %1.16e\n" % (i, kappa_target * ds / (ds ** 2)))
    for i in range(Nstraight - Nend, Nstraight):
        f.write("%d %1.16e\n" % (i, kappa_target * ds / (ds ** 2)))

# Target points: every point of the actuators, the prescribed-peristalsis pieces, the racetrack
# and the pericardium
for name, count in ((f"actuator_top_{N}.target", NLa), (f"actuator_bot_{N}.target", NLa),
                    (f"pperi_top_{N}.target", NLap), (f"pperi_bot_{N}.target", NLap),
                    (f"{mesh_name}race_{N}.target", Nrace), (f"{mesh_name}peri_{N}.target", Nperitot)):
    with fopen(name) as f:
        f.write("%d\n" % count)
        for i in range(0, count):
            f.write("%d %1.16e\n" % (i, kappa_target * ds / (ds ** 2)))

print("wrote the structure files: tube %d points, racetrack %d, pericardium %d, markers %d, actuators 2 x %d, "
      "peristalsis pieces 2 x %d, applied-force sections %d and %d points" %
      (Nstraight, Nrace, Nperitot, Nmarkers, NLa, NLap, 2 * NLa, 2 * Nperist))

shutil.copyfile(f"{mesh_name}tube_{N}.target", f"{mesh_name}tube_stiff_{N}.target")

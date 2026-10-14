// pump_geometry.h: the few numbers of generate_mesh2d.py that the update
// functions of example IB/11 (heart-tube pump, Using IB Software) need.
// Keep them equal to the generator's. (The 2014 code repeated them as
// static const values in every update file.)
#ifndef included_pump_geometry
#define included_pump_geometry

namespace pump
{
static const double L = 1.0;                 // length of the computational domain (m)
static const int N = 512;                    // finest grid cells across the domain
static const double ds = L / (2.0 * N);      // spacing of the boundary points (m)
static const double diameter = 0.1;          // diameter of the tube (m)
static const double R2 = 0.1;                // distance from the middle of the domain to the inner wall (m)
static const double R1 = R2 + diameter;      // distance from the middle of the domain to the outer wall (m)
static const double pamp = 0.8;              // fraction of the diameter closed by the actuators
static const double amp = pamp * diameter / 2.0; // how far each wall of the actuator moves (m)
static const double Lap = 0.3;               // length of the prescribed-peristalsis section (m)
} // namespace pump

#endif // #ifndef included_pump_geometry

// bell_geometry.h: the numbers of generate_mesh2d.py that update_beams.cpp of
// example IB/10 (the jellyfish bell, Using IB Software) needs, and the bell
// shape itself. Keep them equal to the generator's.
//
// The bell is the curve of Herschlag and Miller's 2D jellyfish (J. Theor.
// Biol. 2011), as the 2013 course taught it: starting at the apex (r = 0,
// z = Zs) and going down one side, the tangent angle is
//     theta(s) = -1.55 (1 - exp(-s / beta)),
// where s is the arc length from the apex and beta is the one control
// parameter: it is horizontal at the apex and turns nearly vertical (-1.55 is
// nearly -pi/2) for s > beta. A large beta (0.5) is the relaxed, open bell;
// a small one (0.2) the contracted bell. The positions follow by marching
// along the curve in steps of ds, as the course code did:
//     z_{k+1} = z_k + ds sin(theta_k),   r_{k+1} = r_k + ds cos(theta_k).
#ifndef included_bell_geometry
#define included_bell_geometry

#include <cmath>
#include <vector>

namespace bell
{
static const double L = 4.0;                 // length of the computational domain
static const int N = 256;                    // finest grid cells across the domain
static const double ds = L / (2.0 * N);      // spacing of the boundary points (half a grid cell)
static const double arc = 1.0;               // arc length of each half of the bell, apex to tip
static const int n = static_cast<int>(std::lround(arc / ds)); // points per half (128); the bell has 2n+1 points
static const double Zs = 1.0;                // z of the apex at t = 0
static const double theta_max = 1.55;        // the tangent angle tends to -theta_max (nearly -pi/2)

// The right half of the bell for a given beta: r[k], z[k] for k = 0 (apex) to n (tip).
inline void shape(const double beta, std::vector<double>& r, std::vector<double>& z)
{
    r.assign(n + 1, 0.0);
    z.assign(n + 1, 0.0);
    r[0] = 0.0;
    z[0] = Zs;
    for (int k = 1; k <= n; ++k)
    {
        const double theta = -theta_max * (1.0 - std::exp(-(k * ds) / beta));
        z[k] = z[k - 1] + ds * std::sin(theta);
        r[k] = r[k - 1] + ds * std::cos(theta);
    }
    return;
}
} // namespace bell

#endif // #ifndef included_bell_geometry

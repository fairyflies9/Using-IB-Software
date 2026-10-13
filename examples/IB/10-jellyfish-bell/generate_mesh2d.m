% generate_mesh2d.m: writes the structure files for example IB/10 (the
% jellyfish bell, Using IB Software): a 2D bell of 2n+1 points from the left
% tip through the apex to the right tip, joined by springs and by beams whose
% preferred curvature is the bell's own shape at rest (beta = beta_0).
% update_beams.cpp changes that curvature in time to make the bell pulse.
%
% The shape (bell_geometry.h): from the apex (r = 0, z = Zs) down one side, the
% tangent angle is theta(s) = -1.55 (1 - exp(-s/beta)), s the arc length from
% the apex; the positions follow by marching along the curve in steps of ds,
% as the 2013 course code did. "The position of the boundary is calculated for
% beta_0 = 0.5" (2013).
%
% Run it in this folder (MATLAB or Octave): generate_mesh2d
% generate_mesh2d.py writes the same files (checked with Octave 8.4 and Python 3.12).

L = 4.0;                                      % length of computational domain
N = 256;                                      % number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L/N;                                     % Cartesian mesh width
ds = L/(2*N);                                 % distance between neighboring Lagrangian mesh points (half a cell)

arc = 1.0;                                    % arc length of each half of the bell, apex to tip
n = round(arc/ds);                            % points per half (128); the bell has 2n+1 points
npts = 2*n + 1;
Zs = 1.0;                                     % z of the apex at t = 0 (the bell hangs below it, open downward)
theta_max = 1.55;                             % the tangent angle tends to -theta_max (nearly -pi/2)
beta_0 = 0.5;                                 % the relaxed (open) bell; update_beams.cpp takes it to beta_m = 0.2

mesh_name = 'bell_';                          % structure name

kappa_spring = 1.0e3;                         % stretching stiffness (tension per unit strain); the file stores kappa_spring/ds
kappa_beam = 1.0;                             % bending stiffness; the file stores kappa_beam/ds^3

% The right half of the bell: r(k+1), z(k+1) for k = 0 (apex) to n (tip).
r = zeros(1, n+1);
z = zeros(1, n+1);
z(1) = Zs;
for k = 1:n
    theta = -theta_max*(1 - exp(-(k*ds)/beta_0));
    z(k+1) = z(k) + ds*sin(theta);
    r(k+1) = r(k) + ds*cos(theta);
end

% The whole curve, left tip (point 0) to right tip (point 2n), apex at point n:
% the left half is the mirror image of the right half. X(i+1) is point i.
X = zeros(1, npts);
Y = zeros(1, npts);
for i = 0:npts-1
    k = abs(i - n);
    if i < n
        X(i+1) = -r(k+1);
    else
        X(i+1) = r(k+1);
    end
    Y(i+1) = z(k+1);
end

% Write out the vertex information.
vertex_fid = fopen([mesh_name num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', npts);
for i = 0:npts-1
    fprintf(vertex_fid, '%1.16e %1.16e\n', X(i+1), Y(i+1));
end
fclose(vertex_fid);

% Write out the link information: a spring between each pair of neighbors,
% with the rest length equal to the distance between them at rest.
spring_fid = fopen([mesh_name num2str(N) '.spring'], 'w');
fprintf(spring_fid, '%d\n', npts-1);
for i = 0:npts-2
    rest = sqrt((X(i+2) - X(i+1))^2 + (Y(i+2) - Y(i+1))^2);
    fprintf(spring_fid, '%d %d %1.16e %1.16e\n', i, i+1, kappa_spring*ds/(ds^2), rest);
end
fclose(spring_fid);

% Write out the beam information: "i-1 i i+1 stiffness C1 C2", with the
% preferred curvature (C1, C2) = X_{i-1} - 2 X_i + X_{i+1} of the resting
% shape, so that the bell is in equilibrium at t = 0. update_beams.cpp
% overwrites C1 and C2 before every time step.
beam_fid = fopen([mesh_name num2str(N) '.beam'], 'w');
fprintf(beam_fid, '%d\n', npts-2);
for i = 1:npts-2
    c1 = X(i) - 2*X(i+1) + X(i+2);
    c2 = Y(i) - 2*Y(i+1) + Y(i+2);
    fprintf(beam_fid, '%d %d %d %1.16e %1.16e %1.16e\n', i-1, i, i+1, kappa_beam*ds/(ds^4), c1, c2);
end
fclose(beam_fid);

fprintf('wrote %s%d.vertex (%d points), .spring (%d), .beam (%d); ds = %g, dx = %g; bell width %.4f, height %.4f\n', ...
        mesh_name, N, npts, npts-1, npts-2, ds, dx, 2*r(n+1), Zs - z(n+1));

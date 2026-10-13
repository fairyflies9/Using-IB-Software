% generate_mesh2d.m: writes the structure files for example IB/09 (the curling
% beam, Using IB Software): a straight horizontal beam, clamped at its left end
% by two target points, whose preferred curvature update_beams.cpp raises from
% zero to that of a quarter circle over the first second.
%
% It is the generator of IB/03 (the tethered leaf) turned on its side, with the
% two target points moved from the middle to the left end. The .beam file has
% four columns (no preferred curvature), so the beams start straight; the
% program sets the curvature before every time step.
%
% Run it in this folder (MATLAB or Octave): generate_mesh2d
% generate_mesh2d.py writes the same files (checked with Octave 8.4 and Python 3.12).

L = 1.0;                                      % length of computational domain (m)
N = 512;                                      % number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L/N;                                     % Cartesian mesh width (m)

beam_length = 0.1;                            % beam length (m)
npts = ceil(2*(beam_length/L)*N);             % number of points along the beam (103)
ds = beam_length/(npts-1);                    % physical distance between neighboring Lagrangian mesh points (m)

mesh_name = 'beam_';                          % structure name
x_base = -0.05;                               % x position of the clamped end (m); the beam runs to the right
y_base = 0.0;                                 % y position of the beam (m)

kappa_spring = 3.0e1;                         % stretching stiffness K (tension per unit strain); the file stores kappa_spring/ds
kappa_beam = 2.0e-2;                          % bending stiffness (4x the leaf of IB/03); the file stores kappa_beam/ds^3
kappa_target = kappa_spring;                  % target point stiffness; the file stores kappa_target/ds

% Write out the vertex information: point 0 is the clamped left end and point
% npts-1 is the free right end.
vertex_fid = fopen([mesh_name num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', npts);
for s = 0:npts-1
    x = x_base + s*ds;
    y = y_base;
    fprintf(vertex_fid, '%1.16e %1.16e\n', x, y);
end
fclose(vertex_fid);

% Write out the link information (including connectivity and material parameters).
spring_fid = fopen([mesh_name num2str(N) '.spring'], 'w');
fprintf(spring_fid, '%d\n', npts-1);
for s = 0:npts-2
    fprintf(spring_fid, '%d %d %1.16e %1.16e\n', s, s+1, kappa_spring*ds/(ds^2), ds);
end
fclose(spring_fid);

% Write out the beam information: each line is "i-1 i i+1 stiffness". A fifth
% and sixth column would be the preferred curvature (C1, C2); left out, it is
% zero, and update_beams.cpp sets it in the program.
beam_fid = fopen([mesh_name num2str(N) '.beam'], 'w');
fprintf(beam_fid, '%d\n', npts-2);
for s = 0:npts-3
    fprintf(beam_fid, '%d %d %d %1.16e\n', s, s+1, s+2, kappa_beam*ds/(ds^4));
end
fclose(beam_fid);

% Write out the target point information: the two points at the clamped end,
% 0 and 1, are tethered to where they start, which fixes the end's position
% and its direction.
target_fid = fopen([mesh_name num2str(N) '.target'], 'w');
fprintf(target_fid, '%d\n', 2);
fprintf(target_fid, '%d %1.16e\n', 0, kappa_target*ds/(ds^2));
fprintf(target_fid, '%d %1.16e\n', 1, kappa_target*ds/(ds^2));
fclose(target_fid);

fprintf('wrote %s%d.vertex (%d points), .spring (%d), .beam (%d), .target (2); ds = %g m, dx = %g m\n', ...
        mesh_name, N, npts, npts-1, npts-2, ds, dx);

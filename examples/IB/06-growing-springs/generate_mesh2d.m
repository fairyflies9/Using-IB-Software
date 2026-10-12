% generate_mesh2d.m: writes wing_512.vertex and wing_512.spring for example
% IB/06 (Using IB Software). Run it in MATLAB or Octave from this folder.
% generate_mesh2d.py is a Python version that writes the same files.
% The course folder had no generator for these files. This script was
% written in 2026 and writes the same numbers as the course files.
% The structure (called "wing" for historical reasons) is a straight fiber
% of length 0.1 m on the x axis, from x = 0.1 (point 0) to x = 0 (the last
% point). Its points are joined by springs only: there are no beams, so the
% fiber has no bending stiffness. update_springs.cpp makes the springs'
% rest lengths grow during the run.
% Point indices in the IBAMR files start at 0.

L = 1;                              % length of computational domain (m)
N = 512;                            % number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L/N;                           % Cartesian mesh width (m)

fiber_length = 0.1;                 % fiber length (m)
npts = ceil(2*(fiber_length/L)*N);  % number of points along the fiber (103)
ds = fiber_length/(npts-1);         % physical distance between neighboring Lagrangian mesh points (m)

mesh_name = 'wing_';                % structure name
kappa_spring = 2.0e3;               % stretching stiffness K (tension per unit strain).
                                    % The .spring file stores K/ds, written below as kappa_spring*ds/(ds^2).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the vertex information
vertex_fid = fopen([mesh_name num2str(N) '.vertex'], 'w');

fprintf(vertex_fid, '%d\n', npts);

for s = 0:npts-1
   X(1) = fiber_length - s*ds;
   X(2) = 0.0;
   fprintf(vertex_fid, '%1.16e %1.16e\n', X(1), X(2));
end

fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the spring information: one spring between each pair of
% neighbors, with rest length ds (the starting spacing). The first point of
% each spring (the lower index) is its "master" point.
spring_fid = fopen([mesh_name num2str(N) '.spring'], 'w');

fprintf(spring_fid, '%d\n', npts-1);

for s = 0:npts-2
   fprintf(spring_fid, '%d %d %1.16e %1.16e\n', s, s+1, kappa_spring*ds/(ds^2), ds);
end

fclose(spring_fid);

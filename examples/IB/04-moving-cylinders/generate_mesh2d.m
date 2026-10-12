% generate_mesh2d.m: writes bristles1024.vertex and bristles1024.target for
% example IB/04 (Using IB Software). Run it in MATLAB or Octave from this
% folder. generate_mesh2d.py is a Python version of the same script.
% The course folder had no generator for these files. This script was
% written in 2026 to reproduce them: it gives the same numbers as the
% course files (see README.md for the one last-digit difference between
% MATLAB and Python).
% The structure is a row of 9 small cylinders ("bristles") along the x axis,
% 0.05 m apart, with the middle one centered on the origin. Every point is a
% target point, and update_target_point_positions.cpp moves the targets.
% Point indices in the IBAMR files start at 0.

L = 1;                              % length of computational domain (m)
N = 1024;                           % number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L/N;                           % Cartesian mesh width (m)

radius = 0.0025;                    % cylinder radius (m)
spacing = 0.05;                     % distance between neighboring cylinder centers (m)
ncyl = 9;                           % number of cylinders
npts = ceil(2*(2*pi*radius/L)*N);   % number of points on each cylinder (33)
dtheta = 2*pi/npts;                 % angle between neighboring points on a cylinder

mesh_name = 'bristles';             % structure name
kappa_target = 4.096e6;             % target point stiffness written to the .target file

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the vertex information, one cylinder after another from left to
% right. On each cylinder the angle goes from dtheta to 2*pi, so the last
% point of each cylinder is the one on its right side.
vertex_fid = fopen([mesh_name num2str(N) '.vertex'], 'w');

fprintf(vertex_fid, '%d\n', ncyl*npts);

for c = 0:ncyl-1
   center_x = (c - (ncyl-1)/2)*spacing;   % -0.2, -0.15, ..., 0.2
   for s = 1:npts
      X(1) = center_x + radius*cos(s*dtheta);
      X(2) = radius*sin(s*dtheta);
      fprintf(vertex_fid, '%1.16e %1.16e\n', X(1), X(2));
   end
end

fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the target point information: every point is a target point.
target_fid = fopen([mesh_name num2str(N) '.target'], 'w');

fprintf(target_fid, '%d\n', ncyl*npts);

for s = 0:ncyl*npts-1
   fprintf(target_fid, '%d %1.16e\n', s, kappa_target);
end

fclose(target_fid);

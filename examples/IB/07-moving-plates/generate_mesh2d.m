% generate_mesh2d.m: writes the structure files of both plates for example
% IB/07 (Using IB Software): plate2d_left_512.* and plate2d_rght_512.*
% (.vertex, .spring, .beam and .target). Run it in MATLAB or Octave from this
% folder. generate_mesh2d.py is a Python version that writes the same files.
% Each plate is a straight vertical line of points of length 0.1 m, joined by
% springs and beams, and every point is a target point. The plates start
% 5 mm apart, on either side of the origin.
% The course version wrote one plate per run and had to be edited (an
% if (1) / else switch) to write the other one. This version writes both.
% Point indices in the IBAMR files start at 0, separately for each plate.

L = 1;                              % length of computational domain (m)
N = 512;                            % number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L/N;                           % Cartesian mesh width (m)

plate_length = 0.1;                 % plate length (m)
npts = ceil(2*(plate_length/L)*N);  % number of points along each plate (103)
ds = plate_length/(npts-1);         % physical distance between neighboring Lagrangian mesh points (m)

mesh_names = {'plate2d_left_', 'plate2d_rght_'};  % structure names
offsets = [-2.5e-3, +2.5e-3];       % x position of each plate (m)

kappa_spring = 2.0e3;               % stretching stiffness K (tension per unit strain).
                                    % The .spring file stores K/ds, written below as kappa_spring*ds/(ds^2).
kappa_beam = 5.0e-3;                % bending stiffness. The .beam file stores kappa_beam/ds^3,
                                    % written below as kappa_beam*ds/(ds^4).
kappa_target = kappa_spring;        % target point stiffness. The .target file stores kappa_target/ds.

for p = 1:2
mesh_name = mesh_names{p};
offset = offsets(p);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the vertex information: point 0 is the top end (y = 0.05).
vertex_fid = fopen([mesh_name num2str(N) '.vertex'], 'w');

fprintf(vertex_fid, '%d\n', npts);

for s = 0:npts-1
   X(1) = offset;
   X(2) = 0.0 + 0.5*plate_length - s*ds;
   fprintf(vertex_fid, '%1.16e %1.16e\n', X(1), X(2));
end

fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the spring information
spring_fid = fopen([mesh_name num2str(N) '.spring'], 'w');

fprintf(spring_fid, '%d\n', npts-1);

for s = 0:npts-2
   fprintf(spring_fid, '%d %d %1.16e %1.16e\n', s, s+1, kappa_spring*ds/(ds^2), ds);
end

fclose(spring_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the beam information
beam_fid = fopen([mesh_name num2str(N) '.beam'], 'w');

fprintf(beam_fid, '%d\n', npts-2);

for s = 0:npts-3
   fprintf(beam_fid, '%d %d %d %1.16e\n', s, s+1, s+2, kappa_beam*ds/(ds^4));
end

fclose(beam_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the target point information: every point is a target point.
target_fid = fopen([mesh_name num2str(N) '.target'], 'w');

fprintf(target_fid, '%d\n', npts);

for s = 0:npts-1
   fprintf(target_fid, '%d %1.16e\n', s, kappa_target*ds/(ds^2));
end

fclose(target_fid);

end

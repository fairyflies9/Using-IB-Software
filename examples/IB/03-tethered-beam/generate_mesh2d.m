% generate_mesh2d.m: writes leaf_512.vertex, leaf_512.spring, leaf_512.beam
% and leaf_512.target for example IB/03 (Using IB Software). Run it in MATLAB
% or Octave from this folder. generate_mesh2d.py is a Python version that
% writes the same files.
% The "leaf" is a straight vertical beam of length 0.1 m centered on the
% origin. Its points are joined by springs (stretching) and beams (bending).
% Two points in the middle are target points that hold the leaf in place.
% Point indices in the IBAMR files start at 0.

L = 1;                              % length of computational domain (m)
N = 512;                            % number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L/N;                           % Cartesian mesh width (m)

plate_length = 0.1;                 % leaf length (m)
npts = ceil(2*(plate_length/L)*N);  % number of points along the leaf (103)
ds = plate_length/(npts-1);         % physical distance between neighboring Lagrangian mesh points (m)

mesh_name = 'leaf_';                % structure name
offset = 0;                         % x position of the leaf (m)

kappa_spring = 3.0e1;               % stretching stiffness K (tension per unit strain).
                                    % The .spring file stores K/ds, written below as kappa_spring*ds/(ds^2).
kappa_beam = 5.0e-3;                % bending stiffness. The .beam file stores kappa_beam/ds^3,
                                    % written below as kappa_beam*ds/(ds^4).
kappa_target = kappa_spring;        % target point stiffness. The .target file stores kappa_target/ds.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the vertex information: point 0 is the top end (y = 0.05) and
% point npts-1 is the bottom end (y = -0.05).
vertex_fid = fopen([mesh_name num2str(N) '.vertex'], 'w');

fprintf(vertex_fid, '%d\n', npts);

for s = 0:npts-1
   X(1) = offset;
   X(2) = 0.0 + 0.5*plate_length - s*ds;
   fprintf(vertex_fid, '%1.16e %1.16e\n', X(1), X(2));
end

fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the spring information: one spring between each pair of
% neighbors, with rest length ds (the starting spacing).
spring_fid = fopen([mesh_name num2str(N) '.spring'], 'w');

fprintf(spring_fid, '%d\n', npts-1);

for s = 0:npts-2
   fprintf(spring_fid, '%d %d %1.16e %1.16e\n', s, s+1, kappa_spring*ds/(ds^2), ds);
end

fclose(spring_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the beam information: one beam for each three neighboring points.
% The leaf is straight, so the beams have no preferred curvature.
beam_fid = fopen([mesh_name num2str(N) '.beam'], 'w');

fprintf(beam_fid, '%d\n', npts-2);

for s = 0:npts-3
   fprintf(beam_fid, '%d %d %d %1.16e\n', s, s+1, s+2, kappa_beam*ds/(ds^4));
end

fclose(beam_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the target point information: the two middle points, 50 (at
% y = ds) and 51 (at y = 0), are tethered to where they start.
target_fid = fopen([mesh_name num2str(N) '.target'], 'w');

fprintf(target_fid, '%d\n', 2);

s = floor(npts/2)-1;
fprintf(target_fid, '%d %1.16e\n', s, kappa_target*ds/(ds^2));

s = floor(npts/2);
fprintf(target_fid, '%d %1.16e\n', s, kappa_target*ds/(ds^2));

fclose(target_fid);

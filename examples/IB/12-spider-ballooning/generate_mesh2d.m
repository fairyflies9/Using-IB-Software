% generate_mesh2d.m: writes the structure files for example IB/12 (spider
% ballooning, Using IB Software): a vertical dragline of springs and (very weak)
% beams with a point mass at its lower end, which the penalty IB method lets fall
% under gravity.
%
% The 2020 lecture: "a mass is attached to the bottom of a string. The string
% resists bending (a little) and stretching and is massless. This is a simplified
% model of spider ballooning. The spider is represented as the point mass. The
% silk drag line is the string (massless). The spider falls to the bottom of the
% domain due to gravity. The dragline slows it down." "Note that this is a 2D
% simulation. The mass is actually a mass per unit length."
%
% Change from the course generator (8-AddingMass-Spider, 2020): the beam loop
% ran one triple too far (it wrote a 170th beam, 169 170 171, naming a point past
% the end of the dragline, under a header of 169 that was right). The mass point
% is the last point of the dragline (point npts-1), as in the course file.
%
% Run it in this folder (MATLAB or Octave): generate_mesh2d
% generate_mesh2d.py writes the same files (checked with Octave 8.4 and Python 3.12).

L = 0.3;                                      % width of the computational domain (m); it is 0.3 by 0.6
N = 256;                                      % number of Cartesian grid meshwidths across the width at the finest level
dx = L/N;                                     % Cartesian mesh width (m)

drag_length = 0.10;                           % length of the dragline (m)
npts = ceil(2*(drag_length/L)*N);             % number of points along the dragline (171)
ds = drag_length/(npts-1);                    % distance between neighboring points (m)

mesh_name = 'spider2d_';                      % structure name
x_line = 0.15;                                % x of the dragline (m): the middle of the width
y_top = 0.45 + 0.5*drag_length;               % y of the top of the dragline (m); the mass hangs 0.1 m below

kappa_spring = 2.0e1;                         % stretching stiffness of the dragline (N); the file stores it as is
kappa_beam = 5.0e-15;                         % bending stiffness (N m^2): "resists bending (a little)"; the file stores kappa_beam/ds^2
mass = 2.0e-5;                                % the spider's mass (kg per unit depth)
kappa_mass = kappa_spring;                    % the penalty spring that ties the mass point to its massive copy (N/m)

% Write out the vertex information: point 0 is the top of the dragline and
% point npts-1 is the bottom, where the spider is.
vertex_fid = fopen([mesh_name num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', npts);
for s = 0:npts-1
    fprintf(vertex_fid, '%1.16e %1.16e\n', x_line, y_top - s*ds);
end
fclose(vertex_fid);

% Write out the link information (including connectivity and material parameters).
spring_fid = fopen([mesh_name num2str(N) '.spring'], 'w');
fprintf(spring_fid, '%d\n', npts-1);
for s = 0:npts-2
    fprintf(spring_fid, '%d %d %1.16e %1.16e\n', s, s+1, kappa_spring*ds/ds, ds);
end
fclose(spring_fid);

% Write out the beam information: one beam for each three consecutive points.
beam_fid = fopen([mesh_name num2str(N) '.beam'], 'w');
fprintf(beam_fid, '%d\n', npts-2);
for s = 0:npts-3
    fprintf(beam_fid, '%d %d %d %1.16e\n', s, s+1, s+2, kappa_beam*ds/(ds^3));
end
fclose(beam_fid);

% Write out the mass information: "index mass penalty_stiffness". The point is
% tied to a massive copy of itself by a spring of this stiffness and zero rest
% length; the copy moves by Newton's law under gravity (chapter 13).
mass_fid = fopen([mesh_name num2str(N) '.mass'], 'w');
fprintf(mass_fid, '%d\n', 1);
fprintf(mass_fid, '%d %1.16e %1.16e\n', npts-1, mass, kappa_mass*ds/ds);
fclose(mass_fid);

fprintf('wrote %s%d.vertex (%d points), .spring (%d), .beam (%d), .mass (1 point, %g kg/m); ds = %g m, dx = %g m\n', ...
        mesh_name, N, npts, npts-1, npts-2, mass, ds, dx);

% generate_mesh3d.m: structure files for example IB/08 (glycocalyx in 3D).
%
% Writes glyco_512.vertex and glyco_512.target for one glycocalyx fiber: the
% surface of a cylinder standing on the floor of the domain, made of rings of
% points. Every point is a target point, so the fiber is held in place.
% Runs in MATLAB or Octave.
%
% The domain in input3d is 1/8 by 1/8 by 1 (m) and the finest grid has
% N = 512 cells across the height L = 1, so dx = 1/512. The points are spaced
% about dx/2 apart, both up the cylinder and around it.

L = 1;                              % height of computational domain (m)
N = 512;                            % number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L/N;                           % Cartesian mesh width (m)

glyco_length = 10/64;                  % glyco length (m)
glyco_radius = 1/64;                % glyco radius (m)
glyco_radius = glyco_radius - 1.25*dx;  %glyco radius adjustment for width of delta functions
npts_height = ceil(2*(glyco_length/L)*N);  % number of points along the height (160)
npts_circum = ceil(2*(2*pi*glyco_radius/L)*N); %number of points along the circumference (85)
npts = npts_height*npts_circum;	    % total number of points in the fiber (13600)
dq = glyco_length/(npts_height-1);     % glyco mesh spacing along the height (m)

% ds is NOT the spacing of the points around the cylinder. That spacing is
% 2*pi*glyco_radius/npts_circum = 9.7e-4 m (about dx/2), while
% ds = glyco_radius/(npts_circum-1) = 1.6e-4 m is 6.2 times smaller.
% ds is used only to scale the target stiffness below: each target point gets
% kappa_target/ds = 3.19e4. Dividing by the true spacing would give 5.13e3.
% The value is kept so that the files match the ones every earlier version of
% this example used.
ds = glyco_radius/(npts_circum-1);   % scale for the target stiffness (m)

mesh_name = 'glyco_';      % structure name
offset = -0.5*L+dq;	                    % glyco base from bottom of domain (m)

kappa_spring = 5e0;               % spring constant (Newton)
kappa_beam = 0.0; %5.0e-6;                % beam stiffness constant (Newton m^2)
kappa_target = kappa_spring;        % target point penalty spring constant (Newton)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the vertex information: one ring of npts_circum points at each of
% the npts_height heights, starting at the ring nearest the floor.

vertex_fid = fopen([mesh_name num2str(N) '.vertex'], 'w');

fprintf(vertex_fid, '%d\n', npts);

for q = 0:npts_height-1
for s = 0:npts_circum-1
   X(1) = 0.0 + glyco_radius*cos(s*2*pi/npts_circum);
   X(2) = 0.0 + glyco_radius*sin(s*2*pi/npts_circum);
   X(3) = offset + q*dq;
   fprintf(vertex_fid, '%1.16e %1.16e %1.16e\n', X(1), X(2), X(3));
end
end

fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Springs and beams are not used: the target points alone hold the fiber.
% The commented-out code below shows how they could be added (input3d would
% not need to change, because IBAMR reads a .spring or .beam file whenever it
% finds one with the structure's name).
%
% % Write out the spring information
% spring_fid = fopen([mesh_name num2str(N) '.spring'], 'w');
%
% fprintf(spring_fid, '%d\n', npts-npts_height+npts-npts_circum);
%
% for q = 0:npts_height-1
% for s = 0:npts_circum-2
%    fprintf(spring_fid, '%d %d %1.16e %1.16e\n', q*npts_circum+s, q*npts_circum+s+1, kappa_spring*ds/(ds^2), ds);
% end
% end
%
%
% for q = 0:npts_height-2
% for s = 0:npts_circum-1
%    fprintf(spring_fid, '%d %d %1.16e %1.16e\n', q*npts_circum+s, (q+1)*npts_circum+s, kappa_spring*ds/(ds^2), ds);
% end
% end
%
% fclose(spring_fid);
%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% % Write out the beam information
% beam_fid = fopen([mesh_name num2str(N) '.beam'], 'w');
%
% fprintf(beam_fid, '%d\n', npts-2*npts_height+npts-2*npts_circum);
%
% for q = 0:npts_height-1
% for s = 0:npts_circum-3
%    fprintf(beam_fid, '%d %d %d %1.16e\n', q*npts_circum+s, q*npts_circum+s+1, q*npts_circum+s+2, kappa_beam*ds/(ds^4));
% end
% end
%
%
% for q = 0:npts_height-3
% for s = 0:npts_circum-1
%    fprintf(beam_fid, '%d %d %d %1.16e\n', q*npts_circum+s, (q+1)*npts_circum+s, (q+2)*npts_circum+s, kappa_beam*ds/(ds^4));
% end
% end
%
% fclose(beam_fid);
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the target point information
target_fid = fopen([mesh_name num2str(N) '.target'], 'w');

fprintf(target_fid, '%d\n', npts_height*npts_circum);  % every point of the fiber is a target point

for q=0:npts_height-1 % all rings, all the way up the cylinder
  for s = 0:npts_circum-1
   fprintf(target_fid, '%d %1.16e\n', q*npts_circum+s, kappa_target*ds/(ds^2));
end
end

fclose(target_fid);


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

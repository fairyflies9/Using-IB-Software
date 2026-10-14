% generate_mesh2d.m: writes the structure files for example IB/11 (heart-tube pump,
% Using IB Software). The 2014 generator (Forced-tube-pump, UNC) with two edits:
%   * peri_aforce_512.spring is written with Fmag, phase and force function 2 again
%     (the line the 2014 lecture describes; the 2014 code had it commented out);
%   * peri_kwave_512.vertex and .spring hold the 2014 code's version of that
%     section: zero-stiffness springs with rest length (1-percont)*diameter.
% generate_mesh2d.py writes the same files (checked with Octave 8.4 and Python 3.12).

L = 1;                              % length of computational domain (m)
N = 512;                            % number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L/N;                           % Cartesian mesh width (m)
ds = L/(2*N);                       % space between boundary points in straight tube

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Parameters for the racetrack

Let = 0.4;                          % Length of elastic tube (m)
Nend = 10;                           % Number of rigid points on each end of elastic section
Lt = Let+2*Nend*ds;                 % Length of straight section with three rigid points on each end

diameter = 0.1;                     % diameter of the tube
R2 = 0.1;                           % radius of inner wall
R1 = R2+diameter;                   % radius of outer wall
percont = 0.5;                      %contraction of the stiffness-wave peristalsis: rest length (1-percont)*diameter; the 2014 code used 0.8 (see README.md)

Nstraight = 2*ceil(Lt/ds);          % number of points along each straight section
Ncurve = 2*ceil(pi*R1/ds);          % number of points along each curved section
Nrace = Nstraight+2*Ncurve;         % number of points making up the racetrack part
dtheta = pi/(Ncurve/2);             % angle increment for drawing curved edges

mesh_name = 'heart_';               % structure name

centery = 0;                        % y-position of center of curved sections
centerx1 = -0.5*Lt;                 % x-position of center of left curved section
centerx2 = 0.5*Lt;                  % x-position of center of right curved section

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Parameters for the pericardium
Dp = 2*diameter;                    %diameter of the pericardium
Nperi = 2*ceil((Dp-diameter)/ds);  % number of boundary points along the sides of the pericardium
Nperitot = Nperi + Nstraight;       % total number of pericardium points

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Parameters for the actuator
La = 0.04;                          % length of the actuator section
NLa = ceil(La/ds);                  % number of points along each actuator
Ca = 0.25*Lt;                       % center of the actuator section
NCa = ceil(ceil(Nstraight/2)*Ca/Lt); % index of the center point
Na1 = NCa - ceil(NLa/2);            % index of the starting point with respect to the elastic section
Na2 = Na1+NLa-1;                    % index of the ending point with respect to the elastic section

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Parameters for the prescribed peristalsis
Lap = 0.3;                          % length of the actuator section
NLap = ceil(Lap/ds);                  % number of points along each actuator
Cap = 0.5*Lt;                       % center of the actuator section
NCap = ceil(ceil(Nstraight/2)*Cap/Lt); % index of the center point
Na1p = NCap - ceil(NLap/2);            % index of the starting point with respect to the elastic section
Na2p = Na1p+NLap-1;                    % index of the ending point with respect to the elastic section


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Parameters for applied force peristalsis
Lnperi = 0.05;                          % length of the end of the flexible tube without peristalsis
Lperi = Lt-2*Lnperi;                      % length of the peristalsis section of tube
Nperist = ceil(Lperi/ds);                 % number of peristaltic points on top or bottom of tube
NCent = ceil(Nstraight/4);                 %index of center of elastic tube
Nperi1 = NCent-ceil(0.5*Nperist);           % index of the starting point with respect to the elastic section
Nperi2 = Nperi1+Nperist-1;                  %index of the ending point with respect to the elastic section

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% parameters for markers
Nmarkersx = 11;                     %number of columns of markers
Nmarkersy = 11;                     %number of markers in each column
Nmarkers=Nmarkersx*Nmarkersy;       %total number of markers
dmx = Let/(Nmarkersx-1);            %space between markers in x-direction
dmy = diameter/(Nmarkersy-1);       %space between markers in y-direction

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% material parameters
kappa_spring = 2.0e0;               % spring constant (Newton)
kappa_beam = 1.0e-2;                 % beam stiffness constant (Newton m^2)
stiff_factor = 10.0;                 % heart_tube_stiff_512: the same tube with beams this many times stiffer, for mode FORCE_PERI (see README.md)
kappa_target = kappa_spring;        % target point penalty spring constant (Newton)
Fmag = 1.0e0;                % force of the travelling wave (mode FORCE_PERI); the 2014 code used 4.0 ("my best guess at a reasonable applied force"), which closes the tube (see README.md)
Fmag_vp = 0.25e0;            % the same for the suction actuator (mode FORCE_VP): 0.5 and above close the tube (see README.md)
phase = 0;                      %initial phase of the oscillating force, where F=Fmag*phase and phase = (1+sin(2*pi*f*t-pi/2));

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Make the elastic section of the tube
% Write out the vertex information

vertex_fid = fopen([mesh_name 'tube_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', Nstraight);

%top part
for i=1:ceil(Nstraight/2),
    ytop = centery-R2;
    xtop = -Lt/2+(i-1)*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xtop, ytop);
end

%bottom part
for i=ceil(Nstraight/2)+1:Nstraight,
    ybot = centery-R1;
    xbot = -Lt/2+(i-ceil(Nstraight/2)-1)*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xbot, ybot);
end
fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Make markers as vertices with no material properties

vertex_fid = fopen(['markers_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', Nmarkers);

%top part
for i=0:Nmarkersx-1,
    for j=0:Nmarkersy-1,
        y = centery-R2-j*dmy;
        x = -Let/2+i*dmx;
    fprintf(vertex_fid, '%1.16e %1.16e\n', x, y);
    end
end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% actuator part
% Write out the vertex information

%top part
vertex_fid = fopen(['actuator_top_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', NLa);

for i=Na1:Na2,
    ytop = centery-R2;
    xtop = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xtop, ytop);
end
fclose(vertex_fid);

%bottom part
vertex_fid = fopen(['actuator_bot_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', NLa);

for i=Na1:Na2,
    ybot = centery-R1;
    xbot = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xbot, ybot);
end
fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% prescribed peristalsis part
% Write out the vertex information

%top part
vertex_fid = fopen(['pperi_top_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', NLap);

for i=Na1p:Na2p,
    ytop = centery-R2;
    xtop = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xtop, ytop);
end
fclose(vertex_fid);

%bottom part
vertex_fid = fopen(['pperi_bot_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', NLap);

for i=Na1p:Na2p,
    ybot = centery-R1;
    xbot = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xbot, ybot);
end
fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% valveless pumping applied force
% Use either the target point actuator or the applied force, but not both.
% Write out the vertex information

vertex_fid = fopen(['vp_aforce_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', 2*NLa);

%top points
for i=Na1:Na2,
    ytop = centery-R2;
    xtop = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xtop, ytop);
end

%bottom points
for i=Na1:Na2,
    ybot = centery-R1;
    xbot = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xbot, ybot);
end
fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% peristalsis applied force
% Use either the target point actuator or the applied force, but not both.
% Write out the vertex information

vertex_fid = fopen(['peri_aforce_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', 2*Nperist);

%top points
for i=Nperi1:Nperi2,
    ytop = centery-R2;
    xtop = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xtop, ytop);
end

%bottom points
for i=Nperi1:Nperi2,
    ybot = centery-R1;
    xbot = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xbot, ybot);
end
fclose(vertex_fid);

% the same points again, for the stiffness-wave version
vertex_fid = fopen(['peri_kwave_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', 2*Nperist);

%top points
for i=Nperi1:Nperi2,
    ytop = centery-R2;
    xtop = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xtop, ytop);
end

%bottom points
for i=Nperi1:Nperi2,
    ybot = centery-R1;
    xbot = -Lt/2+i*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xbot, ybot);
end
fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% race track part
% Write out the vertex information

vertex_fid = fopen([mesh_name 'race_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', Nrace);

%right curved part of racetrack
for i=1:ceil(Ncurve/2),
    theta = (i-1)*dtheta-pi/2;
    yin = centery+R2*sin(theta);
    xin = Lt/2+R2*cos(theta);
    fprintf(vertex_fid, '%1.16e %1.16e\n', xin, yin);
end

for i=ceil(Ncurve/2)+1:Ncurve,
    theta=(i-Ncurve/2-1)*dtheta-pi/2;
    yout = centery+R1*sin(theta);
    xout = Lt/2+R1*cos(theta);
    fprintf(vertex_fid, '%1.16e %1.16e\n', xout, yout);
end

%straight section on the top
for i = Ncurve+1:Ncurve+ceil(Nstraight/2),
    yin = centery+R2;
    xin = centerx2-(i-Ncurve-1)*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xin, yin);
end

for i = Ncurve+ceil(Nstraight/2)+1:Ncurve+Nstraight,
    yout = centery+R1;
    xout = centerx2-(i-Ncurve-ceil(Nstraight/2)-1)*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xout, yout);
end

%left curved part of racetrack
for i = Ncurve+Nstraight+1:Ncurve+Nstraight+ceil(Ncurve/2),
    theta = pi/2+(i-Ncurve-Nstraight-1)*dtheta;
    yin = centery+R2*sin(theta);
    xin = centerx1+R2*cos(theta);
    fprintf(vertex_fid, '%1.16e %1.16e\n', xin, yin);
end

for i = Ncurve+Nstraight+ceil(Ncurve/2)+1:2*Ncurve+Nstraight,
    theta = pi/2+(i-Ncurve-Nstraight-ceil(Ncurve/2)-1)*dtheta;
    yout = centery+R1*sin(theta);
    xout = centerx1+R1*cos(theta);
    fprintf(vertex_fid, '%1.16e %1.16e\n', xout, yout);
end
fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Pericardium
% Write out the vertex information

vertex_fid = fopen([mesh_name 'peri_' num2str(N) '.vertex'], 'w');
fprintf(vertex_fid, '%d\n', Nperitot);

% make the top and bottom of the pericardium
for i=1:ceil(Nstraight/2),
    ytop = centery-(R2-(Dp-diameter)/2);
    xtop = -Lt/2+(i-1)*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xtop, ytop);
end

for i=ceil(Nstraight/2)+1:Nstraight,
    ybot = centery-R1-(Dp-diameter)/2;
    xbot = -Lt/2+(i-ceil(Nstraight/2)-1)*ds;
    fprintf(vertex_fid, '%1.16e %1.16e\n', xbot, ybot);
end

% make the four side pieces
for i=Nstraight+1:Nstraight+ceil(Nperi/4),
    y = centery-(R1+(Dp-diameter)/2)+(i-Nstraight-1)*ds;
    x = -Lt/2;
    fprintf(vertex_fid, '%1.16e %1.16e\n', x, y);
end

for i=Nstraight+ceil(Nperi/4)+1:Nstraight+ceil(Nperi/2),
    y = centery-R2+(i-Nstraight-ceil(Nperi/4)-1)*ds;
    x = -Lt/2;
    fprintf(vertex_fid, '%1.16e %1.16e\n', x, y);
end

for i=Nstraight+ceil(Nperi/2)+1:Nstraight+ceil(3*Nperi/4),
    y = centery-(R1+(Dp-diameter)/2)+(i-Nstraight-ceil(Nperi/2)-1)*ds;
    x = Lt/2;
    fprintf(vertex_fid, '%1.16e %1.16e\n', x, y);
end

for i=Nstraight+ceil(3*Nperi/4)+1:Nperitot,
    y = centery-R2+(i-Nstraight-ceil(3*Nperi/4)-1)*ds;
    x = Lt/2;
    fprintf(vertex_fid, '%1.16e %1.16e\n', x, y);
end
fclose(vertex_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Write out the spring information for the elastic section

spring_fid = fopen([mesh_name 'tube_' num2str(N) '.spring'], 'w');
fprintf(spring_fid, '%d\n', Nstraight-2);

%elastic part of tube
for i = 0:ceil(Nstraight/2)-2,
    fprintf(spring_fid, '%d %d %1.16e %1.16e\n', i, i+1, kappa_spring*ds/(ds^2), ds);
end

for i = ceil(Nstraight/2):Nstraight-2,
    fprintf(spring_fid, '%d %d %1.16e %1.16e\n', i, i+1, kappa_spring*ds/(ds^2), ds);
end

fclose(spring_fid);
%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the spring information for the valveless pumping applied force

spring_fid = fopen(['vp_aforce_' num2str(N) '.spring'], 'w');
fprintf(spring_fid, '%d\n', NLa);

%elastic part of tube
for i = 0:(NLa-1),
    fprintf(spring_fid, '%d %d %1.16e %1.16e %d\n', i, i+NLa, Fmag_vp, phase, 1);
end

fclose(spring_fid);
%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Write out the spring information for the peristalsis applied force

spring_fid = fopen(['peri_aforce_' num2str(N) '.spring'], 'w');
fprintf(spring_fid, '%d\n', Nperist);

%elastic part of tube
for i = 0:(Nperist-1),
    fprintf(spring_fid, '%d %d %1.16e %1.16e %d\n', i, i+Nperist, Fmag, phase, 2);
end

fclose(spring_fid);

% Write out the spring information for the stiffness-wave peristalsis (the 2014 code's version)

spring_fid = fopen(['peri_kwave_' num2str(N) '.spring'], 'w');
fprintf(spring_fid, '%d\n', Nperist);

for i = 0:(Nperist-1),
    fprintf(spring_fid, '%d %d %1.16e %1.16e\n', i, i+Nperist, 0, (1-percont)*diameter);
end

fclose(spring_fid);
%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% % Write out the beam information for the elastic section

beam_fid = fopen([mesh_name 'tube_' num2str(N) '.beam'], 'w');
fprintf(beam_fid, '%d\n', Nstraight-4);

%elastic part of tube
for i = 0:ceil(Nstraight/2)-3,
    fprintf(beam_fid, '%d %d %d %1.16e\n', i, i+1, i+2, kappa_beam*ds/(ds^4));
end

for i = ceil(Nstraight/2):Nstraight-3,
    fprintf(beam_fid, '%d %d %d %1.16e\n', i, i+1, i+2, kappa_beam*ds/(ds^4));
end
fclose(beam_fid);

% The stiff tube for mode FORCE_PERI: the same points, springs and targets, beams stiff_factor times stiffer.
copyfile([mesh_name 'tube_' num2str(N) '.vertex'], [mesh_name 'tube_stiff_' num2str(N) '.vertex']);
copyfile([mesh_name 'tube_' num2str(N) '.spring'], [mesh_name 'tube_stiff_' num2str(N) '.spring']);
beam_fid = fopen([mesh_name 'tube_stiff_' num2str(N) '.beam'], 'w');
fprintf(beam_fid, '%d\n', Nstraight-4);
for i = 0:ceil(Nstraight/2)-3,
    fprintf(beam_fid, '%d %d %d %1.16e\n', i, i+1, i+2, stiff_factor*kappa_beam*ds/(ds^4));
end
for i = ceil(Nstraight/2):Nstraight-3,
    fprintf(beam_fid, '%d %d %d %1.16e\n', i, i+1, i+2, stiff_factor*kappa_beam*ds/(ds^4));
end
fclose(beam_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Write out the target point information for the ends of the elastic tube
target_fid = fopen([mesh_name 'tube_' num2str(N) '.target'], 'w');

fprintf(target_fid, '%d\n', 4*Nend);

for i = 0:Nend-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

for i = ceil(Nstraight/2)-Nend:ceil(Nstraight/2)-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

for i = ceil(Nstraight/2):ceil(Nstraight/2)+Nend-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

for i = Nstraight-Nend:Nstraight-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

fclose(target_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Write out the target point information for the actuator

%top actuator
target_fid = fopen(['actuator_top_' num2str(N) '.target'], 'w');
fprintf(target_fid, '%d\n', NLa);

for i = 0:NLa-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

fclose(target_fid);

%bottom actuator
target_fid = fopen(['actuator_bot_' num2str(N) '.target'], 'w');
fprintf(target_fid, '%d\n', NLa);

for i = 0:NLa-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

fclose(target_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Write out the target point information for the actuator

%top prescribed peristalsis
target_fid = fopen(['pperi_top_' num2str(N) '.target'], 'w');
fprintf(target_fid, '%d\n', NLap);

for i = 0:NLap-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

fclose(target_fid);

%bottom prescribed peristalsis
target_fid = fopen(['pperi_bot_' num2str(N) '.target'], 'w');
fprintf(target_fid, '%d\n', NLap);

for i = 0:NLap-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

fclose(target_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Write out the target point information for the racetrack
target_fid = fopen([mesh_name 'race_' num2str(N) '.target'], 'w');

fprintf(target_fid, '%d\n', Nrace);

for i = 0:Nrace-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

fclose(target_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Write out the target point information for the pericardium
target_fid = fopen([mesh_name 'peri_' num2str(N) '.target'], 'w');

fprintf(target_fid, '%d\n', Nperitot);

for i = 0:Nperitot-1,
    fprintf(target_fid, '%d %1.16e\n', i, kappa_target*ds/(ds^2));
end

fclose(target_fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

copyfile([mesh_name 'tube_' num2str(N) '.target'], [mesh_name 'tube_stiff_' num2str(N) '.target']);

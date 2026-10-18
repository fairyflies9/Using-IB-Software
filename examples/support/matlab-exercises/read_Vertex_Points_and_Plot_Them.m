%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% FUNCTION: Reads in the # of vertex pts and all the vertex pts from the
%           .vertex file and plots them.
%
% NOTE: pass string of geometry name in as input, e.g., 'rubberband' to
%       read in and plot rubberband.vertex points.
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function  read_Vertex_Points_and_Plot_Them(struct_name)

%struct_name = (name of geometry), e.g., rubberband for rubberband.vertex

filename = [struct_name '.vertex'];  %Name of file to read in
fileID = fopen(filename);

% The first line is the count: read it on its own. Octave's textscan does not end a row at a line with one
% number, so reading it with the rest paired the count with the first x; MATLAB's textscan does.
N = str2double(fgetl(fileID));  % # of Lagrangian Pts

% Read in the file, use 'CollectOutput' to gather all similar data together
% and 'CommentStyle' to to end and be able to skip lines in file.
C = textscan(fileID,'%f %f','CollectOutput',1);


fclose(fileID);     %Close the data file.

vertices = C{1};    %Stores all read in data in vertices (N,2) array

xLag = zeros(N,1);  % Initialize storage for Lagrangian Pts.
yLag = xLag;        % Initialize storage for Lagrangian Pts.

for i=1:N
   xLag(i,1) = vertices(i,1); %Stores x-values of Lagrangian Mesh
   yLag(i,1) = vertices(i,2); %Stores y-values of Lagrangian Mesh
end

plot(xLag,yLag,'r*'); hold on;
plot(xLag,yLag,'bo'); hold on;
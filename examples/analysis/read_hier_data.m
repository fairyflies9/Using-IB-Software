function [t, data] = read_hier_data(folder, kind, dt, ndim)
% READ_HIER_DATA  Read the Lagrangian positions or forces that the IB examples
% of Using IB Software write (X.NNNNN and F.NNNNN in hier_data_IB2d or
% hier_data_IB3d), in MATLAB or Octave.
%
%   [t, X] = read_hier_data('hier_data_IB2d', 'X', 1.0e-4);      % 2D positions
%   [t, F] = read_hier_data('hier_data_IB2d', 'F', 1.0e-4);      % 2D forces
%   [t, F] = read_hier_data('hier_data_IB3d', 'F', 1.0e-4, 3);   % 3D forces
%
% t is the vector of times (the file number, which is the time step, times dt;
% with dt omitted or empty, the step numbers) and data{k} is an npts-by-ndim
% matrix: the x, y[, z] of every point at time t(k), in Lagrangian order (all
% structures together, in the order of structure_names in the input file).
%
% The files are PETSc ASCII vectors written by the examples' output_data()
% (chapter 11): a few header lines ("Vec Object: 3 MPI processes", "  type:
% mpi") and one line "Process [k]" before each process's block, then one
% number per line, NDIM numbers per point. The course's dataread2.m skipped
% the header with textscan(..., 'HeaderLines', 3, 'commentstyle', 'P'); this
% function instead keeps every line that is a number, which works whatever
% the number of header lines and processes.
%
% The sum of the forces, sum(F{k}), is what the examples print as integral{F}.

if nargin < 3, dt = []; end
if nargin < 4, ndim = 2; end

files = dir(fullfile(folder, [kind '.*']));
if isempty(files)
    error('read_hier_data:nofiles', 'no %s.* files in %s', kind, folder);
end
steps = zeros(numel(files), 1);
for k = 1:numel(files)
    steps(k) = str2double(files(k).name(numel(kind) + 2:end));
end
[steps, order] = sort(steps);
files = files(order);
if isempty(dt)
    t = steps;
else
    t = steps * dt;
end

data = cell(numel(files), 1);
for k = 1:numel(files)
    lines = strsplit(fileread(fullfile(folder, files(k).name)), {'\n', '\r'});
    v = str2double(lines);              % NaN for "Vec Object: ...", "  type: mpi", "Process [0]", ""
    v = v(~isnan(v));
    if mod(numel(v), ndim) ~= 0
        error('read_hier_data:count', '%s holds %d numbers, not a multiple of %d', files(k).name, numel(v), ndim);
    end
    data{k} = reshape(v, ndim, [])';     % one row per point: x y [z]
end
end

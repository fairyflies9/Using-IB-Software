function ex = read_exodus(path)
% READ_EXODUS  The ExodusII file of an IBFE run (viz_IB2d/output.ex2) in MATLAB or Octave (chapter 33).
%   ex = read_exodus('viz_IB2d/output.ex2') returns a structure:
%     ex.times        the dump times (num_states x 1)
%     ex.coords       the reference positions (num_nodes x ndim)
%     ex.names        the nodal variable names, e.g. {'F_0','F_1','U_0','U_1','X_0','X_1','dX_0','dX_1'}
%     ex.connect1     the connectivity of element block 1 (num_elem x nodes per element), 1-based
%     ex.var(name, s) a function: the nodal field 'name' at state s (1-based: s = 1 is the first dump)
%     ex.positions(s) the current configuration, coords + dX, at state s
%   MATLAB reads netCDF with ncread/ncinfo; Octave needs the netcdf package (apt install octave-netcdf, or
%   pkg install -forge netcdf), then the same calls. ExodusII stores names as fixed-width character arrays and
%   the fields as vals_nod_var<k>(time_step, num_nodes); ncread returns them transposed (num_nodes x time_step).
if exist('OCTAVE_VERSION', 'builtin')
    pkg load netcdf
end
info = ncinfo(path);
ex.path = path;
ex.times = double(ncread(path, 'time_whole'));
ex.times = ex.times(:);
dims = containers.Map();
for k = 1:numel(info.Dimensions)
    dims(info.Dimensions(k).Name) = info.Dimensions(k).Length;
end
ex.ndim = dims('num_dim');
axes = {'coordx', 'coordy', 'coordz'};
ex.coords = [];
for d = 1:ex.ndim
    ex.coords = [ex.coords, double(ncread(path, axes{d}))];
end
names = ncread(path, 'name_nod_var');          % char array, one column per name (len_name x num_nod_var)
ex.names = cell(1, size(names, 2));
for k = 1:size(names, 2)
    s = names(:, k)';
    s = s(s ~= 0);
    ex.names{k} = strtrim(s);
end
vars = {info.Variables.Name};
for k = 1:numel(vars)
    if strncmp(vars{k}, 'connect', 7)
        ex.(vars{k}) = double(ncread(path, vars{k}))';   % (num_elem x nodes per element), 1-based already
    end
end
ex.var = @(name, s) local_var(path, ex.names, name, s);
ex.positions = @(s) ex.coords + cell2mat(arrayfun(@(d) local_var(path, ex.names, sprintf('dX_%d', d - 1), s), 1:ex.ndim, 'UniformOutput', false));
end

function a = local_var(path, names, name, s)
k = find(strcmp(names, name), 1);
if isempty(k)
    error('read_exodus:name', '%s is not a nodal variable (%s)', name, strjoin(names, ' '));
end
data = ncread(path, sprintf('vals_nod_var%d', k));   % num_nodes x num_states
if nargin < 4 || isempty(s)
    a = double(data);                                  % the whole history
else
    a = double(data(:, s));
end
end

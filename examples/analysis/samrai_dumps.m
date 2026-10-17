function d = samrai_dumps(folder, var, level)
% SAMRAI_DUMPS  IBAMR's VisIt dumps (SAMRAI HDF5) into MATLAB, on a uniform grid (chapter 33).
%   d = samrai_dumps('viz_IB2d/visit_dump.00341')          the frame's description: d.time, d.variables, d.levels, ...
%   d = samrai_dumps('viz_IB2d/visit_dump.00341', 'Omega') adds d.x, d.y (axes) and d.data (ny x nx) on the finest
%                                                          level's grid; a vector gives d.data{1}, d.data{2}
%   d = samrai_dumps(folder, var, level)                   the same on a coarser level (0 = coarsest)
%   The same reading as samrai_dumps.py: summary.samrai (BASIC_INFO, extents) and processor_cluster.CCCCC.samrai
%   (processor.P/level.L/patch.N/<var>, stored x-fastest). Nodal variables (U, P, Omega) come back on the nodes
%   (nx+1 columns), cell-centred ones (Div U) on the cell centres; coarse patches are interpolated (nodal, bilinear)
%   or repeated (cell) where no finer patch exists. 2D only in this MATLAB version. MATLAB's h5read is used;
%   Octave 8 has no h5read, so this file was checked only against the Python reader, not run.
%   This replaces the 2013 lecture's importsamrai.m (E. Tytell), which read the pre-HDF5 layout and could not cope
%   with the space in "Div U".
sfile = fullfile(folder, 'summary.samrai');
d.folder = folder;
d.ndim = double(h5read(sfile, '/BASIC_INFO/number_dimensions_of_problem'));
names = h5read(sfile, '/BASIC_INFO/var_names');
d.variables = cellfun(@(s) strtrim(char(s(:)')), num2cell(names, 1), 'UniformOutput', false);
d.variables = cellfun(@(s) regexprep(s, char(0), ''), d.variables, 'UniformOutput', false);
cc = double(h5read(sfile, '/BASIC_INFO/var_cell_centered'));
nc = double(h5read(sfile, '/BASIC_INFO/var_number_components'));
d.cell_centered = containers.Map(d.variables, num2cell(cc(:)'));
d.components = containers.Map(d.variables, num2cell(nc(:)'));
d.levels = double(h5read(sfile, '/BASIC_INFO/number_levels'));
d.patches_per_level = double(h5read(sfile, '/BASIC_INFO/number_patches_at_level'))';
dx = double(h5read(sfile, '/BASIC_INFO/dx'));            % h5read returns (3 x levels)
d.dx = dx(1:d.ndim, :)';                                   % levels x ndim
xlo = double(h5read(sfile, '/BASIC_INFO/XLO')); d.xlo = xlo(1:d.ndim)';
rat = double(h5read(sfile, '/BASIC_INFO/ratios_to_coarser_levels')); d.ratios = rat(1:d.ndim, :)';
d.time = double(h5read(sfile, '/BASIC_INFO/time'));
d.step = double(h5read(sfile, '/BASIC_INFO/time_step_number'));
ext = h5read(sfile, '/extents/patch_extents');            % struct of arrays: lower, upper, xlo, xup
pmap = h5read(sfile, '/extents/patch_map');
np = numel(pmap.level_number);
d.patches = struct('level', cell(1, np));
for k = 1:np
    d.patches(k).level = double(pmap.level_number(k));
    d.patches(k).number = double(pmap.patch_number(k));
    d.patches(k).proc = double(pmap.processor_number(k));
    d.patches(k).cluster = double(pmap.file_cluster_number(k));
    d.patches(k).lower = double(ext.lower(1:d.ndim, k))';
    d.patches(k).upper = double(ext.upper(1:d.ndim, k))';
    d.patches(k).xlo = double(ext.xlo(1:d.ndim, k))';
    d.patches(k).xup = double(ext.xup(1:d.ndim, k))';
end
lv0 = d.patches([d.patches.level] == 0);
d.n0 = max(reshape([lv0.upper], d.ndim, [])', [], 1) + 1;
if nargin < 2, return; end
if nargin < 3, level = d.levels - 1; end
if d.ndim ~= 2, error('samrai_dumps:ndim', 'this MATLAB version handles 2D dumps; use samrai_dumps.py for 3D'); end
r0 = ones(1, 2); for lv = 2:level + 1, r0 = r0 .* d.ratios(lv, :); end
n = d.n0 .* r0; dxl = d.dx(level + 1, :);
cell = d.cell_centered(var); ncomp = d.components(var);
if cell, shape = [n(2) n(1)]; else, shape = [n(2) + 1, n(1) + 1]; end
data = cell(1, ncomp); for c = 1:ncomp, data{c} = nan(shape); end
for lv = 0:level
    r = ones(1, 2); for k = lv + 2:level + 1, r = r .* d.ratios(k, :); end
    for p = d.patches([d.patches.level] == lv)
        lo = p.lower .* r; hi = (p.upper + 1) .* r;                   % cells of 'level', 0-based, hi exclusive
        arrays = patch_data(d, p, var, cell, ncomp);
        for c = 1:ncomp
            a = arrays{c};
            if cell
                fine = kron(a, ones(r(2), r(1)));
                data{c}(lo(2) + 1:hi(2), lo(1) + 1:hi(1)) = fine;
            else
                [nyp, nxp] = size(a);
                xi = linspace(0, nxp - 1, (nxp - 1) * r(1) + 1); yi = linspace(0, nyp - 1, (nyp - 1) * r(2) + 1);
                fine = interp2(0:nxp - 1, 0:nyp - 1, a, xi, yi', 'linear');
                data{c}(lo(2) + 1:hi(2) + 1, lo(1) + 1:hi(1) + 1) = fine;
            end
        end
    end
end
if cell
    d.x = d.xlo(1) + dxl(1) * ((0:n(1) - 1) + 0.5); d.y = d.xlo(2) + dxl(2) * ((0:n(2) - 1) + 0.5);
else
    d.x = d.xlo(1) + dxl(1) * (0:n(1)); d.y = d.xlo(2) + dxl(2) * (0:n(2));
end
if ncomp == 1, d.data = data{1}; else, d.data = data; end
end

function arrays = patch_data(d, p, var, cell, ncomp)
f = fullfile(d.folder, sprintf('processor_cluster.%05d.samrai', p.cluster));
g = sprintf('/processor.%05d/level.%05d/patch.%05d/', p.proc, p.level, p.number);
ncell = p.upper - p.lower + 1;
if cell, shape = ncell; else, shape = ncell + 1; end
arrays = cell(1, ncomp);
for c = 1:ncomp
    if ncomp == 1, name = var; else, name = sprintf('%s.%02d', var, c - 1); end
    a = double(h5read(f, [g name]));
    arrays{c} = reshape(a, shape(1), shape(2))';     % x fastest in the file -> (ny x nx)
end
end

function v = read_vtk_legacy(path)
% READ_VTK_LEGACY  A legacy ASCII VTK file (VisIt's exports, IB2d's output) into MATLAB or Octave (chapter 33).
%   v = read_vtk_legacy('Omega_0056.vtk') returns a structure with
%     v.type     'RECTILINEAR_GRID' | 'STRUCTURED_POINTS' | 'UNSTRUCTURED_GRID' | 'POLYDATA'
%     v.dims     [nx ny nz] for the gridded types; v.x, v.y, v.z the axes (RECTILINEAR) or built from
%                v.origin and v.spacing (STRUCTURED_POINTS)
%     v.points   (N x 3) for the unstructured types; v.cells a cell array of 1-based index lists
%     v.data     a struct of the point data: scalars as [ny nx] (or [nz ny nx]) arrays, vectors as [... 3]
%     v.field    a struct of the file's FIELD data (VisIt writes TIME and CYCLE)
%   The arrays are indexed (y, x) so that pcolor(v.x, v.y, v.data.Omega) and quiver(v.x, v.y, U(:,:,1), U(:,:,2))
%   work as they stand. The origin of this reader is N. Battista's read_Structured_Vector_Field_Data_From_vtk.m
%   (2017), which read one file layout; this one reads the headers.
fid = fopen(path, 'r');
if fid < 0, error('read_vtk_legacy:open', 'cannot open %s', path); end
txt = fread(fid, inf, '*char')';
fclose(fid);
lines = strsplit(txt, {'\n', '\r\n'});
if ~strncmp(lines{1}, '# vtk DataFile', 14), error('read_vtk_legacy:format', '%s is not a legacy VTK file', path); end
if ~strcmpi(strtrim(lines{3}), 'ASCII'), error('read_vtk_legacy:binary', 'binary legacy VTK: convert with VisIt (Legacy Ascii) or use Python'); end
v = struct('path', path, 'title', strtrim(lines{2}), 'data', struct(), 'field', struct(), 'cells', {{}});
i = 4; n = numel(lines); dims = []; npts = 0; section = '';
while i <= n
    line = strtrim(lines{i});
    if isempty(line), i = i + 1; continue; end
    parts = strsplit(line);
    key = upper(parts{1});
    switch key
        case 'DATASET'
            v.type = upper(parts{2}); i = i + 1;
        case 'DIMENSIONS'
            dims = cellfun(@str2double, parts(2:4)); v.dims = dims; npts = prod(dims); i = i + 1;
        case 'ORIGIN'
            v.origin = cellfun(@str2double, parts(2:4)); i = i + 1;
        case 'SPACING'
            v.spacing = cellfun(@str2double, parts(2:4)); i = i + 1;
        case {'X_COORDINATES', 'Y_COORDINATES', 'Z_COORDINATES'}
            cnt = str2double(parts{2}); [arr, i] = numbers(lines, cnt, i + 1); v.(lower(key(1))) = arr(:)';
        case 'POINTS'
            cnt = str2double(parts{2}); [arr, i] = numbers(lines, 3 * cnt, i + 1); v.points = reshape(arr, 3, cnt)'; npts = cnt;
        case {'CELLS', 'VERTICES', 'LINES', 'POLYGONS'}
            cnt = str2double(parts{2}); sz = str2double(parts{3});
            j = i + 1;
            while j <= numel(lines) && isempty(strtrim(lines{j})), j = j + 1; end
            if j <= numel(lines) && strncmpi(strtrim(lines{j}), 'OFFSETS', 7)
                % VTK 5.1 layout (VTK 9, IB2d's Python writer): cnt offsets (cells + 1), then sz connectivity entries
                [off, i] = numbers(lines, cnt, j + 1);
                while i <= numel(lines) && ~strncmpi(strtrim(lines{i}), 'CONNECTIVITY', 12), i = i + 1; end
                [conn, i] = numbers(lines, sz, i + 1);
                cells = cell(1, cnt - 1);
                for k = 1:cnt - 1, cells{k} = conn(off(k) + 1:off(k + 1)) + 1; end
            else
                % VTK 4.x layout: sz entries of "m i_1 ... i_m"
                [arr, i] = numbers(lines, sz, i + 1);
                k = 1; cells = {};
                while k <= sz
                    m = arr(k); cells{end + 1} = arr(k + 1:k + m) + 1; k = k + 1 + m; %#ok<AGROW>
                end
            end
            v.cells = cells;
        case 'CELL_TYPES'
            cnt = str2double(parts{2}); [arr, i] = numbers(lines, cnt, i + 1); v.cell_types = arr(:)';
        case {'POINT_DATA', 'CELL_DATA'}
            section = key; v.([lower(key) '_count']) = str2double(parts{2}); i = i + 1;
        case {'SCALARS', 'VECTORS'}
            name = parts{2}; comp = 1; if strcmp(key, 'VECTORS'), comp = 3; end
            if strcmp(key, 'SCALARS') && numel(parts) > 3, comp = str2double(parts{4}); end
            i = i + 1;
            if strncmpi(strtrim(lines{i}), 'LOOKUP_TABLE', 12), i = i + 1; end
            if strcmp(section, 'POINT_DATA'), cnt = v.point_data_count; else, cnt = v.cell_data_count; end
            [arr, i] = numbers(lines, comp * cnt, i);
            v.data.(matlab.lang.makeValidName(name)) = shape_data(arr, comp, cnt, dims, strcmp(section, 'POINT_DATA'));
        case 'FIELD'
            nfield = str2double(parts{3}); i = i + 1;
            for q = 1:nfield
                while i <= n && isempty(strtrim(lines{i})), i = i + 1; end
                hp = strsplit(strtrim(lines{i})); name = hp{1}; comp = str2double(hp{2}); cnt = str2double(hp{3}); dtype = lower(hp{4});
                if strcmp(dtype, 'string')
                    i = i + 1; val = strtrim(lines{i}); i = i + 1;
                else
                    [val, i] = numbers(lines, comp * cnt, i + 1);
                    val = shape_data(val, comp, cnt, dims, strcmp(section, 'POINT_DATA'));
                end
                if isempty(section), v.field.(matlab.lang.makeValidName(name)) = val; else, v.data.(matlab.lang.makeValidName(name)) = val; end
            end
        otherwise
            i = i + 1;
    end
end
if strcmp(v.type, 'STRUCTURED_POINTS') && ~isempty(dims)
    v.x = v.origin(1) + v.spacing(1) * (0:dims(1) - 1); v.y = v.origin(2) + v.spacing(2) * (0:dims(2) - 1); v.z = v.origin(3) + v.spacing(3) * (0:dims(3) - 1);
end
end

function [arr, i] = numbers(lines, count, start)
% count numbers from the lines starting at index start; returns the next line index
arr = zeros(1, count); got = 0; i = start;
while got < count && i <= numel(lines)
    vals = sscanf(lines{i}, '%f')';
    take = min(numel(vals), count - got);
    arr(got + 1:got + take) = vals(1:take); got = got + take; i = i + 1;
end
end

function a = shape_data(arr, comp, cnt, dims, gridded)
if comp > 1
    a = reshape(arr, comp, cnt)';          % cnt x comp
else
    a = arr(:);
end
if gridded && ~isempty(dims)
    % x fastest, then y, then z in the file: reshape as [nx ny nz] and permute to [ny nx nz] (or [nz ny nx] squeezed)
    if comp > 1
        b = zeros([dims(2) dims(1) dims(3) comp]);
        for c = 1:comp
            b(:, :, :, c) = permute(reshape(a(:, c), dims(1), dims(2), dims(3)), [2 1 3]);
        end
        a = squeeze(b);
        if dims(3) == 1, a = reshape(a, dims(2), dims(1), comp); end
    else
        a = permute(reshape(a, dims(1), dims(2), dims(3)), [2 1 3]);
        a = squeeze(a);
    end
end
end

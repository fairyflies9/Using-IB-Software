function c = read_curve(path)
% READ_CURVE  VisIt's .curve file into a struct array c(k).name, c(k).x, c(k).y (chapter 29).
%   c = read_curve('pick.curve'); plot(c(1).x, c(1).y)
% A .curve file is plain text: a line '# name' before each curve, then one 'x y' pair per line
% (a pick through time of two variables gives two curves in one file). importdata(path) reads a file
% with one curve (the 2018 lecture's way); this reader keeps several apart. MATLAB or Octave.
fid = fopen(path, 'r');
if fid < 0, error('read_curve: cannot open %s', path); end
c = struct('name', {}, 'x', {}, 'y', {});
k = 0;
while true
    s = fgetl(fid);
    if ~ischar(s), break; end
    s = strtrim(s);
    if isempty(s), continue; end
    if s(1) == '#'
        k = k + 1; c(k).name = strtrim(s(2:end)); c(k).x = []; c(k).y = [];
    else
        v = sscanf(s, '%f');
        if k == 0, k = 1; c(1).name = 'curve'; c(1).x = []; c(1).y = []; end
        c(k).x(end + 1, 1) = v(1); c(k).y(end + 1, 1) = v(2);
    end
end
fclose(fid);
end

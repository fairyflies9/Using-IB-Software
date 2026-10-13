function v = read_input(path, key)
% READ_INPUT  A number from an IBAMR input file, e.g. read_input('input2d', 'DT').
% Finds the first line that starts with the key and an equals sign and returns
% the number after it; an expression (such as MU = 2.0*PI*...) is not evaluated.
txt = fileread(path);
tok = regexp(txt, ['(?m)^\s*' key '\s*=\s*([-+0-9.eE]+)'], 'tokens', 'once');
if isempty(tok)
    error('read_input:missing', '%s not found in %s', key, path);
end
v = str2double(tok{1});
end

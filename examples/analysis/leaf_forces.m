% leaf_forces.m: the drag and lift on the tethered leaf of example IB/03
% against time, from the F.NNNNN files, and the displacement of its two ends
% from the X.NNNNN files (chapter 11 of Using IB Software). MATLAB or Octave.
%
% Set run_folder below (or call leaf_forces from inside the run folder with
% run_folder = '.'), then run the script. It prints a table and writes
% leaf_forces.png. It needs read_hier_data.m and read_input.m from this folder.
%
% The F files hold the Lagrangian force at every point: the force the structure
% exerts on the fluid. Springs and beams pull their two or three points with
% forces that cancel in the sum, so the sum over the leaf is the tether force,
% and minus that sum is the force the fluid exerts on the leaf: its drag (x)
% and lift (y). The course normalized them as coefficients,
%     C_D = -sum(F_x) / (1/2 rho U^2 L),   C_L = -sum(F_y) / (1/2 rho U^2 L),
% with S = L in 2D (force per unit depth); chapter 8b's F' = F / (rho U^2 L)
% is the same without the 1/2.

run_folder = '.';                          % the folder with input2d and hier_data_IB2d
if exist('OCTAVE_VERSION', 'builtin'), graphics_toolkit('gnuplot'); end  %#ok<*UNRCH>  (Octave without a display)

dt  = read_input(fullfile(run_folder, 'input2d'), 'DT');
rho = read_input(fullfile(run_folder, 'input2d'), 'RHO');
U   = read_input(fullfile(run_folder, 'input2d'), 'V');   % the flow speed the boundary conditions tend to
L   = 0.1;                                                % the leaf's length (generate_mesh2d.m)

[t, F] = read_hier_data(fullfile(run_folder, 'hier_data_IB2d'), 'F', dt);
[t, X] = read_hier_data(fullfile(run_folder, 'hier_data_IB2d'), 'X', dt);

n = numel(t);
F_sum = zeros(n, 2); top = zeros(n, 2); bot = zeros(n, 2);
for k = 1:n
    F_sum(k, :) = sum(F{k}, 1);            % what the examples print as integral{F}
    top(k, :) = X{k}(1, :);                % point 0, the top end (y = +0.05 at t = 0)
    bot(k, :) = X{k}(end, :);              % the last point, the bottom end
end
CD = -F_sum(:, 1) / (0.5 * rho * U^2 * L);
CL = -F_sum(:, 2) / (0.5 * rho * U^2 * L);

fprintf('%-6s %10s %10s %10s %12s %12s\n', 't (s)', 'sum F_x', 'sum F_y', 'C_D', 'C_L', 'top x (m)');
for tt = [0.1 0.25 0.5 1.0 1.5 2.0]
    if t(end) >= tt - 1e-9
        [~, k] = min(abs(t - tt));
        fprintf('%-6.2f %10.4f %10.4f %10.3f %12.3f %12.4f\n', t(k), F_sum(k, 1), F_sum(k, 2), CD(k), CL(k), top(k, 1));
    end
end
k = floor(n / 2) + 1;                      % the same frames as the Python script's CD[n//2:]
fprintf('mean C_D over the second half of the run: %.3f (C_L %.3f)\n', mean(CD(k:end)), mean(CL(k:end)));

figure('visible', 'off');
subplot(1, 2, 1);
plot(t, CD, 'b-', 'LineWidth', 1.5); hold on;
plot(t, CL, 'r-', 'LineWidth', 1.5);
plot(t, tanh(2 * t).^2 * CD(end), 'k:');
xlabel('time (s)'); ylabel('force / (1/2 rho U^2 L)'); legend('C_D', 'C_L', 'C_D(2 s) tanh^2(2t)', 'Location', 'southeast'); grid on;
subplot(1, 2, 2);
plot(t, 100 * (top(:, 1) - top(1, 1)), 'b-', 'LineWidth', 1.5); hold on;
plot(t, 100 * (bot(:, 1) - bot(1, 1)), 'r-', 'LineWidth', 1.5);
plot(t, 100 * (top(:, 2) - top(1, 2)), 'b--');
xlabel('time (s)'); ylabel('displacement of the ends (cm)'); legend('top end, x', 'bottom end, x', 'top end, y', 'Location', 'northwest'); grid on;
try
    print('-dpng', '-r150', 'leaf_forces.png');
    disp('wrote leaf_forces.png');
catch err
    % Octave without a display (octave-cli over ssh) cannot render with its
    % default toolkit; the table above is the result, and the figure can be
    % made on a machine with a display or with the Python version.
    fprintf('could not write leaf_forces.png (%s)\n', err.message);
end


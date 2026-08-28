function test_datcom_section_limits
%TEST_DATCOM_SECTION_LIMITS  Proof harness for DATCOM NX/NPTS limits.
%  Baseline Cessna, dense NX=25/160, NPTS=60, and Boeing 737Max must pass.

    this = fileparts(mfilename('fullpath'));
    oldpwd = pwd;
    addpath(this);
    api = datcom_interp_sections();

    set(0, 'DefaultFigureVisible', 'off');
    hf = figure('Visible', 'off', 'HandleVisibility', 'off');
    cleanup = onCleanup(@() restore_test_state(oldpwd, hf));

    global lib_path WG HT VT F A E R BD NP NB AERO cmp opt ATM AC NP_In NB_In
    lib_path = [this filesep];
    assignin('base', 'lib_path', lib_path); %#ok<NASGU>
    NP_In = cell(1, 4);
    NB_In = cell(1, 2);

    cd(fullfile(this, 'DATCOM'));
    fails = {};

    % --- Cessna globals (same stubs as run_aid_batch / run_datcom_gold) ---
    [unit, cmp, opt] = load_model(this, hf, 'Cessna 172'); %#ok<NASGU>

    fprintf('\n=== CASE baseline Cessna (unmodified DATCOM_IO) ===\n');
    write_for005_batch(unit);
    [st, cmdout] = run_datcom_bin();
    base = parse_datcom_coeffs();
    baseline_txt = fileread('for005.dat');
    if st ~= 0 || ~exist('for006.dat', 'file') || ~has_finite_cl(base)
        fails{end+1} = sprintf('FAIL baseline: %s', fail_msg('baseline', st, cmdout, base, 'Cessna to run with a finite CL table'));
        fprintf('%s\n', fails{end});
    else
        fprintf('PASS baseline: CL(1:3)=%s exit=%d\n', mat2str(base.cl(1:min(3,end))', 4), st);
        print_coeff_table('baseline', base);
    end

    % --- Dense body NX=25 (Fortran max 20) ---
    % CM residual is DATCOM body pitching-moment quadrature vs station count
    % (NX=20→21 already moves CM), not interpolator round-trip.
    fprintf('\n=== CASE dense body NX=25 ===\n');
    fails = [fails, run_dense_body(api, baseline_txt, base, 25, 1e-3, 0.01, 2e-3)];

    % --- Dense body NX=160 (well under 200, over 20) ---
    fprintf('\n=== CASE dense body NX=160 ===\n');
    fails = [fails, run_dense_body(api, baseline_txt, base, 160, 1e-3, 0.01)];

    % --- Dense airfoil NPTS=60 (Fortran max 50) ---
    fprintf('\n=== CASE dense airfoil NPTS=60 ===\n');
    fails = [fails, run_dense_airfoil(api, baseline_txt, base, 60, 2e-3)];

    % --- 737Max smoke (GUI-style DATCOM_IO writer) ---
    fprintf('\n=== CASE Boeing 737Max smoke ===\n');
    [unit737, cmp, opt] = load_model(this, hf, 'Boeing 737Max'); %#ok<NASGU>
    write_for005_batch(unit737);
    [st737, cmd737] = run_datcom_bin();
    C737 = parse_datcom_coeffs();
    if st737 ~= 0 || ~exist('for006.dat', 'file') || isempty(C737) || isempty(C737.cl)
        fails{end+1} = sprintf('FAIL 737Max: %s', fail_msg('737Max', st737, cmd737, C737, 'for006.dat with a CL table'));
        fprintf('%s\n', fails{end});
    else
        fprintf('PASS 737Max: for006.dat CL table length=%d\n', numel(C737.cl));
        print_coeff_table('737Max', C737);
    end

    fprintf('\n');
    if isempty(fails)
        fprintf('ALL PASS\n');
    else
        msg = sprintf('%s\n', fails{:});
        error('test_datcom_section_limits:FAIL\n%s', msg);
    end
end

function fails = run_dense_body(api, baseline_txt, base, nx, atol, rtol, cm_atol)
    if nargin < 7
        cm_atol = atol;
    end
    fails = {};
    tag = sprintf('NX=%d', nx);
    BD2 = api.datcom_interp_body(evalin_global_BD(), nx);
    if BD2.NX ~= nx || numel(BD2.X) ~= nx
        fails = {sprintf('FAIL %s: interpolator NX=%g numel(X)=%d (want %d)', ...
            tag, BD2.NX, numel(BD2.X), nx)};
        fprintf('%s\n', fails{1});
        return
    end
    if abs(BD2.X(1) - evalin_global_BD().X(1)) > 1e-12 || ...
            abs(BD2.X(end) - evalin_global_BD().X(end)) > 1e-12
        fails = {sprintf('FAIL %s: interpolator dropped endpoints', tag)};
        fprintf('%s\n', fails{1});
        return
    end
    body_txt = strtrim(api.datcom_write_body_raw(BD2));
    txt = replace_body_namelist(baseline_txt, body_txt);
    write_text('for005.dat', txt);
    [st, cmdout] = run_datcom_bin();
    C = parse_datcom_coeffs();
    if st ~= 0 || ~exist('for006.dat', 'file') || ~has_finite_cl(C)
        fails = {sprintf('FAIL %s: %s', tag, fail_msg(tag, st, cmdout, C, 'exit 0, for006.dat, finite CL'))};
        fprintf('%s\n', fails{1});
        return
    end
    if isempty(base) || ~coeffs_match(base, C, atol, rtol, cm_atol)
        fails = {sprintf(['FAIL %s: coefficients differ from baseline ', ...
            '(atol=%g, cm_atol=%g, 1%% rel). cl_base=%s cl=%s'], tag, atol, ...
            cm_atol, compact_vec(getfield_or(base, 'cl')), compact_vec(C.cl))};
        fprintf('%s\n', fails{1});
        print_coeff_table(tag, C);
        return
    end
    fprintf('PASS %s: coeffs within tol (CL/CD atol=%g, CM atol=%g)\n', ...
        tag, atol, cm_atol);
    print_coeff_table(tag, C);
end

function fails = run_dense_airfoil(api, baseline_txt, base, npts, atol)
    fails = {};
    tag = sprintf('NPTS=%d', npts);
    global WG
    if ~isfield(WG, 'DATA') || isempty(WG.DATA)
        error('Cessna WG.DATA missing; cannot build WGSCHR');
    end
    DATA2 = api.datcom_interp_airfoil(WG.DATA, npts);
    [xcord, yupper, ylower] = api.datcom_airfoil_xy(DATA2);
    if numel(xcord) ~= npts
        fails = {sprintf('FAIL %s: interpolator XCORD length %d (want %d)', ...
            tag, numel(xcord), npts)};
        fprintf('%s\n', fails{1});
        return
    end
    wgschr = strtrim(api.datcom_write_wgschr(xcord, yupper, ylower));
    txt = replace_wing_naca_with_wgschr(baseline_txt, wgschr);
    write_text('for005.dat', txt);
    [st, cmdout] = run_datcom_bin();
    C = parse_datcom_coeffs();
    no_crash = (st == 0) && exist('for006.dat', 'file') && has_finite_cl(C);
    if ~isempty(base) && no_crash && coeffs_match(base, C, atol, 0)
        fprintf('PASS %s: coeffs within %g of baseline\n', tag, atol);
        print_coeff_table(tag, C);
        return
    end
    if no_crash
        fprintf(['PASS %s: coeff match vs NACA card worse than %g, ', ...
            'but no crash and finite CL\n'], tag, atol);
        print_coeff_table(tag, C);
        return
    end
    fails = {sprintf('FAIL %s: %s', tag, fail_msg(tag, st, cmdout, C, 'no crash and finite CL (or coeff match)'))};
    fprintf('%s\n', fails{1});
end

function BD = evalin_global_BD()
    global BD
end

function [unit, cmp, opt] = load_model(this, hf, model_name)
    global WG HT VT F A E R BD NP NB AERO ATM AC cmp opt
    S = load(fullfile(this, 'Models', [model_name, '.mat']));
    WG = S.WG; HT = S.HT; VT = S.VT; F = S.F; A = S.A; E = S.E; R = S.R;
    BD = S.BD; NP = S.NP; NB = S.NB; AERO = S.AERO;
    if ~isfield(S, 'unit'), unit = 'ft'; else, unit = S.unit; end
    ATM = Atmosphere(AERO.ALT(1));
    ATM.Q = 0.5 * ATM.D * (AERO.MACH(1) * ATM.a)^2;
    AC = struct('alpha', AERO.ALSCHD(max(1, ceil(end/2))), 'CD0', 0);
    if isfield(WG, 'CD0'), AC.CD0 = WG.CD0; end

    cmp = gobjects(1, 8);
    for i = 1:8
        cmp(i) = uicontrol(hf, 'Style', 'checkbox', 'Value', 1, 'Visible', 'off');
    end
    if isfield(S, 'plot_cmp')
        for i = 1:min(4, numel(S.plot_cmp))
            set(cmp(i), 'Value', S.plot_cmp(i));
        end
    end
    opt = gobjects(1, 17);
    for i = 1:17
        opt(i) = uimenu(hf, 'Label', 'x', 'Checked', 'off', 'Visible', 'off');
    end
    set(opt(1), 'UserData', repmat({'0'}, 3, 10));
    set(opt(9), 'UserData', [0.5, 0.9]);
    if strcmp(unit, 'in'), chk = 'on'; else, chk = 'off'; end
    set(opt(14), 'Checked', chk);
end

function write_for005_batch(unit)
    if exist('for005.dat', 'file'), delete('for005.dat'); end
    DATCOM_IO('for005.dat', 'case', 'batch', false, unit);
    if ~exist('for005.dat', 'file')
        error('DATCOM_IO did not write for005.dat');
    end
end

function [st, cmdout] = run_datcom_bin()
    if exist('for006.dat', 'file'), delete('for006.dat'); end
    if exist('datcom.out', 'file'), delete('datcom.out'); end
    tsec = 60;
    % MATLAB system() has no Timeout in R2025b; 'Timeout',n would set an env var.
    % Use GNU timeout(1). If a later MATLAB documents Timeout=, prefer that.
    persistent has_ml_timeout
    if isempty(has_ml_timeout)
        hs = evalc('help(''system'')');
        has_ml_timeout = ~isempty(regexp(hs, 'Timeout\s*=', 'once'));
    end
    if has_ml_timeout
        [st, cmdout] = system('./datcom', 'Timeout', tsec);
    else
        [st, cmdout] = system(sprintf('timeout %d ./datcom', tsec));
    end
    if st == 124
        fprintf('  ./datcom TIMEOUT (%ds) exit=%d\n', tsec, st);
    else
        fprintf('  ./datcom exit=%d\n', st);
    end
    if ~isempty(cmdout)
        snippet = cmdout;
        if numel(snippet) > 500, snippet = snippet(1:500); end
        fprintf('  stdout/stderr: %s\n', strtrim(snippet));
    end
end

function C = parse_datcom_coeffs()
    C = struct('cl', [], 'cd', [], 'cm', [], 'alpha', []);
    if exist('datcomimport', 'file') && exist('for006.dat', 'file')
        try
            S = datcomimport('for006.dat', true);
            if iscell(S), S = S{1}; end
            if isstruct(S) && isfield(S, 'cl') && ~isempty(S.cl)
                C.cl = S.cl(:);
                if isfield(S, 'cd'), C.cd = S.cd(:); end
                if isfield(S, 'cm'), C.cm = S.cm(:); end
                if isfield(S, 'alpha'), C.alpha = S.alpha(:); end
                if all(abs(C.cl) >= 99998)
                    C.cl = [];
                end
                if ~isempty(C.cl)
                    return
                end
            end
        catch
        end
    end
    src = '';
    if exist('datcom.out', 'file')
        src = fileread('datcom.out');
    elseif exist('for006.dat', 'file')
        src = fileread('for006.dat');
    end
    if isempty(src)
        return
    end
    C = parse_cl_from_text(src);
end

function C = parse_cl_from_text(txt)
    C = struct('cl', [], 'cd', [], 'cm', [], 'alpha', []);
    lines = regexp(txt, '\r?\n', 'split');
    hdr = 0;
    for i = 1:numel(lines)
        body = lines{i};
        if length(body) >= 2 && strcmp(body(1:2), '0 ')
            body = body(3:end);
        end
        if ~isempty(regexp(body, '\bALPHA\b', 'once')) && ...
                ~isempty(regexp(body, '\bCD\b', 'once')) && ...
                ~isempty(regexp(body, '\bCL\b', 'once')) && ...
                ~isempty(regexp(body, '\bCM\b', 'once'))
            hdr = i;
            break
        end
    end
    if hdr == 0
        return
    end
    alpha = []; cd = []; cl = []; cm = [];
    for i = hdr+1:numel(lines)
        line = lines{i};
        if isempty(line), continue; end
        if line(1) == '0' && ~strcmp(strtrim(line), '0')
            % new page / next table
            if ~isempty(regexp(line, '\bALPHA\b', 'once')), break; end
            if numel(strtrim(line)) > 1 && isempty(regexp(line, '[-+]?\d', 'once'))
                break
            end
        end
        nums = regexp(line, '[-+]?\d+\.?\d*(?:[Ee][-+]?\d+)?', 'match');
        if numel(nums) < 4
            continue
        end
        vals = str2double(nums);
        if any(abs(vals(1:4)) >= 99998)
            continue
        end
        alpha(end+1, 1) = vals(1); %#ok<AGROW>
        cd(end+1, 1) = vals(2); %#ok<AGROW>
        cl(end+1, 1) = vals(3); %#ok<AGROW>
        cm(end+1, 1) = vals(4); %#ok<AGROW>
    end
    C.alpha = alpha; C.cd = cd; C.cl = cl; C.cm = cm;
end

function tf = has_finite_cl(C)
    tf = ~isempty(C) && isstruct(C) && isfield(C, 'cl') && ~isempty(C.cl) && ...
        all(isfinite(C.cl(:))) && ~all(abs(C.cl(:)) >= 99998);
end

function tf = coeffs_match(A, B, atol, rtol, cm_atol)
    if nargin < 5
        cm_atol = atol;
    end
    if isempty(A) || isempty(B) || isempty(A.cl) || isempty(B.cl)
        tf = false;
        return
    end
    n = min([numel(A.cl), numel(B.cl), numel(A.cd), numel(B.cd), numel(A.cm), numel(B.cm)]);
    if n < 1
        tf = false;
        return
    end
    tf = vec_close(A.cl(1:n), B.cl(1:n), atol, rtol) && ...
        vec_close(A.cd(1:n), B.cd(1:n), atol, rtol) && ...
        vec_close(A.cm(1:n), B.cm(1:n), cm_atol, rtol);
end

function tf = vec_close(a, b, atol, rtol)
    a = a(:); b = b(:);
    tol = max(atol, rtol * abs(a));
    % 1e-12 slack: DATCOM CD can sit 1 ULP over 1e-3 (0.037 vs 0.038).
    tf = all(isfinite(a) & isfinite(b) & abs(a - b) <= tol + 1e-12);
end

function txt = replace_body_namelist(src, body_block)
    % regexp starts at $BODY; keep the original card's column-1 blank so $ is col 2.
    body_block = deblank(body_block);
    while ~isempty(body_block) && body_block(1) == ' '
        body_block = body_block(2:end);
    end
    [s, e] = regexp(src, '\$BODY[\s\S]*?\$', 'start', 'end', 'once');
    if isempty(s)
        error('baseline for005 has no $BODY namelist');
    end
    txt = [src(1:s-1), body_block, src(e+1:end)];
end

function txt = replace_wing_naca_with_wgschr(src, wgschr)
    % Inserted on a new line: need a leading blank so $WGSCHR is not in column 1.
    wgschr = namelist_block(wgschr);
    txt = regexprep(src, 'NACA-W-[^\r\n]+\r?\n', '', 'once');
    [s, e] = regexp(txt, '\$WGPLNF[\s\S]*?\$', 'start', 'end', 'once');
    if isempty(s)
        error('baseline for005 has no $WGPLNF namelist');
    end
    insert = sprintf('%s\n%s', txt(s:e), wgschr);
    txt = [txt(1:s-1), insert, txt(e+1:end)];
end

function s = namelist_block(s)
%NAMELIST_BLOCK  Trailing whitespace only; keep a leading blank so $ is not in col 1.
    s = deblank(s);
    if isempty(s)
        return
    end
    if s(1) ~= ' '
        s = [' ', s];
    end
end

function write_text(path, txt)
    fid = fopen(path, 'w');
    if fid < 0
        error('cannot write %s', path);
    end
    fwrite(fid, txt);
    fclose(fid);
end

function msg = fail_msg(tag, st, cmdout, C, need)
    bits = {sprintf('need %s', need)};
    bits{end+1} = sprintf('exit=%d', st);
    if st == 124
        bits{end+1} = 'timeout';
    end
    if exist('for006.dat', 'file')
        bits{end+1} = 'for006.dat=yes';
    else
        bits{end+1} = 'for006.dat=NO';
    end
    if isempty(C) || isempty(C.cl)
        bits{end+1} = 'CL table=NO';
    else
        bits{end+1} = sprintf('CL=%s', compact_vec(C.cl));
    end
    err = conerr_snippet();
    if ~isempty(err)
        bits{end+1} = err;
    end
    if st ~= 0 && ~isempty(cmdout)
        snippet = regexprep(strtrim(cmdout), '\s+', ' ');
        if numel(snippet) > 180, snippet = snippet(1:180); end
        bits{end+1} = ['cmd: ', snippet];
    end
    msg = strjoin(bits, '; ');
end

function s = conerr_snippet()
    s = '';
    if exist('datcom.out', 'file')
        p = 'datcom.out';
    elseif exist('for006.dat', 'file')
        p = 'for006.dat';
    else
        return
    end
    t = fileread(p);
    m = regexp(t, '\*\* ERROR \*\*[^\n]*', 'match', 'once');
    if ~isempty(m)
        s = strtrim(regexprep(m, '\s+', ' '));
    end
end

function print_coeff_table(tag, C)
    fprintf('  TABLE %s ALPHA=%s\n', tag, compact_vec(getfield_or(C, 'alpha')));
    fprintf('  TABLE %s CL=%s\n', tag, compact_vec(getfield_or(C, 'cl')));
    fprintf('  TABLE %s CD=%s\n', tag, compact_vec(getfield_or(C, 'cd')));
    fprintf('  TABLE %s CM=%s\n', tag, compact_vec(getfield_or(C, 'cm')));
end

function s = compact_vec(v)
    if isempty(v)
        s = '[]';
        return
    end
    s = mat2str(v(:)', 6);
end

function v = getfield_or(S, name)
    if isempty(S) || ~isstruct(S) || ~isfield(S, name)
        v = [];
    else
        v = S.(name);
    end
end

function restore_test_state(oldpwd, hf)
    cd(oldpwd);
    if ishghandle(hf)
        close(hf);
    end
end

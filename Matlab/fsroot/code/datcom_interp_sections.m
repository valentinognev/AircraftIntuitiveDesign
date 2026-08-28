function api = datcom_interp_sections()
%DATCOM_INTERP_SECTIONS  Body/airfoil interpolators for DATCOM section limits.
%  MATLAB exposes only the first function in a file, so this returns handles:
%    api.datcom_interp_body(BD, n)
%    api.datcom_airfoil_xy(DATA)
%    api.datcom_interp_airfoil(DATA, npts)
%    api.datcom_write_body_raw(BD)
%    api.datcom_write_wgschr(xcord, yupper, ylower)
%    api.clamp_section_npts(xcord, yupper, ylower, cap)
    api = struct();
    api.datcom_interp_body = @datcom_interp_body;
    api.datcom_airfoil_xy = @datcom_airfoil_xy;
    api.datcom_interp_airfoil = @datcom_interp_airfoil;
    api.datcom_write_body_raw = @datcom_write_body_raw;
    api.datcom_write_wgschr = @datcom_write_wgschr;
    api.clamp_section_npts = @clamp_section_npts;
end

function BD2 = datcom_interp_body(BD, n)
%DATCOM_INTERP_BODY  Interpolate body stations to n points along X (keep ends).
    if n < 2
        error('datcom_interp_body: n must be >= 2');
    end
    BD2 = BD;
    [x, zu, zl, r, p, s] = body_columns(BD);
    xnew = linspace(x(1), x(end), n);
    zu2 = interp1(x, zu, xnew, 'linear');
    zl2 = interp1(x, zl, xnew, 'linear');
    r2 = interp1(x, r, xnew, 'linear');
    p2 = interp1(x, p, xnew, 'linear');
    s2 = interp1(x, s, xnew, 'linear');
    if isrow_like(BD.X)
        BD2.X = xnew; BD2.ZU = zu2; BD2.ZL = zl2;
        BD2.R = r2; BD2.P = p2; BD2.S = s2;
    else
        BD2.X = xnew(:); BD2.ZU = zu2(:); BD2.ZL = zl2(:);
        BD2.R = r2(:); BD2.P = p2(:); BD2.S = s2(:);
    end
    BD2.NX = n;
end

function [xcord, yupper, ylower] = datcom_airfoil_xy(DATA)
%DATCOM_AIRFOIL_XY  Split closed TE→lower→LE→upper→TE loop into LE→TE halves.
%  Positive-mean half is YUPPER. XCORD is monotonic 0→1, length floor(N/2).
    xy = as_xy(DATA);
    N = size(xy, 1);
    n = floor(N / 2);
    if n < 2
        error('datcom_airfoil_xy: airfoil DATA needs at least 4 points');
    end
    h1 = flipud(xy(1:n, :));
    h2 = xy(end-n+1:end, :);
    if mean(h1(:, 2)) >= mean(h2(:, 2))
        up = h1; lo = h2;
    else
        up = h2; lo = h1;
    end
    [xu, yu] = monotonic_le_te(up(:, 1), up(:, 2));
    [xl, yl] = monotonic_le_te(lo(:, 1), lo(:, 2));
    xcord = xu(:);
    yupper = yu(:);
    ylower = interp1(xl, yl, xcord, 'linear', 'extrap');
    ylower = ylower(:);
end

function DATA2 = datcom_interp_airfoil(DATA, npts)
%DATCOM_INTERP_AIRFOIL  Resample upper/lower independently to npts x-stations.
%  Output is a closed TE→lower→LE→upper→TE loop with 2*npts rows (LE duplicated)
%  so floor(N/2)==npts.
    if npts < 2
        error('datcom_interp_airfoil: npts must be >= 2');
    end
    [x0, yu0, yl0] = datcom_airfoil_xy(DATA);
    xnew = linspace(0, 1, npts)';
    yu = interp1(x0, yu0, xnew, 'linear', 'extrap');
    yl = interp1(x0, yl0, xnew, 'linear', 'extrap');
    x = [flipud(xnew); xnew];
    y = [flipud(yl); yu];
    DATA2 = [x, y];
    if iscell(DATA)
        DATA2 = {DATA2};
    end
end

function s = datcom_write_body_raw(BD)
%DATCOM_WRITE_BODY_RAW  $BODY namelist with no 18-point downsample.
%  Continuation lines wrap at <=80 columns, 10 values/line.
    [x, zu, zl, r, p, sval] = body_columns(BD);
    nx = numel(x);
    if isfield(BD, 'NX') && ~isempty(BD.NX)
        nx = BD.NX;
    end
    if min(sval) < 0.01
        sfmt = '%.3f,';
    else
        sfmt = '%.2f,';
    end
    lines = {sprintf(' $BODY NX=%.1f,ITYPE=1.0,', nx)};
    lines{end+1} = format_namelist_array('X', x, '%.2f,');
    lines{end+1} = format_namelist_array('ZU', zu, '%.2f,');
    lines{end+1} = format_namelist_array('ZL', zl, '%.2f,');
    lines{end+1} = format_namelist_array('R', r, '%.2f,');
    lines{end+1} = format_namelist_array('P', p, '%.2f,');
    slines = format_namelist_array('S', sval, sfmt);
    slines = [slines, '$'];
    lines{end+1} = slines;
    s = sprintf('%s\n', lines{:});
end

function s = datcom_write_wgschr(xcord, yupper, ylower)
%DATCOM_WRITE_WGSCHR  $WGSCHR namelist, 10 values/line, wrap at <=80 columns.
%  NPTS clamped to 60 (SECI /IWING/ size); downsample keeps XCORD 0 and 1.
    [xcord, yupper, ylower] = clamp_section_npts(xcord, yupper, ylower, 60);
    npts = numel(xcord);
    lines = {sprintf(' $WGSCHR TYPEIN=1.0,NPTS=%.1f,', npts)};
    lines{end+1} = format_namelist_array('XCORD', xcord, '%.3f,');
    lines{end+1} = format_namelist_array('YUPPER', yupper, '%.3f,');
    yline = format_namelist_array('YLOWER', ylower, '%.3f,');
    tail = 'CLMAX=1.5$';
    if numel(yline) + numel(tail) <= 80
        yline = [yline, tail];
    else
        yline = sprintf('%s\n  %s', yline, tail);
    end
    lines{end+1} = yline;
    s = sprintf('%s\n', lines{:});
end

function [x, zu, zl, r, p, s] = body_columns(BD)
    x = double(BD.X(:))';
    zu = double(BD.ZU(:))';
    zl = double(BD.ZL(:))';
    r = double(BD.R(:))';
    if isfield(BD, 'P') && ~isempty(BD.P)
        p = double(BD.P(:))';
    else
        p = ones(size(x));
    end
    s = double(BD.S(:))';
    [x, ord] = unique(x, 'stable');
    zu = zu(ord); zl = zl(ord); r = r(ord); p = p(ord); s = s(ord);
    if any(diff(x) <= 0)
        [x, ord] = sort(x);
        zu = zu(ord); zl = zl(ord); r = r(ord); p = p(ord); s = s(ord);
    end
    n = min([numel(x), numel(zu), numel(zl), numel(r), numel(p), numel(s)]);
    x = x(1:n); zu = zu(1:n); zl = zl(1:n); r = r(1:n); p = p(1:n); s = s(1:n);
    if n < 2
        error('datcom_interp_body: need at least 2 unique X stations');
    end
end

function xy = as_xy(DATA)
    if iscell(DATA)
        DATA = DATA{1};
    end
    xy = double(DATA);
    if size(xy, 2) < 2
        error('datcom_airfoil_xy: DATA must be N-by-2');
    end
end

function [x, y] = monotonic_le_te(x, y)
    x = x(:); y = y(:);
    if x(1) > x(end)
        x = flipud(x);
        y = flipud(y);
    end
    [x, ord] = unique(x, 'stable');
    y = y(ord);
    if any(diff(x) <= 0)
        [x, ord] = sort(x);
        y = y(ord);
    end
end

function tf = isrow_like(v)
    tf = isrow(v) || isscalar(v);
end

function [xc, yu, yl] = clamp_section_npts(xc, yu, yl, cap)
%CLAMP_SECTION_NPTS  Downsample XCORD/YUPPER/YLOWER together; keep LE (0) and TE (1).
    xc = xc(:); yu = yu(:); yl = yl(:);
    n = min([numel(xc), numel(yu), numel(yl)]);
    xc = xc(1:n); yu = yu(1:n); yl = yl(1:n);
    if n <= cap
        return
    end
    xnew = linspace(xc(1), xc(end), cap)';
    yu = interp1(xc, yu, xnew, 'linear');
    yl = interp1(xc, yl, xnew, 'linear');
    xc = xnew;
end

function s = format_namelist_array(name, vals, fmt)
%FORMAT_NAMELIST_ARRAY  10 values/line, wrap at <=80 columns, 2-space indent.
    vals = vals(:)';
    header = sprintf('  %s=', name);
    chunks = {};
    line = header;
    n_on_line = 0;
    for i = 1:numel(vals)
        tok = sprintf(fmt, vals(i));
        would = numel(line) + numel(tok);
        if n_on_line > 0 && (n_on_line >= 10 || would > 80)
            chunks{end+1} = line; %#ok<AGROW>
            line = ['  ', tok];
            n_on_line = 1;
        else
            line = [line, tok];
            n_on_line = n_on_line + 1;
        end
    end
    chunks{end+1} = line;
    s = strjoin(chunks, sprintf('\n'));
end

function debug_dump_tornado(model_name, out_name)
set(0,'DefaultFigureVisible','off');
this = fileparts(mfilename('fullpath'));
addpath(this, fullfile(this,'Tornado'));
global WG HT VT F A E R NP NB AERO Results cmp opt ATM AC
S = load(fullfile(this,'Models',[model_name '.mat']));
WG=S.WG; HT=S.HT; VT=S.VT; F=S.F; A=S.A; E=S.E; R=S.R; BD=S.BD;
NP=S.NP; NB=S.NB; AERO=S.AERO;
ATM = Atmosphere(AERO.ALT(1));
AC = struct('alpha', AERO.ALSCHD(max(1,ceil(numel(AERO.ALSCHD)/2))), 'CD0', 0);
if isfield(WG,'CD0'), AC.CD0 = WG.CD0; end

hf = figure('Visible','off','HandleVisibility','off');
cmp = gobjects(1,8);
for i=1:8
    cmp(i) = uicontrol(hf,'Style','checkbox','Value',1,'Visible','off');
end
if isfield(S,'plot_cmp')
    for i=1:min(4,numel(S.plot_cmp)), set(cmp(i),'Value',S.plot_cmp(i)); end
end

mesh = {'10','5'};
[geo,state] = Tornado_IO(mesh);
[lattice,ref] = fLattice_setup2(geo,state,0);
[tres, errMsg] = deal([], '');
try
    raw = solver(state,geo,lattice);
    tres = coeff_create3(raw,lattice,state,ref,geo);
catch ME
    errMsg = ME.message;
end
if ~isempty(errMsg), fprintf('solver err: %s\n', errMsg); end

root = fileparts(fileparts(fileparts(this)));
out_dir = fullfile(root,'Results','debug');
if ~exist(out_dir,'dir'), mkdir(out_dir); end
out = fullfile(out_dir, out_name);
save(out, 'geo','state','ref','AC','AERO','F','A','E','lattice','tres');
fprintf('model=%s AC.alpha=%g state.alpha_deg=%g', model_name, AC.alpha, state.alpha*180/pi);
if ~isempty(tres), fprintf(' CL=%g', tres.CL); end
fprintf('\n');
if isfield(state,'AS')
    fprintf('state.AS=%g state.rho=%g npan=%d nwing=%d\n', state.AS, state.rho, size(lattice.XYZ,1), geo.nwing);
else
    fprintf('state fields: '); disp(fieldnames(state));
    fprintf('npan=%d nwing=%d\n', size(lattice.XYZ,1), geo.nwing);
end
for k=1:geo.nwing
    fv = geo.flap_vector(k,:)*180/pi;
    fprintf('wing %d flap_vector deg: ', k); fprintf('%.2f ', fv); fprintf('\n');
end
close(hf);
end

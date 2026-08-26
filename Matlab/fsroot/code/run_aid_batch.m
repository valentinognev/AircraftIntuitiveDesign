function run_aid_batch(model_name, solver)
%RUN_AID_BATCH  Gold solver dump for one aircraft .mat
% model_name e.g. 'Cessna 172' (no extension)
% solver 'datcom' | 'tornado' | 'avl' | (future: 'all')
if nargin < 1, model_name = 'Cessna 172'; end
if nargin < 2, solver = 'datcom'; end
switch lower(solver)
    case 'datcom'
        run_datcom_gold(model_name);
    case 'tornado'
        run_tornado_gold(model_name);
    case 'avl'
        run_avl_gold(model_name);
    otherwise
        error('not implemented');
end
end

function run_datcom_gold(model_name)
this = fileparts(mfilename('fullpath'));
addpath(this);
global lib_path WG HT VT F A E R BD NP NB AERO Results cmp opt ATM AC
lib_path = [this filesep];
assignin('base','lib_path',lib_path); %#ok<NASGU>

root = fileparts(fileparts(fileparts(this))); % AircraftIntuitiveDesign
out_dir = fullfile(root,'Results','matlab',model_name);
if ~exist(out_dir,'dir'), mkdir(out_dir); end

S = load(fullfile(this,'Models',[model_name,'.mat']));
WG=S.WG; HT=S.HT; VT=S.VT; F=S.F; A=S.A; E=S.E; R=S.R; BD=S.BD;
NP=S.NP; NB=S.NB; AERO=S.AERO;
if ~isfield(S,'unit'), unit='ft'; else, unit=S.unit; end
Results = cell(1,4);
ATM = Atmosphere(AERO.ALT(1));
ATM.Q = 0.5*ATM.D*(AERO.MACH(1)*ATM.a)^2;
AC = struct('alpha',AERO.ALSCHD(max(1,ceil(end/2))),'CD0',0);
if isfield(WG,'CD0'), AC.CD0 = WG.CD0; end

set(0,'DefaultFigureVisible','off');
hf = figure('Visible','off','HandleVisibility','off');
cmp = gobjects(1,8); %#ok<NASGU>
for i=1:8
    cmp(i) = uicontrol(hf,'Style','checkbox','Value',1,'Visible','off');
end
if isfield(S,'plot_cmp')
    for i=1:min(4,numel(S.plot_cmp)), set(cmp(i),'Value',S.plot_cmp(i)); end
end
opt = gobjects(1,17);
for i=1:17
    opt(i) = uimenu(hf,'Label','x','Checked','off','Visible','off');
end
set(opt(1),'UserData',repmat({'0'},3,10));
set(opt(9),'UserData',[0.5,0.9]);
set(opt(14),'Checked',onoff(strcmp(unit,'in')));

status = struct('datcom','failed','error',{{}});

try
    cd(fullfile(this,'DATCOM'));
    delete('*.dat');
    DATCOM_IO('for005.dat','case','batch',false,unit);
    [st,cmdout] = system('./datcom'); %#ok<ASGLU>
    if exist('for005.dat','file'), copyfile('for005.dat',fullfile(out_dir,'for005.dat')); end
    if exist('datcom.out','file'), copyfile('datcom.out',fullfile(out_dir,'datcom.out')); end
    if exist('for006.dat','file') && exist('datcomimport','file')
        Results{1} = datcomimport('for006.dat',true);
        if iscell(Results{1}), Results{1}=Results{1}{1}; end
        if isfield(Results{1},'cl')
            status.datcom = 'ok';
            write_json(fullfile(out_dir,'datcom.json'), strip_datcom(Results{1}));
        end
    end
catch ME
    status.error{end+1} = ['datcom: ' ME.message];
end
cd(this);

write_json(fullfile(out_dir,'status.json'), status);
close(hf);
fprintf('batch %s datcom=%s\n', model_name, status.datcom);
end

function run_tornado_gold(model_name)
set(0,'DefaultFigureVisible','off');
this = fileparts(mfilename('fullpath'));
addpath(this, fullfile(this,'Tornado'));
global lib_path WG HT VT F A E R BD NP NB AERO Results cmp opt ATM AC
lib_path = [this filesep];
assignin('base','lib_path',lib_path); %#ok<NASGU>

root = fileparts(fileparts(fileparts(this))); % AircraftIntuitiveDesign
out_dir = fullfile(root,'Results','matlab',model_name);
if ~exist(out_dir,'dir'), mkdir(out_dir); end

S = load(fullfile(this,'Models',[model_name,'.mat']));
WG=S.WG; HT=S.HT; VT=S.VT; F=S.F; A=S.A; E=S.E; R=S.R; BD=S.BD;
NP=S.NP; NB=S.NB; AERO=S.AERO;
if ~isfield(S,'unit'), unit='ft'; else, unit=S.unit; end
Results = cell(1,4);
ATM = Atmosphere(AERO.ALT(1));
ATM.Q = 0.5*ATM.D*(AERO.MACH(1)*ATM.a)^2;
AC = struct('alpha',AERO.ALSCHD(max(1,ceil(end/2))),'CD0',0);
if isfield(WG,'CD0'), AC.CD0 = WG.CD0; end

hf = figure('Visible','off','HandleVisibility','off');
cmp = gobjects(1,8); %#ok<NASGU>
for i=1:8
    cmp(i) = uicontrol(hf,'Style','checkbox','Value',1,'Visible','off');
end
if isfield(S,'plot_cmp')
    for i=1:min(4,numel(S.plot_cmp)), set(cmp(i),'Value',S.plot_cmp(i)); end
end
opt = gobjects(1,17);
for i=1:17
    opt(i) = uimenu(hf,'Label','x','Checked','off','Visible','off');
end
set(opt(1),'UserData',repmat({'0'},3,10));
set(opt(9),'UserData',[0.5,0.9]);
set(opt(14),'Checked',onoff(strcmp(unit,'in')));

status_path = fullfile(out_dir,'status.json');
if isfile(status_path)
    status = jsondecode(fileread(status_path));
else
    status = struct();
end
status.error = normalize_errors(status);
status.error = status.error(~cellfun(@(s) strncmp(s,'tornado: ',9), status.error));
status.tornado = 'failed';

try
    mesh = {'10','5'};
    [geo,state] = Tornado_IO(mesh);
    [lattice,ref] = fLattice_setup2(geo,state,0);
    tres = solver(state,geo,lattice);
    if isempty(tres)
        error('solver returned empty results');
    end
    tres = coeff_create3(tres,lattice,state,ref,geo);
    Results{3} = tres;
    status.tornado = 'ok';
    write_json(fullfile(out_dir,'tornado.json'), strip_tornado(tres));
catch ME
    status.error{end+1} = ['tornado: ' ME.message];
end

write_json(status_path, status);
close(hf);
fprintf('batch %s tornado=%s\n', model_name, status.tornado);
end

function run_avl_gold(model_name)
set(0,'DefaultFigureVisible','off');
this = fileparts(mfilename('fullpath'));
addpath(this, fullfile(this,'Tornado'), fullfile(this,'AVL'));
global lib_path WG HT VT F A E R BD NP NB AERO Results cmp opt ATM AC
lib_path = [this filesep];
assignin('base','lib_path',lib_path); %#ok<NASGU>

root = fileparts(fileparts(fileparts(this))); % AircraftIntuitiveDesign
out_dir = fullfile(root,'Results','matlab',model_name);
if ~exist(out_dir,'dir'), mkdir(out_dir); end

S = load(fullfile(this,'Models',[model_name,'.mat']));
WG=S.WG; HT=S.HT; VT=S.VT; F=S.F; A=S.A; E=S.E; R=S.R; BD=S.BD;
NP=S.NP; NB=S.NB; AERO=S.AERO;
if ~isfield(S,'unit'), unit='ft'; else, unit=S.unit; end
Results = cell(1,4);
ATM = Atmosphere(AERO.ALT(1));
ATM.Q = 0.5*ATM.D*(AERO.MACH(1)*ATM.a)^2;
AC = struct('alpha',AERO.ALSCHD(max(1,ceil(end/2))),'CD0',0);
if isfield(WG,'CD0'), AC.CD0 = WG.CD0; end

hf = figure('Visible','off','HandleVisibility','off');
cmp = gobjects(1,8); %#ok<NASGU>
for i=1:8
    cmp(i) = uicontrol(hf,'Style','checkbox','Value',1,'Visible','off');
end
if isfield(S,'plot_cmp')
    for i=1:min(4,numel(S.plot_cmp)), set(cmp(i),'Value',S.plot_cmp(i)); end
end
opt = gobjects(1,17);
for i=1:17
    opt(i) = uimenu(hf,'Label','x','Checked','off','Visible','off');
end
set(opt(1),'UserData',repmat({'0'},3,10));
set(opt(9),'UserData',[0.5,0.9]);
set(opt(14),'Checked',onoff(strcmp(unit,'in')));

status_path = fullfile(out_dir,'status.json');
if isfile(status_path)
    status = jsondecode(fileread(status_path));
else
    status = struct();
end
status.error = normalize_errors(status);
status.error = status.error(~cellfun(@(s) strncmp(s,'avl: ',5), status.error));
status.avl = 'failed';

try
    mesh = {'10','10'};
    [geo,state] = Tornado_IO(mesh);
    avl_run = fullfile(this,'AVL','run');
    st_old = fullfile(avl_run,'geometry.st');
    sb_old = fullfile(avl_run,'geometry.sb');
    if isfile(st_old), delete(st_old); end
    if isfile(sb_old), delete(sb_old); end
    avl_path = AVL_IO(mesh,geo,state,false);
    stfile = fullfile(avl_path,'geometry.st');
    if exist(stfile,'file')
        Results{4} = parseST(stfile);
        status.avl = 'ok';
        write_json(fullfile(out_dir,'avl.json'), Results{4});
        copyfile(stfile, fullfile(out_dir,'geometry.st'));
        copyfile(fullfile(avl_path,'geometry.avl'), fullfile(out_dir,'geometry.avl'));
    else
        error('geometry.st not found in %s', avl_path);
    end
catch ME
    status.error{end+1} = ['avl: ' ME.message];
end

write_json(status_path, status);
close(hf);
fprintf('batch %s avl=%s\n', model_name, status.avl);
end

function errs = normalize_errors(status)
if ~isfield(status,'error') || isempty(status.error)
    errs = {};
elseif ischar(status.error)
    errs = {status.error};
elseif isstring(status.error)
    errs = cellstr(status.error);
elseif iscell(status.error)
    errs = status.error;
else
    errs = {};
end
end

function s = onoff(tf)
if tf, s='on'; else, s='off'; end
end

function write_json(path, obj)
fid = fopen(path,'w'); fwrite(fid, jsonencode(obj,'PrettyPrint',true)); fclose(fid);
end

function D = strip_datcom(S)
% function strip_datcom - keep DATCOM coefficient fields for JSON export
keep = {'alpha','cl','cd','cm','cn','ca','cla','cma','cyb','cnb','clb','xcg','mach','alt'};
D = struct();
for i=1:numel(keep)
    if isfield(S,keep{i}), D.(keep{i}) = S.(keep{i}); end
end
end

function D = strip_tornado(S)
keep = {'CL','CD','Cm','CY','Cl','Cn','CL_a','Cm_a','CY_b','Cl_b','Cn_b','CL0','Cm0'};
D = struct();
for i=1:numel(keep)
    if isfield(S,keep{i}), D.(keep{i}) = S.(keep{i}); end
end
end

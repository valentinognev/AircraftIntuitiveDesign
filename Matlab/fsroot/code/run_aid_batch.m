function run_aid_batch(model_name, solver)
%RUN_AID_BATCH  Gold solver dump for one aircraft .mat
% model_name e.g. 'Cessna 172' (no extension)
% solver 'datcom' | (future: 'tornado', 'avl', 'all')
if nargin < 1, model_name = 'Cessna 172'; end
if nargin < 2, solver = 'datcom'; end
switch lower(solver)
    case 'datcom'
        run_datcom_gold(model_name);
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
    DATCOM_IO('for005.dat','case','DATCOM',false,unit);
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

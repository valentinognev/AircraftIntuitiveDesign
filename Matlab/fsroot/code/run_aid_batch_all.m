function run_aid_batch_all
this = fileparts(mfilename('fullpath'));
d = dir(fullfile(this,'Models','*.mat'));
summary = struct('name',{},'datcom',{},'tornado',{},'avl',{});
root = fileparts(fileparts(fileparts(this)));
for i=1:numel(d)
    name = d(i).name(1:end-4);
    fprintf('==== %s ====\n', name);
    stpath = fullfile(root,'Results','matlab',name,'status.json');
    skip = false;
    if exist(stpath,'file')
        st = jsondecode(fileread(stpath));
        if isfield(st,'datcom') && isfield(st,'tornado') && isfield(st,'avl')
            skip = true;
            fprintf('SKIP %s (status.json present)\n', name);
        end
    end
    if ~skip
        try
            run_aid_batch(name);
        catch ME
            fprintf('FATAL %s: %s\n', name, ME.message);
        end
    end
    row.name = name; row.datcom='missing'; row.tornado='missing'; row.avl='missing';
    if exist(stpath,'file')
        st = jsondecode(fileread(stpath));
        row.datcom = st.datcom; row.tornado = st.tornado; row.avl = st.avl;
    end
    summary(end+1) = row; %#ok<AGROW>
end
matlab_dir = fullfile(root,'Results','matlab');
if ~exist(matlab_dir,'dir'), mkdir(matlab_dir); end
fid = fopen(fullfile(matlab_dir,'_summary.json'),'w');
fwrite(fid, jsonencode(summary,'PrettyPrint',true)); fclose(fid);
end

function run_aid_batch(model_name)
error('not implemented');
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

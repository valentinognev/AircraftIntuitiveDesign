function debug_lattice_stages(model_name)
set(0,'DefaultFigureVisible','off');
this = fileparts(mfilename('fullpath'));
addpath(this, fullfile(this,'Tornado'));
global WG HT VT F A E R NP NB AERO cmp opt ATM AC
S = load(fullfile(this,'Models',[model_name '.mat']));
WG=S.WG; HT=S.HT; VT=S.VT; F=S.F; A=S.A; E=S.E; R=S.R; NP=S.NP; NB=S.NB; AERO=S.AERO;
ATM = Atmosphere(AERO.ALT(1));
AC = struct('alpha', AERO.ALSCHD(max(1,ceil(numel(AERO.ALSCHD)/2))), 'CD0', 0);
hf = figure('Visible','off','HandleVisibility','off');
cmp = gobjects(1,8);
for i=1:8
    cmp(i) = uicontrol(hf,'Style','checkbox','Value',1,'Visible','off');
end
[geo,state] = Tornado_IO({'10','5'});
[n,m] = find(geo.flapped');
fprintf('find order %s:\n', model_name);
for k = 1:numel(n)
    fprintf('k=%d n=%d m=%d fv=%g deg\n', k, n(k), m(k), geo.flap_vector(m(k),n(k))*180/pi);
end
[lattice,ref] = fLattice_setup2(geo,state,0);
geo0 = geo;
geo0.flap_vector = zeros(size(geo.flap_vector));
geo0.flapped = zeros(size(geo.flapped));
[lattice0,ref0] = fLattice_setup2(geo0,state,0);
root = fileparts(fileparts(fileparts(this)));
out = fullfile(root,'Results','debug',['matlab_' lower(strrep(model_name,'-','_')) '_lattice.mat']);
save(out, 'lattice0', 'lattice', 'geo', 'state');
fprintf('post npan=%d pre0 npan=%d maxdiff=%g\n', size(lattice.XYZ,1), size(lattice0.XYZ,1), max(abs(lattice0.XYZ(:)-lattice.XYZ(:))));
close(hf);
end

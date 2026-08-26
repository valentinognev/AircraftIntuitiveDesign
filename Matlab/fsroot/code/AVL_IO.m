function AVL_path = AVL_IO(mesh,geo,state,check_io)
global lib_path

%CaseID
CaseID = 'geometry';

%Discretization
nj = str2double(mesh{1});
ni = str2double(mesh{2});

%Enter Run Directory
current_path = pwd;
cd(fullfile(lib_path,'AVL','run'))

%Write Geometry/Input fid
Write_Input(CaseID,geo,ni,nj)

%Write Case/Run fid
Write_Case(CaseID,state)

%Run AVL using
if ispc
    if check_io
      	system(['Notepad ',CaseID,'.avl']);
        system(['Notepad ',CaseID,'.run']);
        %!Notepad([CaseID,'.run'])
    end
    system(['avl.exe',' < ',CaseID,'.run']);
else
    if check_io
      	type([CaseID,'.avl'])
        type([CaseID,'.run'])
    end
    setenv('DYLD_LIBRARY_PATH', '/usr/local/bin:/opt/local/lib:')
    system(['./avl3.35',' < ',CaseID,'.run']);
end

%Check Outputs
file = dir([CaseID,'.st']); AVL_path = file.folder;

%Return to Main Directory
cd(current_path)

end

function Write_Input(CaseID,geo,ni,nj)
global AERO WG AC BD cmp

%Name File
fid=fopen([CaseID,'.avl'],'wt');
fprintf(fid,'%s\n',CaseID);

%Mach Number
fprintf(fid,'\n#MACH\n');
fprintf(fid,'%.6f\n',AERO.MACH);

%Moments of Inertia
fprintf(fid,'\n#IYsym IZsym Zsym\n');
fprintf(fid,'%.1f %.1f %.1f\n',0,0,0); %Symmetry

%Reference Dimensions
fprintf(fid,'\n#Sref Cref Bref\n');
fprintf(fid,'%.4f %.4f %.4f\n',WG.S,WG.cbar,WG.b);

%Reference Position (0,0,0)
fprintf(fid,'\n#Xref Yref Zref\n');
fprintf(fid,'%.4f %.4f %.4f\n',AERO.XCG,0,AERO.ZCG);

%Profile Drag
fprintf(fid,'\n#CDp\n');
fprintf(fid,'%.3f\n',AC.CD0);

%Write FlapID Data at Nodes 
geo.flap_id(:,end+1,:) = 0; %add extra spanwise section
geo.flap_id(:,2:end,:) = max(geo.flap_id(:,1:end-1,:),geo.flap_id(:,2:end,:));
geo.fc(:,end+1) = 0;
geo.fc(:,2:end) = max(geo.fc(:,1:end-1),geo.fc(:,2:end));

%Loop Over Surfaces
label = {'WG','HT','VT'};
cs = {'flap','elevator','rudder','','','','',''};
for i = 1:3, label{end+1} = sprintf('Planform %d',i+3); end
%limit to 3 lifting surfaces
if geo.nwing>3, warndlg('Limiting to 3 Planforms'), geo.nwing=3; end
for i=1:geo.nwing, Write_Surface(fid,label{i},cs{i},geo,i,ni,nj), end
    
%Loop Over Bodies
% PT = {BD}; label = {'Fuselage'};
% if get(cmp(4),'Value'), PT(i) = {}; label(i) = {}; end
%for i=1:length(PT), Write_Body(PT,label{i},fid), end

%Finish and Close
fclose(fid);
    
end

function Write_Surface(fid,label,cs,geo,k,ni,nj)

%Surface
fprintf(fid,'\n#======================================================\n');
fprintf(fid,'SURFACE\n%s\n',label);
if geo.nelem(k)==nj-1
    fprintf(fid,'%d %.1f %d %.1f\n',ni,1,nj,-2); %match cosine spacing
else
    fprintf(fid,'%d %.1f %d %.1f\n',ni,1.0,nj,-1.1); %weighted outboard 
end

%Component
fprintf(fid,'\nCOMPONENT\n%d\n',1);

%Duplicate
if geo.dihed(k,1)~=pi/2 || geo.starty(k,1)
    fprintf(fid,'\nYDUPLICATE\n%.1f\n',0.0);
end

%Scale
fprintf(fid,'\nSCALE\n%.1f %.1f %.1f\n',1.0,1.0,1.0);

%Translate
fprintf(fid,'\nTRANSLATE\n%.1f %.1f %.1f\n',0.0,0.0,0.0);

%Incidence
fprintf(fid,'\nANGLE\n%.1f\n',0.0);

%Other Key Words...NOWAKE/NOALBE/NOLOAD

%Correct for Dihedral
for i=2:geo.nelem(k)
    dy = geo.starty(k,i)-geo.starty(k,i-1); sine = sin(geo.dihed(k,i-1));
    dz = geo.startz(k,i)-geo.startz(k,i-1); cosine = cos(geo.dihed(k,i-1));
    geo.starty(k,i) = geo.starty(k,i-1)+dy*cosine-dz*sine;
    geo.startz(k,i) = geo.startz(k,i-1)+dz*cosine+dy*sine;
end

%Prepare Variables to Loop Over Sections
n = geo.nelem(k); 
x = [geo.startx(k,1:n),geo.startx(k,n)+geo.b(k,n)*tan(geo.SW(k,n))];
y = [geo.starty(k,1:n),geo.starty(k,n)+geo.b(k,n)*cos(geo.dihed(k,n))];
z = [geo.startz(k,1:n),geo.startz(k,n)+geo.b(k,n)*sin(geo.dihed(k,n))];
c = [geo.c(k,1:n),geo.c(k,n)*geo.T(k,n)];
tw = [geo.TW(k,1:n,1),geo.TW(k,n,2)];
foil = [geo.foil(k,1:n,1),geo.foil(k,n,2)];

%Loop Over Sections
for j = 1:n+1
    
    %Section Parameters
    fprintf(fid,'\nSECTION\n');
    fprintf(fid,'%.2f %.2f %.2f %.2f %.2f\n',x(j),y(j),z(j),c(j),tw(j));
    
    %Airfoil Data
%     fprintf(fid,'\nAIRFOIL\n'); %this feature seems to be broken
%     fprintf(fid,'%.6f %.6f\n',fliplr(foil{j}'));
    fname = sprintf('%s.%d',label,j);
    afid = fopen(fname,'wt');
    fprintf(afid,'%.6f %.6f\n',fliplr(foil{j}'));
    fclose(afid);
    fprintf(fid,'\nAFILE\n%s\n',fname);
    
    %Controls
    if geo.flap_id(k,j,1) %flap
        switch label
            case 'WG', cs = 'flap';
            case 'HT', cs = 'elevator';
            case 'VT', cs = 'rudder';
        end
        fprintf(fid,'\nCONTROL\n'); 
        fprintf(fid,'%s %.1f %.1f %.1f %.1f %.1f\n',cs,geo.fc(k,j),0,0,0,1);
    end
    if geo.flap_id(k,j,2) %aileron
        if geo.flap_id(k,j,1), geo.fc(k,j) = geo.fc(k,j+1); end %overlap
        fprintf(fid,'\nCONTROL\n'); cs = 'aileron';
        fprintf(fid,'%s %.1f %.1f %.1f %.1f %.1f\n',cs,geo.fc(k,j),0,0,0,-1);
    end
    
    %Thick Airfoil Correction
    t = max(foil{j}(:,2))-min(foil{j}(:,2));
    fprintf(fid,'\nCLAF\n%.4f\n',1+0.77*t); 
    
    %CDCL                         |  (keyword)
    %CL1 CD1  CL2 CD2  CL3 CD3    |  CD(CL) function parameters
    
end

end

function Write_Body(PT,label,fid)

%Body
fprintf(fid,'BODY\n%s',label);

end

function Write_Case(CaseID,state)
%From Joseph Moster DEC 2011 (runAVL)

% Create run file
fid = fopen([CaseID,'.run'], 'w');
fprintf(fid, 'LOAD %s\n', [CaseID,'.avl']);

%Load mass parameters
if ~isempty(dir([CaseID,'.mass']))
    fprintf(fid, 'MASS %s\n', [CaseID,'.mass']);
    fprintf(fid, 'MSET 1\n');
end
fprintf(fid, '%i\n',   0);

%Disable Graphics
fprintf(fid, 'PLOP\ng\n\n');

%Open the OPER menu
fprintf(fid, '%s\n',   'OPER');

%Define the run case
fprintf(fid, '%s\n',   'c1');
fprintf(fid, 'v %6.4f\n',state.AS);
fprintf(fid, '\n');

%Options for trimming
%fprintf(fid, '%s\n',   'd1 rm 0'); %Set surface 1 so rolling moment is 0
%fprintf(fid, '%s\n',   'd2 pm 0'); %Set surface 2 so pitching moment is 0

%Run the Case
fprintf(fid, '%s\n',   'x');

%Save the st data
fprintf(fid, '%s\n',   'st');
fprintf(fid, '%s%s\n',CaseID,'.st');

%Save the sb data
fprintf(fid, '%s\n',   'sb');
fprintf(fid, '%s%s\n',CaseID,'.sb');

%Drop out of OPER menu
fprintf(fid, '%s\n',   '');

%Quit Program
fprintf(fid, 'Quit\n');

%Close fid
fclose(fid);

end
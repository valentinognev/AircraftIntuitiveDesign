function Initialize_GUI(choice)
global ax cmp WG WG_In HT HT_In VT VT_In BD_In BD AERO AERO_In AERO_Out ...
    F F_In A A_In E E_In R R_In NP_In NP NB_In NB Results opt tabs 
global lib_path

%% %%%%%%%%%%%%%%%%%%%%%%%% INITIALIZE FIGURE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if isempty(findall(0,'Type','Figure'))
    
    %Results (Analysis)
    Results = cell(1,4); 
    % -Results{1}: Digital DATCOM
    % -Results{2}: ASCDM
    % -Results{3}: Tornado
    % -Results{4}: AVL
    
    %Options (Settings)
    opt = []; 
    % -opt(1):  Estimate CG ________
    % -opt(2):  Transparency        \
    % -opt(3):  Show Axes           |
    % -opt(4):  Plot Resolution     |   Plot Options
    % -opt(5):  Shading             |
    % -opt(6):  Project Dimensions  |
    % -opt(7):  Color ______________/
	% -opt(8):  Trim                \
	% -opt(9):  Slip Stream         |   Calculations
    % -opt(10): Body Stability _____/
    % -opt(11): DATCOM IO Files     \
    % -opt(12): Plot DATCOM         |   DATCOM Options
    % -opt(13): Read DATCOM Results /
    % -opt(14): Toggle Units        
    % -opt(15): Error Check
    % -opt(16): Scroll Sensitivity
    
    %Initialize
    NP_In=cell(1,4); NP=NP_In;
    NB_In=cell(1,2); NB=NB_In;
    %opengl('save', 'software')  %use OpenGL for reduced graphics (grainy)
    res=get(0,'ScreenSize'); unit = 'ft'; 
    w = res(3); h = res(4); w=960; h=600; 
    f=figure('Name','Aircraft Intuitive Design Tool','NumberTitle','off',...
        'MenuBar','none','Position',[(res(3)-w)/2,(res(4)-h)/2,w,h],'Resize','on',...
        'WindowScrollWheelFcn',@Scroll,'Units','normalized',...
        'KeyPressFcn',{@Isolate,0},'KeyReleaseFcn',{@Isolate,1});
    
    %Axes
    ax{1}=axes('Units','normalized','Position',[0.3,0.2,0.7,0.6]); %axes
    ax{1}.Tag = 'Geometry'; %plot type
    ax{2}=cell(1,11); %handles {WG,HT,VT,BD,WG2,HT2,VT2,PROP,BD2,BD3,other}
    ax{3}=[]; %secondary axes (for profile sketcher)
    ax{4}={}; %background image {axes,data,image}
    ax{5}={}; %secondary background image {axes,data,image}
    ax{6}={}; %additional axes for cost function plots
    
 	%Axis Properties
    camproj(ax{1},'perspective')    %perspective viewing
    axis(ax{1},'off')               %Set axis visibility off
    view(ax{1},3)                   %Apply view rotation
    axis(ax{1},'equal')             %Correct aspect ratio
    camva(ax{1},5)              	%Zoom/Turn off stretch-to-fit
    
    %Context Menu
    c = uicontextmenu;
    f.UIContextMenu = c;
    uimenu(c,'Label','Reset Plot','Callback',{@setting,'reset'})
    rp = uimenu(c,'Label','Report');
    uimenu(rp,'Label','Create New','Callback',{@Add_Report,f},...
        'UserData',' ')
    uimenu(rp,'Label','Neutral Point','Callback',{@Add_Report,f},...
        'UserData','WG.X+WG.xmac+AC.N0*WG.cbar(end)')
    uimenu(rp,'Label','Drag Force (lb)','Callback',{@Add_Report,f},...
        'UserData','AC.CD0*ATM.Q*WG.S')
    uimenu(rp,'Label','Airspeed (ft/s)','Callback',{@Add_Report,f},...
        'UserData','AERO.MACH(1)*ATM.a') %kts *0.592484
    uimenu(rp,'Label','HT Volume Term','Callback',{@Add_Report,f},...
        'UserData','HT.V')
    uimenu(rp,'Label','VT Volume Term','Callback',{@Add_Report,f},...
        'UserData','VT.V')
    vw = uimenu(c,'Label','View');
    uimenu(vw,'Label','Side','Callback',{@setting,'view'})
    uimenu(vw,'Label','Top','Callback',{@setting,'view'})
    uimenu(vw,'Label','Front','Callback',{@setting,'view'})
    bg = uimenu(c,'Label','Background');
    uimenu(bg,'Label','Load','Callback',{@Image,'load',c})
    uimenu(bg,'Label','Flip','Callback',{@Image,'flip',c})
    uimenu(bg,'Label','Rotate','Callback',{@Image,'rotate',c})
    uimenu(bg,'Label','Hide','Callback',{@Image,'show',c},...
        'UserData',[0,0,1,1])
    uimenu(bg,'Label','White','Checked','off',...
        'Callback',{@setting,'color'});

    %Load/Save
    uimenu(f,'Label','New','Callback',{@AID,'make','New'});
    uimenu(f,'Label','Load','Callback',{@AID,'make','Load'});
    uimenu(f,'Label','Save','Callback',{@AID,'save','Save'});
    
    %DATCOM
    analyze = uimenu(f,'Label','Analyze');
    if exist(fullfile(lib_path,'DATCOM'),'dir')
        uimenu(analyze,'Label','DATCOM','Callback',{@AID,'save','DATCOM'});
    end
    if exist(fullfile(lib_path,'ASCDM'),'dir')
        uimenu(analyze,'Label','ASCDM','Callback',{@AID,'save','ASCDM'});
    end
    if exist(fullfile(lib_path,'Tornado'),'dir')
        uimenu(analyze,'Label','Tornado','Callback',{@AID,'save','Tornado'});
    end
    if exist(fullfile(lib_path,'AVL'),'dir')
        uimenu(analyze,'Label','AVL','Callback',{@AID,'save','AVL'});
    end
    
    %Results
    %The results menu option can be used to compare results from various
    %analysis methods side-by-side. This is a useful tool for validation.
%     out = uimenu(f,'Label','Results');
%     uimenu(out,'Label','Cruise','Callback',{@Plot_Results,'cruise'});
%     stb = uimenu(out,'Label','Stability');
%     uimenu(stb,'Label','Static','Callback',{@Plot_Results,'stc'});
%     uimenu(stb,'Label','Dynamic','Callback',{@Plot_Results,'dyn'});
%     uimenu(out,'Label','Drag','Callback',{@Plot_Results,'drag'})
%     uimenu(out,'Label','Control','Callback',{@Plot_Results,'con'});
    
    %Flight Simulator
    %All that is needed for this option is a simulink 6-DOF model and a
    %function to write the required stability derivatives to the base
    %workspace using the assignin('base',...) function. 
    
%     uimenu(f,'Label','Simulator','Callback',{@AID,'sim'});
    
    %Settings
    list = uimenu(f,'Label','Settings');
    
    %Scale A/C
    uimenu(list,'Label','Scale A/C Size','Callback',{@setting,'scale'})
    
    %Initialize Weight/Balance Data
    opt(1) = uimenu(list,'Label','Estimate CG','Checked','off');
    if isempty(get(opt(1),'UserData'))
        cg_data = cell(3,10);
        for i=1:3, for j=1:10, cg_data{i,j} = '0'; end, end
        set(opt(1),'UserData',cg_data)
    end
    
    %Plot
    plt = uimenu(list,'Label','Plot Options');
    opt(2) = uimenu(plt,'Label','Transparent','Checked','off',...
        'UserData',0.3);
    opt(3) = uimenu(plt,'Label','Show Axes','Checked','off');
    opt(4) = uimenu(plt,'Label','Plot Resolution','UserData',[100,101,51]);
    opt(5) = uimenu(plt,'Label','Interpolated Shading','Checked','on');
    opt(6) = uimenu(plt,'Label','Project Dimensions','Checked','off');
    opt(7) = uimenu(plt,'Label','Aircraft Color','UserData',[1,1,1]);
    
    %Calculation Settings
    calc = uimenu(list,'Label','Calculations');
    opt(8) = uimenu(calc,'Label','Trim Mode','Checked','off',...
        'UserData',[0,30]);
    opt(9) = uimenu(calc,'Label','Estimate Slipstream','Checked','off',...
        'UserData',[0.5,0.9]);
    opt(10) = uimenu(calc,'Label','Multhopp''s Method','Checked','on');
    
    %Other
    %dat = uimenu(list,'Label','DATCOM Options');
    %opt(11) = uimenu(dat,'Label','Input/Output Files','Checked','off');
    opt(12) = uimenu(list,'Label','Plot Results','Checked','off','Visible','off');
    opt(13) = uimenu(list,'Label','Read Coefficients','Checked','on','Visible','off');
    units = uimenu(list,'Label','Units');
    opt(14) = uimenu(units,'Label','in-oz-ft/s','Checked','off');
    opt(17) = uimenu(units,'Label','ft-lb-kts','Checked','on');
    %opt(14) = uimenu(units,'Label','Length - Inches','Checked','off');
    %opt(17) = uimenu(units,'Label','Airspeed - Knots','Checked','off');
    opt(11) = uimenu(list,'Label','Inputs/Outputs','Checked','off');
    opt(15) = uimenu(list,'Label','Error Check','Checked','on',...
        'UserData',[999,89,0]);
    opt(16) = uimenu(list,'Label','Scroll Sensitivity','Checked','off',...
        'UserData',0.1);
    
    %Callbacks
    set(opt,'Callback',@setting)
    set(opt(1),'Callback',{@setting,'weights'});
    set(opt(2),'Callback',{@setting,'alpha'});
    set(opt(3),'Callback',{@setting,'axes'});
    set(opt(4),'Callback',{@setting,'res'});
    set(opt(7),'Callback',{@setting,'ac_rgb'});
    set(opt(8),'Callback',{@setting,'trim'});
    set(opt(9),'Callback',{@setting,'dw'});
    set(opt(14),'Callback',{@setting,'units'});
    set(opt(15),'Callback',{@setting,'error'});
    set(opt(16),'Callback',{@setting,'scroll'});
    %set(opt(17),'Callback',{@setting,'units2'});
    set(opt(17),'Callback',{@setting,'units'});
    
    %Help
    help = uimenu(f,'Label','Help');
    uimenu(help,'Label','Examples','Callback',{@AID,'make','Models'})
    uimenu(help,'Label','Quick Start','Callback',{@doc,'quick ref'});
    uimenu(help,'Label','User''s Manual','Callback',{@doc,'full'})
    uimenu(help,'Label','','Enable','off');
    uimenu(help,'Label','Interactive Controls:','Enable','off');
    uimenu(help,'Label','===================','Enable','off');
    uimenu(help,'Label','Scroll - Adjust Selection/Zoom','Enable','off');
    uimenu(help,'Label','Left Click - Select/Rotate','Enable','off');
	uimenu(help,'Label','Double Click - Adjust Profile','Enable','off');
    uimenu(help,'Label','Right Click - Drag Plot/Pan','Enable','off');
    uimenu(help,'Label',' -> Model - Weight/Balance','Enable','off');
    uimenu(help,'Label',' -> Background - Options','Enable','off');
    uimenu(help,'Label','Center/Shift Click - Drag Part','Enable','off');
    uimenu(help,'Label','Space Key - Assign to Variable','Enable','off');
    uimenu(help,'Label','Any Other Key - Isolate Part','Enable','off');
    uimenu(help,'Label','===================','Enable','off');
    uimenu(help,'Label','','Enable','off');
    uimenu(help,'Label','Background Image:','Enable','off');
    uimenu(help,'Label','===================','Enable','off');
    uimenu(help,'Label','Scroll - Scale Image','Enable','off');
    uimenu(help,'Label','Left Click - Drag Image','Enable','off');
    uimenu(help,'Label','Right Click - Options','Enable','off');
    uimenu(help,'Label','===================','Enable','off');
    uimenu(help,'Label','','Enable','off');
    
else
    
    %Reset Figure
    f = gcf; f.Units = 'pixels';
    
    %Clear Axes
    ax{2}=cell(1,11);
    delete(findall(ax{1},'Type','surface'))
    delete(findall(ax{1},'Type','line'))
    delete(findall(ax{1},'Type','text'))
    delete(findall(ax{1},'Type','quiver'))
    
    %Check Units
    check = get(opt(14),'Checked');
    if strcmp(check,'on'), unit = 'in'; else, unit = 'ft'; end
    
end

%Aircraft tabs
uicontrol('Style','text','String','Parameters:','Units',...
    'normalized','Position',[0.03,0.05,0.28,0.92],'FontSize',14,...
    'HorizontalAlignment','Left');

%Tabs
Pos=[0.05,0.3,0.25,0.62];
tabs=uitabgroup(f,'Units','normalized','Position',Pos);
Wing=uitab(tabs,'Title','Wing');
HTail=uitab(tabs,'Title','HT');
VTail=uitab(tabs,'Title','VT');
Flaps=uitab(tabs,'Title','Control');
Body=uitab(tabs,'Title','Body');
Aero=uitab(tabs,'Title','Aero');
NewPart=uitab(tabs,'Title','+');
%Simulation=uitab(tabs,'Title','Sim');

%Send Tab Info
set(f,'WindowButtonDownFcn',@Click)

%% %%%%%%%%%%%%%%%%%%%%  Initialize tabs  %%%%%%%%%%%%%%%%%%%%%%%%%%%

%Labels
PR={'Root Chord','Break Chord','Tip Chord','Semi-Span','Break Span',...
    'Inboard Sweep','Outboard Sweep','Sweep Reference',...
    'Inboard Dihedral','Outboard Dihedral','Thickness',...
    'Washout','Incidence','Position, X','Position, Y','Position, Z'}; %plnf
PF={'Span','Chord','Deflection'};                                     %flap
AP={'Angle(s) of Attack','Altitude','Mach Number','Weight',...
    'CG Location, X','CG Location, Z','Inertia, X','Inertia, Y',...
    'Wing Root Airfoil','Wing Tip Airfoil','Tail Airfoil'};           %aero

%Field Names (DATCOM)
RP={'CHRDR','CHRDBP','CHRDTP','SSPN','SSPNOP','SAVSI','SAVSO',...
    'CHSTAT','DHDADI','DHDADO','TC','TWISTA','i','X','Y','Z'};        %plnf
RF={'SPANFI','SPANFO','CHRDFI','CHRDFO','DELTA'};                     %flap
RC=[RF(1:end-1),{'DELTAL','DELTAR'}];                                 %ailn
RA={'ALSCHD','ALT','MACH','WT','XCG','ZCG','XI','YI'};                %aero

%Update Options (choice)
update = {@AID,'update'};

%Dimensions
DIM={unit,unit,unit,unit,unit,'deg','deg','LE-TE','deg','deg','chord',...
    'deg','deg',unit,unit,unit};                                      %plnf
DMF={unit,unit,'deg'};                                                %flap
DMA={'deg','ft','(or ft/s)','lb',unit,unit,'slug*ft^2','slug*ft^2',...
    'NACA','NACA','NACA'};                                            %aero
if strcmp(get(opt(17),'Checked'),'on')
    DMA{3} = '(or kts)'; 
else
    DMA(7:8) = {'oz*in^2','oz*in^2'};
end

%Control Surface Placeholders
F.FTYPE=1; F.PHETE=0.003; F.PHETEP=0.002; F.TC=0.22; F.CB=0.3; A.STYPE=1;
E.FTYPE=1; E.PHETE=0.003; E.PHETEP=0.002; E.TC=0.22; E.CB=0.3;

%Initialize
if nargin %no input arguments (i.e. fuselage length)
    
    %Length
    L = choice; if isempty(L), L = 12; end
    
    %Wing
    WG_Default={L/4,L/4,L/4,L/2,0,0,0,0.25,0,0,0.12,0,0,L/4,0,0};
    for i=1:length(RP), WG.(RP{i})=WG_Default{i}; end
    WG_Default=cellfun(@num2str,WG_Default,'UniformOutput', false);
    
    %Horizontal Tail
    HT_Default={L/8,L/8,L/8,L/4,0,0,0,1,0,0,0.12,0,-1,7*L/8,0,0};
    for i=1:length(RP), HT.(RP{i})=HT_Default{i}; end
    HT_Default=cellfun(@num2str,HT_Default,'UniformOutput', false);
    
    %Vertical Tail
    VT_Default={L/8,L/8,L/8,L/4,0,0,0,1,0,0,0.12,0,0,7*L/8,0,0};
    for i=1:length(RP), VT.(RP{i})=VT_Default{i}; end
    VT_Default=cellfun(@num2str,VT_Default,'UniformOutput', false);
    
    %Body
    BD.NX=11; BD.X=linspace(0,L,BD.NX);     %longitudinal station position
    BD.ZU=L/12*ones(1,BD.NX); BD.ZL=-BD.ZU; %upper and lower coordinates
    BD.R=(BD.ZU-BD.ZL)/2; BD.S=pi*BD.ZU.^2; %half-width (and area not used)
    BD.N = 1:11; BD.P=ones(1,BD.NX);        %station shape parameter
    
    %Flaps
    F_Default = {L/12,L/4,L/12,L/12,0,0};
    for i=1:length(RF), F.(RF{i}) = F_Default{i}; end
    F_Default = cellfun(@num2str,F_Default,'UniformOutput', false);
    F_Default{4} = 'F.CHRDFI';
    
    %Ailerons
    A_Default={L/4,L/2,L/24,L/24,0,0};
    for i=1:length(RC), A.(RC{i}) = A_Default{i}; end
    A_Default=cellfun(@num2str,A_Default,'UniformOutput', false);
    A_Default{4}='A.CHRDFI'; A_Default{2}='WG.SSPN';
    
    %Elevator
    E_Default={L/12,L/4,L/24,L/24,0,0};
    for i=1:length(RF), E.(RF{i})=E_Default{i}; end
    E_Default = cellfun(@num2str,E_Default,'UniformOutput', false);
    E_Default{4} = 'E.CHRDFI'; E_Default{2} = 'HT.SSPN';
    
    %Rudder
    R_Default={L/12,L/4,L/24,L/24,0,0}; R_Default{4} = 'R.CHRDFI';
    for i=1:length(RF), R.(RF{i}) = R_Default{i}; end
    
    %Aero
    WG.NACA={'2412','2412'}; HT.NACA={'0012'}; VT.NACA={'0012'};
    WG.DATA={NACA_Panel_Maker(100,WG.NACA{1})};
    HT.DATA={NACA_Panel_Maker(50,HT.NACA{1})};
    VT.DATA={NACA_Panel_Maker(50,VT.NACA{1})};
    Aero_Default = {0,0,0.09,240,7.5*L/24,0,100,100}; %Nicolai pg 574
    for i=1:length(RA), AERO.(RA{i}) = Aero_Default{i}; end
    Aero_Default = cellfun(@num2str,Aero_Default,'UniformOutput',false);
    Aero_Default{1} = '-4:4:16'; %alpha range
    Aero_Default{5} = 'WG.X+WG.xmac+WG.cbar(end)/4';  %cg
    Aero_Default(9:11) = {WG.NACA{1},WG.NACA{2},HT.NACA{1}}; %airfoils
    WG.xmac = 0; WG.cbar = WG.CHRDR; 
    
else %update
    
    %Use Current Body Length
    L = BD.X(end)-BD.X(1);
    
    %Keep Current Planform tabs
    WG_Default=cell(1,16); HT_Default=cell(1,16); VT_Default=cell(1,16);
    for i=1:16
        WG_Default{i}=eval(get(WG_In(i),'String'));
        HT_Default{i}=eval(get(HT_In(i),'String'));
        VT_Default{i}=eval(get(VT_In(i),'String'));
    end
    
    %Keep Current Control tabs
    F_Default=cell(1,6); A_Default=cell(1,6);
    E_Default=cell(1,6); R_Default=cell(1,6);
    for i=1:5
        F_Default{i}=get(F_In(i),'String');
        A_Default{i}=get(A_In(i),'String');
        E_Default{i}=get(E_In(i),'String');
        R_Default{i}=get(R_In(i),'String');
    end
    F_Default{6}=F_Default{5}; A_Default{6}=get(A_In(6),'String');
    E_Default{6}=E_Default{5}; R_Default{6}=R_Default{5};
    
    %Keep Current Aero tabs
    Aero_Default=cell(1,11);
    for i=1:11, Aero_Default{i}=get(AERO_In(i),'String'); end
    
end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%% PLANFORMS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Planform Spacing Options
xi=[3,5,8,10,13];               %line breaks
lh = 0.01;      lt = 0.008;     %line height/thickness
y0 = 1;         dy = 0.0615;    %vertical spacing
x0 = 0.5;       dx = 0.05;      %horizontal spacing
wedit = 0.25;   h = 0.05;       %edit box dimensions
wchk = 0.1;     hchk = 0.06;    %check box
wdim = 0.2;                     %dimension text box

%Scroll Rate
delta = 10^(floor(log10(L))-2);
set(opt(16),'UserData',delta)
DP = zeros(1,length(DIM));
for i=1:length(DIM)
    if strcmp(DIM{i},unit)
        DP(i)=delta;
    elseif strcmp(DIM{i},'deg')
        DP(i)=1;
    else
        DP(i)=0.01;
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% WING %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Wing tabs
WG_In = zeros(1,length(PR));
for i=1:length(PR)
    
    uicontrol(Wing,'Style','text','Units','normalized','Position',...
        [0,y0-dy*i,x0-dx,h],'String',PR{i},'HorizontalAlignment','right')
    WG_In(i) = uicontrol(Wing,'Style','edit','String',WG_Default{i},...
        'Units','normalized','Position',[x0,y0-dy*i,wedit,h],...
        'Callback',update,'UserData',DP(i),'Tag',['WG.',RP{i}]);
    uicontrol(Wing,'Style','text','String',DIM{i},'Units','normalized',...
        'Position',[x0+wedit,y0-dy*i,wdim,h],'HorizontalAlignment','left')
end
if ~isempty(cmp) && cmp(1), val = get(cmp(1),'Value'); else, val = 1; end
cmp(1) = uicontrol(Wing,'Style','CheckBox','Value',val,'Units',...
    'normalized','Position',[0,y0-hchk,wchk,hchk],'Callback',{@Viz,1});
for i=1:length(xi) %section breaks
    uicontrol(Wing,'Style','text','Units','normalized','Position',...
        [0,y0-lh-dy*(xi(i)),1,lt],'BackgroundColor',[0.8,0.8,0.8]);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%% HORIZONTAL TAIL %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Horizontal Tail tabs
HT_In=zeros(1,length(PR));
for i=1:length(PR)
    uicontrol(HTail,'Style','text','Units','normalized','Position',...
        [0,y0-dy*i,x0-dx,h],'String',PR{i},'HorizontalAlignment','right')
    HT_In(i)=uicontrol(HTail,'Style','edit','String',HT_Default{i},...
        'Units','normalized','Position',[x0,y0-dy*i,wedit,h],...
        'Callback',update,'UserData',DP(i),'Tag',['HT.',RP{i}]);
    uicontrol(HTail,'Style','text','String',DIM{i},'Units','normalized',...
        'Position',[x0+wedit,y0-dy*i,wdim,h],'HorizontalAlignment','left')
end
if length(cmp)>1 && cmp(2), val = get(cmp(2),'Value'); else, val = 1; end
cmp(2) = uicontrol(HTail,'Style','CheckBox','Value',val,'Units',...
    'normalized','Position',[0,y0-hchk,wchk,hchk],'Callback',{@Viz,2});
for i=1:length(xi) %section breaks
    uicontrol(HTail,'Style','text','Units','normalized','Position',...
        [0,y0-lh-dy*(xi(i)),1,lt],'BackgroundColor',[0.8,0.8,0.8]);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%% VERTICAL TAIL %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Vertical Tail tabs
VT_In=zeros(1,length(PR));
for i=1:length(PR)
    uicontrol(VTail,'Style','text','Units','normalized','Position',...
        [0,y0-dy*i,x0-dx,h],'String',PR{i},'HorizontalAlignment','right')
    VT_In(i)=uicontrol(VTail,'Style','edit','String',VT_Default{i},...
        'Units','normalized','Position',[x0,y0-dy*i,wedit,h],...
        'Callback',update,'UserData',DP(i),'Tag',['VT.',RP{i}]);
    uicontrol(VTail,'Style','text','String',DIM{i},'Units','normalized',...
        'Position',[x0+wedit,y0-dy*i,wdim,h],'HorizontalAlignment','left')
end
if length(cmp)>2 && cmp(3), val = get(cmp(3),'Value'); else, val = 1; end
cmp(3) = uicontrol(VTail,'Style','CheckBox','Value',val,'Units',...
    'normalized','Position',[0,y0-hchk,wchk,hchk],'Callback',{@Viz,3});
for i=1:length(xi) %section breaks
    uicontrol(VTail,'Style','text','Units','normalized','Position',...
        [0,y0-lh-dy*(xi(i)),1,lt],'BackgroundColor',[0.8,0.8,0.8]);
end

%% %%%%%%%%%%%%%%%%%%%%%%% CONTROL SURFACES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Control Surface Spacing Options
y0 = 0.94;  dy = 0.052;
x0 = 0.05;  dx = 0.27;
wtext = 0.25; %label widths
xdim = x0+2*dx+wedit; %from planforms

%Scroll Rate
DP = [delta,delta,delta,delta,1,1];

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% FLAPS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Flap tabs
F_In=zeros(1,length(RF));
uicontrol(Flaps,'Style','text','String','Flaps:','Units','normalized',...
    'Position',[x0,y0+0.01,wtext,0.05],'HorizontalAlignment','left')
uicontrol(Flaps,'Style','text','String','Inboard','Units','normalized',...
    'Position',[x0+dx,y0,wtext,0.05])
uicontrol(Flaps,'Style','text','String','Outboard','Units','normalized',...
    'Position',[x0+2*dx,y0,wedit,0.05])
for i=1:length(PF)-1
    uicontrol(Flaps,'Style','text','String',PF{i},'Units','normalized',...
        'Position',[x0,y0-dy*i,wtext,0.05],'HorizontalAlignment','right');
    for j=1:2
        F_In(2*i-2+j)=uicontrol(Flaps,'String',F_Default{2*i-2+j},...
            'Units','normalized','Position',[x0+dx*j,y0-dy*i,wedit,h],...
            'Style','edit','Callback',update,'Tag',['F.',RF{2*i-2+j}]);
    end
    uicontrol(Flaps,'Style','text','String',DMF{i},'Units','normalized',...
        'Position',[xdim,y0-dy*i,wdim,h],'HorizontalAlignment','left')
end
uicontrol(Flaps,'String','Deflection','Units','normalized','Position',...
    [x0,y0-dy*(i+1),wedit,h],'Style','text','HorizontalAlignment','right')
F_In(end)=uicontrol(Flaps,'Style','edit','String',F_Default{end},...
    'Units','normalized','Position',[x0+1.5*dx,y0-dy*(i+1),wedit,h],...
    'Callback',update);
uicontrol(Flaps,'Style','text','String',DMF{end},'Units','normalized',...
    'Position',[xdim,y0-dy*(i+1),wdim,h],'HorizontalAlignment','left')
uicontrol(Flaps,'Style','text','Units','normalized','Position',...
    [0,y0-lh-dy*(i+1.5),1,lt],'BackgroundColor',[0.8,0.8,0.8])
for k=1:length(F_In), set(F_In(k),'UserData',DP(k)), end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%% AILERONS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Aileron tabs
A_In=zeros(1,length(RC)); y0=y0-(i+3)*dy;
uicontrol(Flaps,'Style','text','String','Ailerons:','Units','normalized',...
    'Position',[x0,y0+0.01,wtext,h],'HorizontalAlignment','left')
uicontrol(Flaps,'Style','text','String','Inboard','Units','normalized',...
    'Position',[x0+dx,y0,wtext,h])
uicontrol(Flaps,'Style','text','String','Outboard','Units','normalized',...
    'Position',[x0+2*dx,y0,wtext,h])
for i=1:length(PF)
    uicontrol(Flaps,'Style','text','String',PF{i},'Units','normalized',...
        'Position',[x0,y0-dy*i,wtext,h],'HorizontalAlignment','right');
    for j=1:2
        A_In(2*i-2+j)=uicontrol(Flaps,'String',A_Default{2*i-2+j},...
            'Units','normalized','Position',[x0+dx*j,y0-dy*i,wedit,h],...
            'Style','edit','Callback',update,'Tag',['A.',RC{2*i-2+j}]);
    end
    uicontrol(Flaps,'Style','text','String',DMF{i},'Units','normalized',...
        'Position',[xdim,y0-dy*i,wdim,h],'HorizontalAlignment','left')
end
uicontrol(Flaps,'Style','text','Units','normalized','Position',...
    [0,y0-lh-dy*(i+0.5),1,lt],'BackgroundColor',[0.8,0.8,0.8])
for k=1:length(A_In), set(A_In(k),'UserData',DP(k)), end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%% ELEVATOR %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Elevator tabs
E_In=zeros(1,length(RF)); y0=y0-(i+2)*dy;
uicontrol(Flaps,'Style','text','String','Elevator:','Units','normalized',...
    'Position',[x0,y0+0.01,wtext,0.05],'HorizontalAlignment','left')
uicontrol(Flaps,'Style','text','String','Inboard','Units','normalized',...
    'Position',[x0+dx,y0,wtext,0.05])
uicontrol(Flaps,'Style','text','String','Outboard','Units','normalized',...
    'Position',[x0+2*dx,y0,wedit,0.05])
for i=1:length(PF)-1
    uicontrol(Flaps,'Style','text','String',PF{i},'Units','normalized',...
        'Position',[x0,y0-dy*i,wtext,0.05],'HorizontalAlignment','right');
    for j=1:2
        E_In(2*i-2+j)=uicontrol(Flaps,'String',E_Default{2*i-2+j},...
            'Units','normalized','Position',[x0+dx*j,y0-dy*i,wedit,h],...
            'Style','edit','Callback',update,'Tag',['E.',RF{2*i-2+j}]);
    end
    uicontrol(Flaps,'Style','text','String',DMF{i},'Units','normalized',...
        'Position',[xdim,y0-dy*i,wdim,h],'HorizontalAlignment','left')
end
uicontrol(Flaps,'String','Deflection','Units','normalized','Position',...
    [x0,y0-dy*(i+1),wedit,h],'Style','text','HorizontalAlignment','right')
E_In(end)=uicontrol(Flaps,'Style','edit','String',E_Default{end},...
    'Units','normalized','Position',[x0+1.5*dx,y0-dy*(i+1),wedit,h],...
    'Callback',update);
uicontrol(Flaps,'Style','text','String',DMF{end},'Units','normalized',...
    'Position',[xdim,y0-dy*(i+1),wdim,h],'HorizontalAlignment','left')
uicontrol(Flaps,'Style','text','Units','normalized','Position',...
    [0,y0-lh-dy*(i+1.5),1,lt],'BackgroundColor',[0.8,0.8,0.8])
for k=1:length(E_In), set(E_In(k),'UserData',DP(k)), end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% RUDDER %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Rudder tabs
R_In=zeros(1,length(RF)); y0=y0-(i+3)*dy;
uicontrol(Flaps,'Style','text','String','Rudder:','Units','normalized',...
    'Position',[x0,y0+0.01,wtext,0.05],'HorizontalAlignment','left')
uicontrol(Flaps,'Style','text','String','Inboard','Units','normalized',...
    'Position',[x0+dx,y0,wtext,0.05])
uicontrol(Flaps,'Style','text','String','Outboard','Units','normalized',...
    'Position',[x0+2*dx,y0,wedit,0.05])
for i=1:length(PF)-1
    uicontrol(Flaps,'Style','text','String',PF{i},'Units','normalized',...
        'Position',[x0,y0-dy*i,wtext,0.05],'HorizontalAlignment','right');
    for j=1:2
        R_In(2*i-2+j)=uicontrol(Flaps,'String',R_Default{2*i-2+j},...
            'Units','normalized','Position',[x0+dx*j,y0-dy*i,wedit,h],...
            'Style','edit','Callback',update,'Tag',['R.',RF{2*i-2+j}]);
    end
    uicontrol(Flaps,'Style','text','String',DMF{i},'Units','normalized',...
        'Position',[xdim,y0-dy*i,wdim,h],'HorizontalAlignment','left')
end
uicontrol(Flaps,'String','Deflection','Units','normalized','Position',...
    [x0,y0-dy*(i+1),wedit,h],'Style','text','HorizontalAlignment','right')
R_In(end)=uicontrol(Flaps,'Style','edit','String',R_Default{end},...
    'Units','normalized','Position',[x0+1.5*dx,y0-dy*(i+1),wedit,h],...
    'Callback',update);
uicontrol(Flaps,'Style','text','String',DMF{end},'Units','normalized',...
    'Position',[xdim,y0-dy*(i+1),wdim,h],'HorizontalAlignment','left')
for k=1:length(R_In), set(R_In(k),'UserData',DP(k)), end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%% BODY %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Body Spacing Options
y0 = 1;  	dy = 0.06;  %vertical spacing
x0 = 0.15;  dx = 0.25;  %horizontal spacing
wbtn = 0.6; hbtn = 0.1; %button
wbedit = 0.2;           %smaller edit boxes


%Body tabs
uicontrol(Body,'Style','pushbutton','String','Adjust','Units',...
    'normalized','Position',[0.2,y0-2.25*dy,wbtn,hbtn],...
    'Callback',{@Profile_Sketcher,'Fuselage',unit})
uicontrol(Body,'Style','text','String','Station','Units','normalized',...
    'Position',[x0,y0-3.5*dy,wbedit,h]);
uicontrol(Body,'Style','text','String',['Position, ',unit],'Units',...
    'normalized','Position',[x0+dx-0.02,y0-3.5*dy,wbedit+0.04,h]);
uicontrol(Body,'Style','pushbutton','String','Shape','Units',...
    'normalized','Position',[x0+2*dx,y0-3.5*dy,wbedit,h],...
    'HorizontalAlignment','center','Callback',{@setting,'shape'});
y0 = y0-3.5*dy;
stations = cell(1,11); for i=1:11, stations{i} = num2str(i); end
for i=1:11
    BD_In(1,i)=uicontrol(Body,'Style','edit','String',num2str(i),...
        'Units','normalized','Position',[x0,y0-i*dy,wbedit,h],...
        'UserData',1);
    BD_In(2,i)=uicontrol(Body,'Style','edit','String',num2str(BD.X(i)),...
        'Units','normalized','Position',[x0+dx,y0-i*dy,wbedit,h],...
        'UserData',delta);
    BD_In(3,i)=uicontrol(Body,'Style','edit','String',num2str(BD.P(i)),...
        'Units','normalized','Position',[x0+2*dx,y0-i*dy,wbedit,h],...
        'UserData',0.1);
    set(BD_In(:,i),'Tag',['0',num2str(i)])
end
if ~range(BD.P), set(BD_In(3,2:10),'String',''), end
set(BD_In(:,1:11),'Callback',update)
uicontrol(Body,'Style','pushbutton','String','Circular Cross-Section',...
    'Units','normalized','Position',[0.25,y0-(i+1.5)*dy,0.5,h],...
    'Callback',{@AID,'update','Fuselage'});
if length(cmp)>3 && cmp(4), val = get(cmp(4),'Value'); else, val = 1; end
cmp(4) = uicontrol(Body,'Style','CheckBox','Value',val,'Units','normalized',...
    'Position',[0,0.98-hchk,wchk,wchk],'Callback',{@Viz,4});

%% %%%%%%%%%%%%%%%%%%%%%%%%% AERODYNAMICS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Aero Spacing Options
xi = [1,4,6,8,11];      	%line breaks
y0 = 1;  	dy = 0.07;      %vertical spacing
x0 = 0.5;  	dx = 0.05;      %horizontal spacing

%Scroll Rate
delta_w = 10^(floor(log10(AERO.WT(1)))-2);
DP=[0.1,500,0.01,delta_w,delta,delta,delta*10,delta*10,0,0,0];

%Aerodynamic tabs
AERO_In=zeros(1,length(AP));
for i=1:length(AP)
    uicontrol(Aero,'Style','text','Units','normalized','Position',...
        [0,y0-dy*i,x0-dx,h],'String',AP{i},'HorizontalAlignment','right')
    AERO_In(i)=uicontrol(Aero,'Style','edit','String',Aero_Default{i},...
        'Units','normalized','Position',[x0,y0-dy*i,wedit,h],...
        'Callback',update,'UserData',DP(i));
    if i<=length(RA), set(AERO_In(i),'Tag',['AERO.',RA{i}]), end
    uicontrol(Aero,'Style','text','String',DMA{i},'Units','normalized',...
        'Position',[x0+wedit,y0-dy*i,wdim,h],'HorizontalAlignment','left')
end
uicontrol(Aero,'Style','text','String','CG Adjust:',...
    'Position',[0,50,100,20],'FontSize',10,'Units','normalized');
uicontrol(Aero,'Style','checkbox','String','%MAC',...
    'Position',[120,50,100,20],'FontSize',10,'Units','normalized',...
    'Callback',{@setting,'cg_lim'});
AERO_In(i+1)=uicontrol(Aero,'Style','slider',...
    'Position',[20,20,200,20],'Min',0,'Max',L,'Value',5*L/16,...
    'Callback', @sliderRelease,'Units','normalized');
addlistener(AERO_In(i+1),'ContinuousValueChange',@sliderCallback);
for i=1:length(xi) %section breaks
    uicontrol(Aero,'Style','text','Units','normalized','Position',...
        [0,y0-lh-dy*(xi(i)),1,lt],'BackgroundColor',[0.8,0.8,0.8]);
end

%Disable Inertia Inputs
%set(AERO_In(7:8),'Enable','off')

%% %%%%%%%%%%%%%%%%%%%%%%%%%%% NEW PART %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%New Part Spacing Options
y0 = 1;  	dy = 0.15;  %vertical spacing
wbtn = 0.6; hbtn = 0.1; %button
x0 = 0.2;

%New Part Tab
parts = {'New Body','Propeller','New Wing','New HT','New VT'};
uicontrol(NewPart,'Style','text','String','Choose a Component to Add:',...
    'Units','normalized','Position',[0,y0-0.1,0.7,h],'FontSize',10);
imported = zeros(1,length(parts)); y0 = y0 - dy;
if ~isempty(NB{1}), imported(1) = 1; end
if ~isempty(NB{2}), imported(1) = 2; end
for n=1:length(NP)
    if n==4, i = 2; else, i = n+2; end
    if ~isempty(NP{n}), imported(i) = 1; end
end
for i=1:length(parts)
    btn = uicontrol(NewPart,'Style','pushbutton','String',parts{i},...
        'Units','normalized','Position',[x0,y0-i*dy,wbtn,hbtn],...
        'Callback',{@addPart,f,unit,i});
    if imported(i),     addPart(btn,0,f,unit,i), end
    if imported(i)==2,  addPart(btn,0,f,unit,i), end %body 2
end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%% RESULTS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Results Spacing Options
y0 = 1;         dy = 0.3;      	%vertical spacing
x0 = 0.1;       wradio = 0.8; 	%horizontal spacing
hradio = 0.25;	%radio button size

%Results Section
uicontrol('Style','text','String','Results:','Units','normalized',...
    'Position',[0.03,0.23,0.2,0.05],'FontSize',14,'HorizontalAlignment','Left')
plt_type=uibuttongroup('Visible','on','Position',[0.05,0.08,0.12,0.15],...
    'Title','Plot');
uicontrol(plt_type,'Style','radiobutton','String','Geometry',...
    'Units','normalized','Position',[x0,y0-dy,wradio,hradio],...
    'Callback',{@AID,'change_ax'})
uicontrol(plt_type,'Style','radiobutton','String','Stability',...
    'Units','normalized','Position',[x0,y0-2*dy,wradio,hradio],...
    'Callback',{@AID,'change_ax',tabs})
uicontrol(plt_type,'Style','radiobutton','String','Aerodynamics',...
    'Units','normalized','Position',[x0,y0-3*dy,wradio,hradio],...
    'Callback',{@AID,'change_ax'})
results = uipanel('Visible','on','Title','Stability',...
    'Position',[0.18,0.08,0.12,0.15],'ButtonDownFcn',{@cg,f,Aero});
AERO_Out = uicontrol(results,'Style','text','Units','normalized',...
    'Position',[0.1,0.1,0.8,0.8],'HitTest','off');

%Normalize Units
f.Units = 'normalized';

% Dark MATLAB desktop uses light uicontrol text; keep values readable on white edits
set(findall(f,'Style','edit'),'ForegroundColor',[0,0,0])

%Update Plot
delete(findall(ax{1},'Type','light'))
AID(0,0,'update')

end

function doc(handle,~,option)%%%%%%%%%%%%%%%%% DOCUMENTATION %%%%%%%%%%%%%%%%%%%
global lib_path ax WG HT VT WG_In HT_In VT_In tabs

switch option
    case 'quick ref'
        
        tab_list = get(tabs,'Children');
        if tabs.SelectedTab==tab_list(2) %HT
            PT = HT; PT_In = HT_In; 
            Az1 = 0; El1 = 90; 
        elseif tabs.SelectedTab==tab_list(3) %VT
            PT = VT; PT_In = VT_In; 
            Az1 = 0; El1 = 0; 
        else
            PT = WG; PT_In = WG_In;
            Az1 = 0; El1 = 90; 
        end
        
        %Rotate Model Axes
        N=30; %steps for cool animation
        [Az0,El0]=view(ax{1});
        Az = Az0;	dAz=(Az1-Az0)/N;
        El = El0;	dEl=(El1-El0)/N;
        
        %If Beyond 10 Deg
        if abs(dAz)>10/N || abs(dEl)>10/N
            for n=1:N
                El=El+dEl;  Az=Az+dAz;
                view(ax{1},[Az,El])
                delete(findall(ax{1},'Type','light'))
                camlight(-15,30), camlight(15,30)
                pause(0.001)
            end
        else
            view(ax{1},[Az1,El1])
        end
        
        %Plot Patches to Distinguish Click Points
        alpha(0.3) 
        x = [PT.X;0;PT.Xbrk;0;PT.Xtip].*ones(1,4)+...
            [PT.CHRDR;0;PT.CHRDBP;0;PT.CHRDTP].*[0,0.25,0.75,1];
        y = [PT.Y;PT.Y+0.1*PT.SSPN;PT.Ybrk;PT.Ytip-0.1*PT.SSPN;PT.Ytip];
        z = [PT.Z;0;PT.Zbrk;0;PT.Ztip];
        if PT.SSPNOP %[root; tip; le_in; le_out; te_in; te_out]
            x([2,4],:) = interp1(y([1,3,5]),x([1,3,5],:),y([2,4]),'linear');
            z([2,4]) = interp1(y([1,3,5]),z([1,3,5]),y([2,4]),'linear');
            xi = [1,4;1,4;1,2;1,2;3,4;3,4]; xj = [1,2;4,5;2,3;3,4;2,3;3,4];
            yj=[xj,xj]; yj(:,2:3)=fliplr(yj(:,2:3)); %correct polygon shape
            color = [0,1,0;1,1,0;0,0,1;1,0,1;0,1,1;0,1,1];
            option = [1,1;3,3;6,9;7,10;4,4;4,4];
        else %[root; tip; le; te]
            x([2,4],:) = interp1(y([1,5]),x([1,5],:),y([2,4]),'linear');
            z([2,4]) = interp1(y([1,5]),z([1,5]),y([2,4]),'linear');
            xi = [1,4;1,4;1,2;3,4]; xj = [1,2;4,5;2,4;2,4];
            yj=[xj,xj]; yj(:,2:3)=fliplr(yj(:,2:3)); %correct polygon shape
            color = [0,1,0;1,1,0;0,0,1;0,1,1]; option = [1,1;3,3;6,9;4,4];
        end
        if El1 == 0, z1 = z; z = y; y = z1; end %correct for vertical tail
        for i=1:size(xi,1)
            p(i) = patch([x(xj(i,1),xi(i,:)),fliplr(x(xj(i,2),xi(i,:)))],...
                y(yj(i,:)),z(yj(i,:)),color(i,:));
            set(PT_In(option(i,:)),'BackgroundColor',color(i,:))
        end
        
        %Help Message
        waitfor(helpdlg({'- Certain parameters can be selected by clicking on these regions','',...
            '- Scroll up or down to adjust any selected parameter''s value','',...
            '- Center/Shift+Click to drag individual components along axes','',...
            '- Hold down any key to isolate/uncover the selected component','',...
            '- Double Click fuselage (or any other component) to adjust profile'},'Quick Start Guide'))
        
        %Rotate Model Axes
        N=30; %steps for cool animation
        Az1 = Az0;  El1 = El0;
        [Az0,El0]=view(ax{1});
        Az = Az0;		dAz=(Az1-Az0)/N;
        El = El0;   	dEl=(El1-El0)/N;
        
        %If Beyond 10 Deg
        if abs(dAz)>10/N || abs(dEl)>10/N
            for n=1:N
                El=El+dEl;  Az=Az+dAz;
                view(ax{1},[Az,El])
                delete(findall(ax{1},'Type','light'))
                camlight(-15,30), camlight(15,30)
                pause(0.001)
            end
        else
            view(ax{1},[Az1,El1])
        end
        
        %Reset Transparency
        delete(p)
        alpha(1)
        
    case 'tutorial'
        
    case 'full'
        fname = fullfile(lib_path,'AID_Documentation.pdf');
        %system(['open ''',fname,'''']); %fname in hard quotes
        uiopen(fname,1);
end
%     %Axes
%     ax{1}=axes('Units','normalized','Position',[0.3,0.2,0.7,0.6]); %axes
%     ax{1}.Tag = 'Geometry'; %plot type
%     
%  	%Axis Properties
%     camproj(ax{1},'perspective')    %perspective viewing
%     axis(ax{1},'off')               %Set axis visibility off
%     view(ax{1},3)                   %Apply view rotation
%     axis(ax{1},'equal')             %Correct aspect ratio
%     camva(ax{1},5)              	%Zoom/Turn off stretch-to-fit
AID(0,0,'update')

end

function cg(~,~,f,Aero)%%%%%%%%%%%%%%%%%%% ADJUST CG %%%%%%%%%%%%%%%%%%%%%%
global tabs AERO_In

set(tabs,'SelectedTab',Aero)
set(f,'CurrentObject',AERO_In(5))
AID(AERO_In(5),0,'update')

end
%% %%%%%%%%%%%%%%%%%%%%%%%%%%%% ADD PART %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function addPart(handle,~,f,unit,component)
global BD NP_In NP NB_In NB tabs cmp

%Component
n = 0;
switch component
    case 1
        if isempty(NB_In{1})
            name = 'Body 2';    n = 1;
        else
            name = 'Body 3';    n = 2;
            set(handle,'Visible','off')
        end
    case 2
        name = 'Prop';
        set(handle,'Visible','off')
    case 3
        name = 'Wing 2';
        set(handle,'Visible','off')
    case 4
        name = 'HT 2';
        set(handle,'Visible','off')
    case 5
        name = 'VT 2';
        set(handle,'Visible','off')
end
New = uitab(tabs,'Title',name);
set(f,'WindowButtonDownFcn',@Click) %update tab info

%Labels
PR={'Root Chord','Break Chord','Tip Chord','Semi-Span','Break Span',...
    'Inboard Sweep','Outboard Sweep','Sweep Reference',...
    'Inboard Dihedral','Outboard Dihedral','Thickness',...
    'Washout','Incidence','Position, X','Position, Y','Position, Z'}; %plnf

%Field Names (DATCOM)
RP={'CHRDR','CHRDBP','CHRDTP','SSPN','SSPNOP','SAVSI','SAVSO',...
    'CHSTAT','DHDADI','DHDADO','TC','TWISTA','i','X','Y','Z'};        %plnf

%Update Options (choice)
update = {@AID,'update'};

%Dimensions
DIM={unit,unit,unit,unit,unit,'deg','deg','LE-TE','deg','deg','','deg',...
    'deg',unit,unit,unit};                                                  %plnf

%Adjust Rate
L = BD.X(end)-BD.X(1);
delta = 10^(floor(log10(L))-2);
DP = zeros(1,length(DIM));
for i=1:length(DIM)
    if strcmp(DIM{i},unit)
        DP(i)=delta;
    elseif strcmp(DIM{i},'deg')
        DP(i)=1;
    else
        DP(i)=0.01;
    end
end

%Wing
if strcmp(name,'Wing 2')
    WG_Default={L/4,L/4,L/4,L/2,0,0,0,0.25,0,0,0.12,0,0,L/4,0,0};
    if ~isempty(NP{1})
        winglet_option = 0;
        for k=1:length(RP)
            if isfield(NP{1},RP{k}), WG_Default{k}=NP{1}.(RP{k}); end
        end
    else
        winglet_option = 1;
        NP{1}.NACA = {'2412'};
        NP{1}.DATA = {NACA_Panel_Maker(100,NP{1}.NACA{1})};
    end
    WG_Default=cellfun(@num2str,WG_Default,'UniformOutput', false);
    
    %Winglet
    if winglet_option
        answr = questdlg('Create winglet?','Winglet','Yes','No','Yes');
    else
        answr = 'Nope';
    end
    if strcmp(answr,'Yes')
        WG_Default{1} = 'WG.CHRDTP';        % root chord
        WG_Default{3} = 'NP{1}.CHRDR/2';    % tip chord
        WG_Default{4} = 'WG.SSPN/10';      	% semi-span
        WG_Default{6} = '60';               % sweep
        WG_Default{8} = '1';                % sweep reference
        WG_Default{9} = '60';               % dihedral
        WG_Default{11} = 'WG.TC';          	% thickness
        WG_Default{13} = 'WG.i-WG.TWISTA'; 	% incidence
        WG_Default{14} = 'WG.Xtip';        	% X
        WG_Default{15} = 'WG.Ytip';        	% Y
        WG_Default{16} = 'WG.Ztip';       	% Z
    end
    
end

%Horizontal Tail
if strcmp(name,'HT 2')
    HT_Default={L/8,L/8,L/8,L/4,0,0,0,1,0,0,0.12,0,0,7*L/8,0,0};
    if ~isempty(NP{2})
        for k=1:length(RP)
            if isfield(NP{2},RP{k}), HT_Default{k}=NP{2}.(RP{k}); end
        end
	else
        NP{2}.NACA = {'0012'};
        NP{2}.DATA = {NACA_Panel_Maker(50,NP{2}.NACA{1})};
    end
    HT_Default=cellfun(@num2str,HT_Default,'UniformOutput', false);
end

%Vertical Tail
if strcmp(name,'VT 2')
    VT_Default={L/8,L/8,L/8,L/4,0,0,0,1,0,0,0.12,0,0,7*L/8,0,0};
    if ~isempty(NP{3})
        for k=1:length(RP)
            if isfield(NP{3},RP{k}), VT_Default{k}=NP{3}.(RP{k}); end
        end
	else
        NP{3}.NACA = {'0012'};
        NP{3}.DATA = {NACA_Panel_Maker(50,NP{3}.NACA{1})};
    end
    VT_Default=cellfun(@num2str,VT_Default,'UniformOutput', false);
end

%Propeller
if strcmp(name,'Prop')
    Prop_Default={L/32,L/32,L/64,L/8,0,0,0,0,0,0,0.12,30,30,L/4,L/4,0};
    if ~isempty(NP{4})
        for k=1:length(RP)
            if isfield(NP{4},RP{k}), Prop_Default{k}=NP{4}.(RP{k}); end
        end
    else
        NP{4}.NACA = {'0012'};
        NP{4}.DATA = {NACA_Panel_Maker(50,NP{4}.NACA{1})};
    end
    Prop_Default=cellfun(@num2str,Prop_Default,'UniformOutput', false);
end

%Initialize Body tabs
if n && ~isempty(NB{n})
    if NB{n}.NX>7
        XP = linspace(NB{n}.X(1),NB{n}.X(end),7);
        N = interp1(NB{n}.X,1:NB{n}.NX,XP,'nearest','extrap');
        if length(unique(N))<NB{n}.NX, N = [1:6,NB{n}.NX]; end
    else
        N = 1:NB{n}.NX;
    end
    X = NB{n}.X(N); P = NB{n}.P(N); NB{n}.N = N;
    pos = {num2str(NB{n}.X0),num2str(NB{n}.Y0),num2str(NB{n}.Z0)};
elseif n
    NB{n}.NX=7; NB{n}.X=linspace(0,L/4,NB{n}.NX); 
    NB{n}.ZU=L/24*ones(1,NB{n}.NX); NB{n}.ZL=-NB{n}.ZU;
    NB{n}.R=(NB{n}.ZU-NB{n}.ZL)/2;  NB{n}.S=pi*NB{n}.ZU.^2;
    X = NB{n}.X; N = 1:7; P = ones(1,7); NB{n}.N = N;
    pos = {num2str(L/4),num2str(L/4),'0'};
end

%Planform Spacing Options
xi=[3,5,8,10,13];               %line breaks
lh = 0.01;      lt = 0.008;     %line height/thickness
y0 = 1;         dy = 0.0615;    %vertical spacing
x1 = 0.5;       wt = 0.05;      %horizontal spacing
wedit = 0.25;   h = 0.05;       %edit box dimensions
wchk = 0.1;     hchk = 0.06;    %check box
wdim = 0.2;                     %dimension text box

switch component
    
    case 1 %%%%%%%%%%%%%%%%%%%%%%%%% NEW BODY %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        %Body Spacing Options
        y0 = 1;         dy = 0.06;      %vertical spacing
        x0 = 0.15;      dx = 0.25;      %horizontal spacing
        wbtn = 0.6;     hbtn = 0.1;     %button
        wbedit = 0.2;
        label = {'Position, X','Position, Y','Position, Z'};
        
        %Body tabs
        uicontrol(New,'Style','pushbutton','String','Adjust','Units',...
            'normalized','Position',[0.2,y0-2.25*dy,wbtn,hbtn],...
            'Callback',{@Profile_Sketcher,sprintf('Body %d',n+1),unit})
        uicontrol(New,'Style','text','String','Station','Units','normalized',...
            'Position',[x0,y0-3.5*dy,wbedit,h]);
        uicontrol(New,'Style','text','String',['Position, ',unit],'Units',...
            'normalized','Position',[x0+dx-0.02,y0-3.5*dy,wbedit+0.04,h]);
        uicontrol(New,'Style','pushbutton','String','Shape','Units',...
            'normalized','Position',[x0+2*dx,y0-3.5*dy,wbedit,h],...
            'HorizontalAlignment','center',...
            'Callback',{@setting,sprintf('shape%d',n)});
        y0 = y0-3.5*dy;
        stations = cell(1,11); for i=1:11, stations{i} = num2str(i); end
        for i=1:7
            if i>length(N)
                Nstr = ''; Xstr = ''; Pstr = '';
            else
                Nstr = num2str(N(i)); 
                Xstr = num2str(X(i)); 
                if ~range(P) && i>1 && i<7
                    Pstr = '';
                else
                    Pstr = num2str(P(i));
                end
            end
            NB_In{n}(1,i)=uicontrol(New,'Style','edit','String',Nstr,...
                'Units','normalized','Position',[x0,y0-i*dy,wbedit,h],...
                'UserData',1);
            NB_In{n}(2,i)=uicontrol(New,'Style','edit','String',Xstr,...
                'Units','normalized','Position',[x0+dx,y0-i*dy,wbedit,h],...
                'UserData',delta);
            NB_In{n}(3,i)=uicontrol(New,'Style','edit','String',Pstr,...
                'Units','normalized','Position',[x0+2*dx,y0-i*dy,wbedit,h],...
                'UserData',0.1);
            set(NB_In{n}(:,i),'Tag',[num2str(n),num2str(i)]);
        end
        set(NB_In{n}(:,1:7),'Callback',update)
        uicontrol(New,'Style','pushbutton','String','Circular Cross-Section',...
            'Units','normalized','Position',[0.25,y0-(i+1.5)*dy,0.5,h],...
            'Callback',{@AID,'update',sprintf('Body %d',n)});
        for i=8:10
            uicontrol(New,'Style','text','String',label{i-7},'Units',...
                'normalized','Position',[0,y0-(i+2)*dy,x1-wt,h],...
                'HorizontalAlignment','right');
            NB_In{n}(1,i)=uicontrol(New,'Style','edit','String',pos{i-7},...
                'Units','normalized','Position',[x1,y0-(i+2)*dy,wedit,h]);
            uicontrol(New,'Style','text','String',unit,'Units','normalized',...
                'Position',[x1+wedit,y0-(i+2)*dy,wdim,h],'HorizontalAlignment','left')
        end
        set(NB_In{n}(1,8:10),'Callback',update,'UserData',delta)
        cmp(8+n) = uicontrol(New,'Style','CheckBox','Value',1,'Units','normalized',...
            'Position',[0,0.98-hchk,wchk,wchk],'Callback',{@Viz,8+n});
        
    case 2 %%%%%%%%%%%%%%%%%%%%%%%%% PROPELLER %%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        %Prop tabs
        n = 4; NP_In{n} = zeros(1,length(PR));
        for i=1:length(PR)
            uicontrol(New,'Style','text','Units','normalized','Position',...
                [0,y0-dy*i,x1-wt,h],'String',PR{i},'HorizontalAlignment','right')
            NP_In{n}(i) = uicontrol(New,'Style','edit','String',Prop_Default{i},...
                'Units','normalized','Position',[x1,y0-dy*i,wedit,h],...
                'Callback',update,'UserData',DP(i),'Tag',['NP{4}.',RP{i}]);
            uicontrol(New,'Style','text','String',DIM{i},'Units','normalized',...
                'Position',[x1+wedit,y0-dy*i,wdim,h],'HorizontalAlignment','left')
        end
        cmp(8) = uicontrol(New,'Style','CheckBox','Value',1,'Units','normalized',...
            'Position',[0,y0-hchk,wchk,hchk],'Callback',{@Viz,4+n});
        for i=1:length(xi) %section breaks
            uicontrol(New,'Style','text','Units','normalized','Position',...
                [0,y0-lh-dy*(xi(i)),1,lt],'BackgroundColor',[0.8,0.8,0.8]);
        end
        
    case 3 %%%%%%%%%%%%%%%%%%%%%%%% NEW WING %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        %Wing tabs
        n = 1; NP_In{n} = zeros(1,length(PR));
        for i=1:length(PR)
            uicontrol(New,'Style','text','Units','normalized','Position',...
                [0,y0-dy*i,x1-wt,h],'String',PR{i},'HorizontalAlignment','right')
            NP_In{n}(i) = uicontrol(New,'Style','edit','String',WG_Default{i},...
                'Units','normalized','Position',[x1,y0-dy*i,wedit,h],...
                'Callback',update,'UserData',DP(i),'Tag',['NP{1}.',RP{i}]);
            uicontrol(New,'Style','text','String',DIM{i},'Units','normalized',...
                'Position',[x1+wedit,y0-dy*i,wdim,h],'HorizontalAlignment','left')
        end
        cmp(5) = uicontrol(New,'Style','CheckBox','Value',1,'Units','normalized',...
            'Position',[0,y0-hchk,wchk,hchk],'Callback',{@Viz,4+n});
        for i=1:length(xi) %section breaks
            uicontrol(New,'Style','text','Units','normalized','Position',...
                [0,y0-lh-dy*(xi(i)),1,lt],'BackgroundColor',[0.8,0.8,0.8]);
        end
        
    case 4 %%%%%%%%%%%%%%%%%%%% NEW HORIZONTAL TAIL %%%%%%%%%%%%%%%%%%%%%%%
        
        %Horizontal Tail tabs
        n = 2; NP_In{n} = zeros(1,length(PR));
        for i=1:length(PR)
            uicontrol(New,'Style','text','Units','normalized','Position',...
                [0,y0-dy*i,x1-wt,h],'String',PR{i},'HorizontalAlignment','right')
            NP_In{n}(i) = uicontrol(New,'Style','edit','String',HT_Default{i},...
                'Units','normalized','Position',[x1,y0-dy*i,wedit,h],...
                'Callback',update,'UserData',DP(i),'Tag',['NP{2}.',RP{i}]);
            uicontrol(New,'Style','text','String',DIM{i},'Units','normalized',...
                'Position',[x1+wedit,y0-dy*i,wdim,h],'HorizontalAlignment','left')
        end
        cmp(6) = uicontrol(New,'Style','CheckBox','Value',1,'Units','normalized',...
            'Position',[0,y0-hchk,wchk,hchk],'Callback',{@Viz,4+n});
        for i=1:length(xi) %section breaks
            uicontrol(New,'Style','text','Units','normalized','Position',...
                [0,y0-lh-dy*(xi(i)),1,lt],'BackgroundColor',[0.8,0.8,0.8]);
        end
        
    case 5 %%%%%%%%%%%%%%%%%%%%% NEW VERTICAL TAIL %%%%%%%%%%%%%%%%%%%%%%%%
        
        %Vertical Tail tabs
        n =3; NP_In{n} = zeros(1,length(PR));
        for i=1:length(PR)
            uicontrol(New,'Style','text','Units','normalized','Position',...
                [0,y0-dy*i,x1-wt,h],'String',PR{i},'HorizontalAlignment','right')
            NP_In{n}(i) = uicontrol(New,'Style','edit','String',VT_Default{i},...
                'Units','normalized','Position',[x1,y0-dy*i,wedit,h],...
                'Callback',update,'UserData',DP(i),'Tag',['NP{3}.',RP{i}]);
            uicontrol(New,'Style','text','String',DIM{i},'Units','normalized',...
                'Position',[x1+wedit,y0-dy*i,wdim,h],'HorizontalAlignment','left')
        end
        cmp(7) = uicontrol(New,'Style','CheckBox','Value',1,'Units','normalized',...
            'Position',[0,y0-hchk,wchk,hchk],'Callback',{@Viz,4+n});
        for i=1:length(xi) %section breaks
            uicontrol(New,'Style','text','Units','normalized','Position',...
                [0,y0-lh-dy*(xi(i)),1,lt],'BackgroundColor',[0.8,0.8,0.8]);
        end
end

%Update
f.Units = 'normalized';
set(tabs,'SelectedTab',New)
AID(0,0,'update')

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%% SETTINGS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function setting(handle,~,choice)
global opt ax WG_In WG HT_In HT VT_In VT BD_In BD AERO_In AERO ...
    F_In A_In E_In R_In NB_In NB NP_In NP Results

%Set Callbacks for setting Menu
if isprop(handle,'Checked')
    check = get(handle,'Checked');
elseif isprop(handle,'Value')
    check = get(handle,'Value');
end
update = 1;

%Check Units
if strcmp(get(opt(14),'Checked'),'on'), unit = 'in'; else, unit = 'ft'; end

%Change Required Setting
if nargin>2 %do more than toggle value
    
    scale = 1; %Use scale section for units and scale A/C options
    switch choice
            
        case 'res' %%%%%%%%%%%%%%%% CHANGE PLOT RESOLUTION %%%%%%%%%%%%%%%%
            
            if strcmp(get(opt(5),'Checked'),'on')
                force_wireframe = 1;
                set(opt(5),'Checked','off') %shaded > wireframe
            else
                force_wireframe = 0;
            end
            finished = 0;
            while ~finished
                AID(0,0,'plot') %update plot
                prompt = {'Body','Wing','Tail'};
                res_in = get(handle,'UserData');
                default = cell(1,3);
                for i=1:3, default{i} = num2str(res_in(i)); end
                res = inputdlg(prompt,'Plot Resolution',1,default);
                if isempty(res), res = default; finished = 1; end
                res = str2double(res);
                set(handle,'UserData',res);
            end
            if force_wireframe
                set(opt(5),'Checked','on') %back to shaded
            end
            
        case 'reset' %%%%%%%%%%%%%%%%%%% RESET AXES %%%%%%%%%%%%%%%%%%%%%%%  
            
            %Clear Plots
            tag = ax{1}.Tag; delete(findall(gcf,'Type','axes'))
            ax{1}=axes('Units','normalized'); %axes
            ax{1}.Tag = tag; %plot type
            ax{2}=cell(1,11); %handles {WG,HT,VT,BD,WG2,HT2,VT2,PROP,BD2,BD3,other}
            ax{3}=[]; %secondary axes (for profile sketcher)
            
            axes(ax{1})
            if strcmp(ax{1}.Tag,'Geometry')
                set(ax{1},'Position',[0.3,0.2,0.7,0.6])
            elseif strcmp(ax{1}.Tag,'Stability')
                Results = cell(1,4);
                set(ax{1},'Position',[0.41,0.6,0.5,0.3]);
                grid(ax{1},'on'), hold(ax{1},'on')
                ax{3} = axes('Position',[0.41,0.15,0.5,0.3]);
                grid(ax{3},'on'), hold(ax{3},'on')
                AID(0,0,'update')
                return
            elseif strcmp(ax{1}.Tag,'Aerodynamics')
                set(ax{1},'Position',[0.41,0.55,0.5,0.45]);
                ax{3} = axes('Position',[0.41,0.15,0.5,0.3]);
            end
            
            %Axis Properties
            camproj(ax{1},'perspective')    %perspective viewing
            axis(ax{1},'off')               %Set axis visibility off
            view(ax{1},3)                   %Apply view rotation
            axis(ax{1},'equal')             %Correct aspect ratio
            camva(ax{1},5)              	%Zoom/Turn off stretch-to-fit
            
            %Reset Settings
            set(opt(2),'Checked','off') %turn off transparency
            set(opt(3),'Checked','off') %turn off axes
            set(opt(5),'Checked','on')  %turn on shading
            
            %Reset Lighting
            delete(findall(ax{1},'Type','light'))
            
        case 'view' %%%%%%%%%%%%%%%%%%% CHANGE VIEW %%%%%%%%%%%%%%%%%%%%%%%  
            
            %Prescribed View
            delete(findall(ax{1},'Type','light'))
            if strcmp(handle.Label,'Side')
                view(ax{1},[0,0]), 
            elseif strcmp(handle.Label,'Top')
                view(ax{1},[0,90])
            elseif strcmp(handle.Label,'Front')
                view(ax{1},[-90,0])
            end
            
        case 'alpha' %%%%%%%%%%%%%%% ALPHA (TRANSPARENCY) %%%%%%%%%%%%%%%%%    
            
            %Transparency
            if strcmp(check,'off')
                set(handle,'Checked','on');
                alpha(get(opt(2),'UserData'))
            else
                set(handle,'Checked','off');
                alpha(1)
            end
            
        case 'axes' %%%%%%%%%%%%%%%%%%%%% PLOT AXES %%%%%%%%%%%%%%%%%%%%%%%
            
            %Plot Axes (to prevent scaling issues)
            if strcmp(check,'off')
                lim = get(ax{1},{'XLim','YLim','ZLim'});
                set(handle,'Checked','on'); 
                D = BD.X(end)/2;
                plot3(ax{1},[0,0],1.25*[-D,D],[0,0],'k');
                text(0,1.35*D,0,'y');
                plot3(ax{1},[-0.4*D,2.4*D],[0,0],[0,0],'k');
                text(2.45*D,0,0,'x');
                plot3(ax{1},[0,0],[0,0],0.7*[-D,D],'k');
                text(0,0,0.8*D,'z');
                set(ax{1},{'XLim','YLim','ZLim'},lim)
                ax{1}.Clipping = 'off';
                camproj(ax{1},'orthographic')
            else
                set(handle,'Checked','off'); axis(ax{1},'equal')
                delete(findall(ax{1},'Type','line')), ax{2}{11} = [];
                delete(findall(ax{1},'Type','text'))
                camproj(ax{1},'perspective')    %Perspective viewing
            end
            
        case 'dw' %%%%%%%%%%%%%%% INPUT DOWNWASH tabs %%%%%%%%%%%%%%%
            
            if strcmp(check,'off')
                set(handle,'Checked','on');
            else
                prompt = {'Dynamic Pressure Ratio','Downwash Gradient'};
                res_in = get(handle,'UserData');
                default = cell(1,2);
                for i=1:2, default{i} = num2str(res_in(i)); end
                dw = inputdlg(prompt,'Slipstream at Tail',1,default);
                if isempty(dw), dw = default; end
                dw = [eval(dw{1}),eval(dw{2})];
                set(handle,'UserData',dw);
                set(handle,'Checked','off');
            end
            
        case 'color' %%%%%%%%%%%%%%%%%% WHITE BACKGROUND %%%%%%%%%%%%%%%%%%
            
            if strcmp(check,'off')
                set(gcf,'Color',[1,1,1])
                set(handle,'Checked','on');
            else
                set(gcf,'Color',[0.94,0.94,0.94])
                set(handle,'Checked','off');
            end
            
        case 'scale' %%%%%%%%%%%%%%%% SCALE FULL AIRCRAFT %%%%%%%%%%%%%%%%%
            
            value = inputdlg('Scaling Factor','Scale',1,{'1'});
            if ~isempty(value), scale = eval(value{1}); else, scale=1;  end
            
        case 'units' %%%%%%%%%%%%%%%%%%% TOGGLE UNITS %%%%%%%%%%%%%%%%%%%%%
            if handle==opt(14)
                set(opt(17),'Checked',check)
            else
                set(opt(14),'Checked',check)
            end
            prompt = sprintf('Scale dimensions to maintain size?');
            lnew = BD.X(end)-BD.X(1);
            yep = sprintf(' Yes (length will remain %.0f %s) ',BD.X(end)-BD.X(1),unit);
            if strcmp(unit,'in'), lnew = 12*lnew; else, lnew = lnew/12; end
            nope = sprintf(' No (new length will be %.0f %s) ',lnew,unit);
            scl=questdlg(prompt,'Change Units',yep,nope,nope);
            if ~isempty(scl)
                if strcmp(check,'off')
                    set(handle,'Checked','on')
                    if strcmp(scl,yep)
                        scale = 12; 
                        wt = eval(get(AERO_In(4),'String'))/scale;
                        set(AERO_In(4),'String',num2str(wt))
                    else
                        scale = 0;  
                        wt = eval(get(AERO_In(4),'String'))/12;
                        delta_w = 10^(floor(log10(wt))-2);
                        set(AERO_In(4),'String',num2str(wt),'UserData',delta_w)
                    end
                else
                    set(handle,'Checked','off')
                    if strcmp(scl,'Yes')
                        scale = 1/12; 
                        wt = eval(get(AERO_In(4),'String'))/scale;
                        set(AERO_In(4),'String',num2str(wt))
                    else
                        scale = 0;
                        wt = eval(get(AERO_In(4),'String'))*12;
                        delta_w = 10^(floor(log10(wt))-2);
                        set(AERO_In(4),'String',num2str(wt),'UserData',delta_w)
                    end
                end
            end
            
     	case 'units2' %%%%%%%%%%%%%%%%%%% TOGGLE UNITS %%%%%%%%%%%%%%%%%%%%%
            scale = 0;
            if strcmp(check,'off')
                set(handle,'Checked','on')
            else
                set(handle,'Checked','on')
            end
        case 'ac_rgb' %%%%%%%%%%%%%%%%%% ADJUST COLOR %%%%%%%%%%%%%%%%%%%%%
            
            res=get(0,'ScreenSize'); w=140; h=120;
            figure('Position',[(res(3)-w)/2,(res(4)-h)/2,w,h],...
                'Name','Color','NumberTitle','off','MenuBar','none',...
                'Units','normalized','Resize','off');
            axes('Units','normalized','Visible','off');
            x0 = 20; dx = 40; C = get(handle,'UserData');
            r=uicontrol('Style','slider','Value',C(1),'BackgroundColor',...
                [1,0,0],'Position',[x0,10,20,100],'Min',0,'Max',1,...
                'Callback',@R_Slider,'Units','normalized');
            addlistener(r,'ContinuousValueChange',@R_Slider);
            g=uicontrol('Style','slider','Value',C(2),'BackgroundColor',...
                [0,1,0],'Position',[x0+dx,10,20,100],'Min',0,'Max',1,...
                'Callback',@G_Slider,'Units','normalized');
            addlistener(g,'ContinuousValueChange',@G_Slider);
            b=uicontrol('Style','slider','Value',C(3),'BackgroundColor',...
                [0,0,1],'Position',[x0+2*dx,10,20,100],'Min',0,'Max',1,...
                'Callback',@B_Slider,'Units','normalized');
            addlistener(b,'ContinuousValueChange',@B_Slider);
            
        case 'trim' %%%%%%%%%%%%%%%%%%%%%% TRIM %%%%%%%%%%%%%%%%%%%%%%%%%%%
            
            trim = get(handle,'UserData'); delta = trim(2);
            if strcmp(check,'off')
                set(handle,'Checked','on');
                mode = questdlg('Trim Elevator or Incidence and Angle of Attack?',...
                    'Trim Mode','Elevator','WG.i/HT.i/alpha','Elevator');
                if isempty(mode), mode = 'Elevator'; end
                if strcmp(mode,'Elevator')
                    delta = inputdlg('Max Elevator Deflection','Forward CG Limit',1,{num2str(delta)});
                    if isempty(delta), delta = 30; else, delta = str2double(delta); end
                    set(handle,'UserData',[1,delta])
                else
                    set(handle,'UserData',[2,delta])
                end
            else
                set(handle,'Checked','off');
                set(handle,'UserData',[0,delta]);
            end
            
        case 'error' %%%%%%%%%%%%%%%% SET ERROR LIMITS %%%%%%%%%%%%%%%%%%%%
            
            if strcmp(check,'off')
                set(handle,'Checked','on');
                prompt = {'Max Length','Max Angle','Minimums (0 => min(ds))'};
                error_in = get(handle,'UserData');
                default = cell(1,3);
                for i=1:3, default{i} = num2str(error_in(i)); end
                error = inputdlg(prompt,'Input Value Limits',1,default);
                if isempty(error),error = default; end
                error = str2double(error);
                set(handle,'UserData',error);
                
            else
                set(handle,'Checked','off');
            end
            
        case 'cg_lim' %%%%%%%%%%%%%%%%% SCALE CG SLIDER %%%%%%%%%%%%%%%%%%%
            
            if get(handle,'Value')
                set(handle,'Value',1)
                set(AERO_In(end),'Min',WG.X+WG.xmac,...
                    'Max',WG.X+WG.xmac+WG.cbar(end))
                if AERO.XCG < WG.X+WG.xmac
                    AERO.XCG = WG.X+WG.xmac;
                    set(AERO_In(end),'Value',AERO.XCG);
                elseif AERO.XCG > WG.X+WG.xmac+WG.cbar(end)
                    AERO.XCG = WG.X+WG.xmac+WG.cbar(end);
                    set(AERO_In(end),'Value',AERO.XCG);
                end
            else
                set(handle,'Value',0)
                set(AERO_In(end),'Min',0,'Max',BD.X(end))
                
            end
            
        case 'scroll' %%%%%%%%%%%%% SCROLL SENSITIVITY %%%%%%%%%%%%%%%%%%%%
            
            delta = get(handle,'UserData');
            L = BD.X(end)-BD.X(1);
            delta_new = 10^(floor(log10(L))-2);
            p=sprintf('Enter minimum spacing for scroll adjust (%s)',unit);
            out = inputdlg(p,'Scroll Increment',1,{num2str(delta_new)});
            if ~isempty(out), delta = eval(out{1}); end
            set(handle,'UserData',delta)
            
            %Planforms
            DIM={unit,unit,unit,unit,unit,'deg','deg','','deg','deg',...
                'LE-TE','deg','deg',unit,unit,unit};
            DP = zeros(1,length(DIM));
            for i=1:length(DIM)
                if strcmp(DIM{i},unit)
                    DP(i)=delta;
                elseif strcmp(DIM{i},'deg')
                    DP(i)=1;
                else
                    DP(i)=0.01;
                end
            end
            for i=1:length(DP), set(WG_In(i),'UserData',DP(i)), end
            for i=1:length(DP), set(VT_In(i),'UserData',DP(i)), end
            for i=1:length(DP), set(HT_In(i),'UserData',DP(i)), end
            for n=1:length(NP)
                if ~isempty(NP_In{n})
                    for i=1:length(DP)
                        set(NP_In{n}(i),'UserData',DP(i))
                    end
                end
            end
            
            %Controls
            DP = [delta,delta,delta,delta,1,1];
            for i=1:length(DP)-1, set(F_In(i),'UserData',DP(i)), end
            for i=1:length(DP),   set(A_In(i),'UserData',DP(i)), end
            for i=1:length(DP)-1, set(E_In(i),'UserData',DP(i)), end
            for i=1:length(DP)-1, set(R_In(i),'UserData',DP(i)), end
            
            %Body
            for i=1:size(BD_In,1)
                for j=1:size(BD_In,2), set(BD_In(i,j),'UserData',delta),end
            end
            for n=1:size(NB_In)
                if ~isempty(NB_In{n})
                    for i=1:2
                        for j=1:7
                            set(NB_In{n}(i,j),'UserData',delta)
                        end
                    end
                    for j=8:10
                        set(NB_In{n}(1,j),'UserData',delta)
                    end
                end
            end
            
        case 'weights' %%%%%%%%%%%%% WEIGHTS & BALANCE %%%%%%%%%%%%%%%%%%%%
            
            if strcmp(check,'off')
                set(handle,'Checked','on');
                
                %Highlight Unknown Component Weights
                if ~isfield(WG,'XCG'), set(ax{2}{1},'FaceColor','r'), end
                if ~isfield(HT,'XCG'), set(ax{2}{2},'FaceColor','r'); end
                if ~isfield(VT,'XCG'), set(ax{2}{3},'FaceColor','r'); end
                if ~isfield(BD,'XCG'), set(ax{2}{4},'FaceColor','r'); end
                for n=1:length(NP)
                    if ~isempty(NP_In{n})
                        if ~isfield(NP{n},'XCG')
                            set(ax{2}{4+n},'FaceColor','r');
                        end
                    end
                end
                for n=1:length(NB)
                    if ~isempty(NB_In{n})
                        if ~isfield(NB{n},'XCG')
                            set(ax{2}{8+n},'FaceColor','r');
                        end
                    end
                end
                
                %Disable CG Inputs
                set(AERO_In(4:6),'Enable','off')
                set(AERO_In(end),'Visible','off')
            else
                set(handle,'Checked','off');
                
                %Enable CG Inputs
                set(AERO_In(4:6),'Enable','on')
                set(AERO_In(end),'Visible','on')
            end
            
        case 'shape' %%%%%%%%%%% FUSELAGE CROSS-SECTION TYPE %%%%%%%%%%%%%%
            
            set(BD_In(3,:),'String','')
            if all(BD.P==0)
                set(BD_In(3,[1,min([BD.NX,11])]),'String','1')
            elseif all(BD.P>0) && all(BD.P<5)
                set(BD_In(3,[1,min([BD.NX,11])]),'String','5')
            else
                set(BD_In(3,[1,min([BD.NX,11])]),'String','0')
            end
            
        case 'shape1' %%%%%%%%%%% BODY 1 CROSS-SECTION TYPE %%%%%%%%%%%%%%%
            
            set(NB_In{1}(3,1:7),'String','')
            if all(NB{1}.P==0)
                set(NB_In{1}(3,[1,min([NB{1}.NX,7])]),'String','1')
            elseif all(NB{1}.P>0) && all(NB{1}.P<5)
                set(NB_In{1}(3,[1,min([NB{1}.NX,7])]),'String','5')
            else
                set(NB_In{1}(3,[1,min([NB{1}.NX,7])]),'String','0')
            end
            
        case 'shape2' %%%%%%%%%%% BODY 2 CROSS-SECTION TYPE %%%%%%%%%%%%%%%
            
            set(NB_In{2}(3,1:7),'String','')
            if all(NB{2}.P==0)
                set(NB_In{2}(3,[1,min([NB{2}.NX,7])]),'String','1')
            elseif all(NB{2}.P>0) && all(NB{2}.P<5)
                set(NB_In{2}(3,[1,min([NB{2}.NX,7])]),'String','5')
            else
                set(NB_In{2}(3,[1,min([NB{2}.NX,7])]),'String','0')
            end
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%% SCALE FUNCTION %%%%%%%%%%%%%%%%%%%%%%%%%%%%
    if scale~=1
        if ~scale, scale = 1; end
        RP={'CHRDR','CHRDBP','CHRDTP','SSPN','SSPNOP','SAVSI',...
            'SAVSO','CHSTAT','DHDADI','DHDADO','TC','TWISTA',...
            'i','X','Y','Z'};
        RB={'X','ZU','ZL','R'};
        index = [1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1]; %length dimensions
        for i=1:length(RP)                                  %Planforms
            if index(i)
                set(WG_In(i),'String',num2str(WG.(RP{i})*scale))
                set(HT_In(i),'String',num2str(HT.(RP{i})*scale))
                set(VT_In(i),'String',num2str(VT.(RP{i})*scale))
            end
        end
        for n=1:length(NP)                                  %Added Planform
            if ~isempty(NP_In{n})
                for i=1:length(RP)
                    if index(i)
                        set(NP_In{n}(i),'String',...
                            num2str(NP{n}.(RP{i})*scale))
                    end
                end
            end
        end
        for i=1:length(RB), BD.(RB{i}) = BD.(RB{i})*scale; end  %Body
        for i=1:11
            set(BD_In(2,i),'String',num2str(BD.X(BD.N(i))))
        end
        RB(end+1:end+3)={'X0','Y0','Z0'};
        for n=1:length(NB)                                      %Added Body
            if ~isempty(NB_In{n})
                for i=1:length(RB), NB{n}.(RB{i})=NB{n}.(RB{i})*scale; end
                for i=1:7
                    set(NB_In{n}(2,i),'String',num2str(NB{n}.X(NB{n}.N(i))))
                end
                set(NB_In{n}(1,8),'String',num2str(NB{n}.X0))
                set(NB_In{n}(1,9),'String',num2str(NB{n}.Y0))
                set(NB_In{n}(1,10),'String',num2str(NB{n}.Z0))
            end
        end
        
        %AERO Parameters
        delta_w = 10^(floor(log10(AERO.WT(1)*scale))-2);
        set(AERO_In(4),'UserData',delta_w)
        for i=4:8
            val = eval(get(AERO_In(i),'String'))*scale;
            set(AERO_In(i),'String',num2str(val))
        end
        
        %Re-Initialize Unit Labels
        if strcmp(choice,'units') || strcmp(choice,'units2')
            Initialize_GUI, return %refresh GUI
        else
            setting(opt(16),0,'scroll') %update scroll sensitivity
        end
        
    end
    
else
    
    %Toggle Value
    if isprop(handle,'Checked')
        if strcmp(check,'off')
            set(handle,'Checked','on');
        else
            set(handle,'Checked','off');
        end
    elseif isprop(handle,'Value')
        if check
            set(handle,'Value',1);
        else
            set(handle,'Value',0);
        end
    end
end

if update, AID(0,0,'update'), end

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SLIDERS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% CG ADJUST %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function sliderCallback(handle,~)
global AERO_In AERO opt

AERO.XCG=get(handle,'Value');
set(AERO_In(5),'String',num2str(AERO.XCG))
set(opt(2),'UserData',0.3,'Checked','on')
AID(0,0,'update','cg')

end

function sliderRelease(~,~)
global opt

set(opt(2),'Checked','off')
AID(0,0,'update')

end

%%%%%%%%%%%%%%%%%%%%%%%%%%%% COLOR ADJUST RED %%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function R_Slider(handle,~)
global opt

r=get(handle,'Value');
rgb=get(opt(7),'UserData');
set(opt(7),'UserData',[r,rgb(2:3)])
AID(0,0,'update','rgb')

end

%%%%%%%%%%%%%%%%%%%%%%%%%%% COLOR ADJUST GREEN %%%%%%%%%%%%%%%%%%%%%%%%%%%%

function G_Slider(handle,~)
global opt

g=get(handle,'Value');
rgb=get(opt(7),'UserData');
set(opt(7),'UserData',[rgb(1),g,rgb(3)])
AID(0,0,'update','rgb')

end

%%%%%%%%%%%%%%%%%%%%%%%%%%%% COLOR ADJUST BLUE %%%%%%%%%%%%%%%%%%%%%%%%%%%%

function B_Slider(handle,~)
global opt

b=get(handle,'Value');
rgb=get(opt(7),'UserData');
set(opt(7),'UserData',[rgb(1:2),b])
AID(0,0,'update','rgb')

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%% IMAGE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Image(handle,~,action,c)
global ax opt lib_path

%Either Load or Adjust Image
switch action
    case 'load'
        %if exist('3Views','dir') cd 3Views, fl = 1; else, fl = 0; end
        [File,Path]=uigetfile({'*.png;*.jpg;*.gif','Image Files'},...
            'Choose Background Image File',fullfile(lib_path,'3Views')); 
        %if fl, cd .., end
        fname=[Path,File];
        if ~isempty(File) && ischar(File)
            if ~isempty(ax{4}), cla(ax{4}{1}), end
            ax{4}{1} = axes('Units','normalized','Position',[0,0,1,1]);
            uistack(ax{4}{1},'bottom')
            ax{4}{2} = imread(fname);
            %if length(size(ax{4}{2}))>2, ax{4}{2} = rgb2gray(ax{4}{2}); end
            ax{4}{3} = imshow(ax{4}{2});
            ax{4}{3}.UIContextMenu = c;
            set(ax{4}{1},'HandleVisibility','off','Visible','off')
            if strcmp(get(opt(3),'Checked'),'off')
                setting(opt(3),0,'axes')%plot axes to reduce scaling issues
            end
            set(opt(2),'UserData',0.7,'Checked','on') %set transparency
        end
        
    case 'flip'
        
        if isempty(ax{4})
            %warndlg('No background image has been loaded.')
        else
            if strcmp(handle.Checked,'off')
                handle.Checked = 'on';
                ax{4}{1}.XDir = 'reverse';
            else
                handle.Checked = 'off';
                ax{4}{1}.XDir = 'normal';
            end
        end
        
    case 'rotate'
        
        if isempty(ax{4})
            %warndlg('No background image has been loaded.')
        else
            ax{4}{3}.CData = imrotate(ax{4}{3}.CData,90);
        end
        
    case 'show'
        
        if strcmp(handle.Checked,'on')
            handle.Checked = 'off';
            a = ax{4}{1}; ax{4}{1} = axes; props = {'Position','XDir'};
            set(ax{4}{1},props,get(a,props))
            uistack(ax{4}{1},'bottom')
            ax{4}{3} = imshow(ax{4}{2});
            ax{4}{3}.UIContextMenu = c;
            if strcmp(get(opt(3),'Checked'),'off')
                setting(opt(3),0,'axes') %plot axes to reduce scaling issues
            end
            set(opt(2),'UserData',0.7,'Checked','on') %set transparency
        elseif ~isempty(ax{4}) %hide
            delete(ax{4}{3})
            handle.Checked = 'on';
            if strcmp(get(opt(3),'Checked'),'on')
                setting(opt(3),0,'axes') %turn off axis plot
            end
            set(opt(2),'UserData',0.7,'Checked','off') %set transparency
        end
        
    otherwise
        if strcmp(handle.Style,'checkbox')
            if handle.Value
                ax{4}{1}.UserData = 1;
            else
                ax{4}{1}.UserData = 0;
            end
        end
end

%Update
axes(ax{1})
AID(0,0,'update')

end

%%%%%%%%%%%%%%%%%%%%%%%%%%%% SCROLL WHEEL %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Scroll(~,object)
global ax WG HT VT BD F A E R NP NB AERO ATM

obj = gco; delta = 0;
if ~isempty(obj) && isprop(gco,'String') && strcmp(obj.Type,'uicontrol')
    delta = obj.UserData; 
end
if isempty(delta) || length(delta)>1, delta = 0; end
if ispc, delta=-delta; end %fix scroll direction
if delta
    if isempty(obj.String), obj.String = 1; end %adjusting empty P inputs
    value = eval(obj.String);
    if ~isnan(value)
        value = value + delta*object.VerticalScrollCount;
        obj.String = num2str(value);
        AID(obj,0,'update')
    end
elseif ~isempty(obj) && (strcmp(obj.Type,'axes') || strcmp(obj.Type,'image'))
    if strcmp(obj.Type,'image'), obj = ax{4}{1}; bg=1; else,  bg=0; end
    pos = obj.CurrentPoint; 
    x0 = pos(1,1);              y0 = pos(1,2);
    xlim = obj.XLim;            ylim = obj.YLim;
    xrange = xlim(2)-xlim(1);   yrange = ylim(2)-ylim(1);
    xp = (x0-xlim(1))/xrange;   yp = (y0-ylim(1))/yrange;
    dx = -xrange/10*object.VerticalScrollCount;
    dy = -yrange/10*object.VerticalScrollCount;
    if bg
        dx = -dx/xrange/10; dy = -dy/yrange/10; yp = 1-yp;
        obj.Position(1) = obj.Position(1) - dx*xp;
        obj.Position(2) = obj.Position(2) - dy*yp;
        if obj.Position(3) + dx > 0.1
            obj.Position(3) = obj.Position(3) + dx;
        end
        if obj.Position(4) + dy > 0.1
            obj.Position(4) = obj.Position(4) + dy;
        end
    else
        obj.XLim = obj.XLim + [-dx*xp,dx*(1-xp)];
        obj.YLim = obj.YLim + [-dy*yp,dy*(1-yp)];
    end
elseif strcmp(ax{1}.Tag,'Stability')  
    scale = object.VerticalScrollCount/100;
    ax{1}.Position(3:4) = ax{1}.Position(3:4)*(1+scale);
    ax{3}.Position(3:4) = ax{3}.Position(3:4)*(1+scale);
else
    cm = camva(ax{1});
    camva(ax{1},max([cm-object.VerticalScrollCount/5,0.1]))
end
end

function Isolate(f,~,release)%%%%%%%%%%%%%%%% ISOLATE %%%%%%%%%%%%%%%%%%%%%
global ax tabs opt

%Isolate or Replot Figure
tab = get(get(tabs,'SelectedTab'),'Title');
labels = {'Wing','HT','VT','Body','Wing 2','HT 2','VT 2','Prop','Body 2','Body 3'};
selected = strcmp(tab,labels);
key = get(f,'CurrentKey');
%if strcmp(key,'shift'), release = 1; end % comment to free up cmd+shift for screen capture screenshot
if strcmp(key,'space') && ~isempty(gco) && isprop(gco,'Style') && strcmp(get(gco,'Style'),'edit') %clear edit box
    set(gco,'String',''), AID(gco,0,'update')
elseif release
    set(gcf,'Pointer','arrow')
    set(gcf,'WindowButtonDownFcn',@Click)
    if strcmp(get(opt(3),'Checked'),'on') && strcmp(get(opt(3),'Tag'),'off') 
       	setting(opt(3),0,'axes') %plot axes if previously on
   	end
    for i=1:length(labels)
        if isprop(ax{2}{i},'FaceAlpha')
            if strcmp(get(opt(2),'Checked'),'on')
                set(ax{2}{i},'FaceAlpha',get(opt(2),'UserData'))
                set(ax{2}{i},'PickableParts','visible')
            else
                set(ax{2}{i},'FaceAlpha',1,'PickableParts','visible')
            end
        end
    end
elseif strcmp(key,'shift') && strcmp(ax{1}.Tag,'Geometry') %drag or "shift" component
    set(gcf,'Pointer','hand')
    if strcmp(get(opt(3),'Checked'),'off')
        set(opt(3),'Tag','off'), setting(opt(3),0,'axes')
    else
        set(opt(3),'Tag','on')
    end
else %(strcmp(key,'control') || strcmp(key,'0')) && strcmp(ax{1}.Tag,'Geometry')
    %set(gcf,'Pointer','hand')
    set(gcf,'WindowButtonDownFcn',{@Click,1})
%    	if strcmp(get(opt(3),'Checked'),'off')
%         set(opt(3),'Tag','off'), setting(opt(3),0,'axes') 
%     else
%       	set(opt(3),'Tag','on')
%     end
    for i=1:length(labels)
        if ~selected(i)
            if isprop(ax{2}{i},'FaceAlpha')
                set(ax{2}{i},'FaceAlpha',0.1,'PickableParts','none')
            end
        end
    end
end
end

%% %%%%%%%%%%%%%%%%%%%%%%%%% MOUSE CONTROLS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Click(h,~,key)
global ax tabs

%Distinguish Click Type
obj = gco;
if nargin<3, key = 0; end
f = ancestor(h,'figure');
click = get(f,'SelectionType');
ax{1}.UserData = f.CurrentPoint;
tab_list = get(tabs,'Children');
f.WindowButtonUpFcn = {@Release,ax{1}.UserData}; 

%Manipulate Image or Jump to Component
if ~isempty(ax{4}) && isvalid(ax{4}{3}) && ~strcmp(obj.Type,'surface')
    %Manipulate Image
    if strcmp(click,'normal') || isempty(click)
        f.WindowButtonMotionFcn = {@Drag,f,'drag image'};
    elseif strcmp(click,'extend')
        f.WindowButtonMotionFcn = {@Drag,f,'scale image'};
    elseif strcmp(click,'alt')
        f.WindowButtonMotionFcn = {@Drag,f,'scale image 2'};
    end
elseif strcmp(obj.Type,'line') && strcmp(ax{1}.Tag,'Stability')
    if strcmp(click,'normal') %manipulate plot
        set(tabs,'SelectedTab',tab_list(6))
        f.WindowButtonMotionFcn = {@Drag,f,'drag line',obj};
    end
elseif strcmp(obj.Type,'axes')
   	if strcmp(click,'open')
        f1=figure('NumberTitle','off','MenuBar','none','Units','normalized');
        set(f1,'Name','Extracted Plot')
        fpos = f.Position; %main figure
        apos = obj.Position; %axes
        f1.Position = [fpos(1:2),0,0] + apos.*[fpos(3:4),fpos(3:4)];
        f1.Position = f1.Position+[-apos(3),-apos(4),2*apos(3),2*apos(4)]/8;
        a = copyobj(obj,f1); a.Position = [0.125,0.125,0.775,0.775];
        if ~isempty(obj.Legend), legend(a,obj.Legend.String); end
        assignin('base','a',a)
        fprintf('\nWrote current axes handle, a, to base workspace\n'), a
    elseif strcmp(click,'normal')
        obj.UserData = obj.CurrentPoint;
        f.WindowButtonMotionFcn = {@Drag,f,'drag axes',obj};
    elseif strcmp(click,'alt')
        set(gcf,'Pointer','hand')
        obj.UserData = f.CurrentPoint;
        f.WindowButtonMotionFcn = {@Drag,f,'pan',obj};
    
    end
elseif strcmp(obj.Type,'surface') && ~strcmp(click,'normal')
    if strcmp(click,'extend') || key
        set(gcf,'Pointer','hand')
        part = get(obj,'Tag');
        ax{1}.UserData = f.CurrentPoint;
        y_avg = round(mean(mean(obj.YData)),6);
        if y_avg == 0, dir = -1; else, dir = y_avg/abs(y_avg); end
        f.WindowButtonMotionFcn = {@Drag,f,'drag component',part,dir};
    elseif strcmp(click,'alt')
        ax{1}.UserData = f.CurrentPoint;
        f.WindowButtonMotionFcn = {@Drag,f,'pan'};
    end
elseif ~isempty(strfind(obj.Tag,'Report')) && strcmp(click,'alt')
    ax{1}.UserData = f.CurrentPoint;
  	f.WindowButtonMotionFcn = {@Drag,f,'drag report',obj.Tag};
elseif strcmp(click,'open') %double click figure, plot refresh fix
    refresh.String = ax{1}.Tag;
    AID(refresh,0,'change_ax')
elseif ~strcmp(obj.Type,'uicontrol') 
    %Drag to Rotate/Pan
    %if (strcmp(click,'normal') && ~key) || ~strcmp(obj.Type,'surface')
    set(gcf,'Pointer','crosshair')
    cursor = NaN(16,16,3); %cool little airplane cursors
    %top view
    cursor([7,10],2:12,1)=1; cursor([1,16],7:9,1)=1; cursor(4:13,16,1)=1;
    cursor([5:6,11:12],[5,14],1)=1; cursor([4,13],[5,15],1)=1;
    cursor([2:3,14:15],6,1)=1; cursor(8:9,[1,13:16],1)=1;
    cursor([1:7,10:16],9,1)=1;
    %front view
    cursor([4:8,12],8:9,2)=1; cursor(8,[1:2,15:16],2)=1;
    cursor(8:9,[2:4,7,10,13:15],2)=1; cursor(9:10,[4:7,10:13],2)=1;
    cursor(11:11,[6:7,10:11],2)=1;
    %side view
    cursor(3,15:16,3)=1; cursor(3:9,16,3)=1; cursor(6,13:15,3)=1;
    cursor(6,3:12,3)=1; cursor(4,14,3)=1; cursor(5,13,3)=1;
    cursor(8,[1,5:9],3)=1; cursor(10,3:15,3)=1; cursor([7,9],2,3)=1;
    ax{1}.UserData = f.CurrentPoint;
    f.WindowButtonMotionFcn = {@Drag,f,'rotate',cursor};
end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% MOUSE DRAG %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function Drag(~,~,f,choice,part,dir)
global ax opt WG WG_In HT HT_In VT VT_In BD NP NP_In NB NB_In ...
    F F_In E E_In AC AERO AERO_In ATM tabs 

%Mouse Position
if nargin<5 || ischar(part) || length(part)>1, a=ax{1}; else, a=part; end
if ~isvalid(a), return, end
if strcmp(a.Type,'axes')
    pt_old = a.UserData;
    pt_new = f.CurrentPoint;
    dx = pt_new(1,1) - pt_old(1,1);
    dy = pt_new(1,2) - pt_old(1,2);
end

%Drag Type
switch choice
    case 'rotate'
        [Az,El] = view;
        Az = Az - dx*360;
        El = El - dy*360;
        El = min([max([El,-90]),90]); %limit to +/- 90deg
        view(ax{1},[Az,El])
     	set(f,'Pointer','custom'); %angle test for dragging along axis 
        if El>45 %top view
            set(f,'PointerShapeCData',part(:,:,1));
        elseif abs(El)<=15 && abs(abs(rem(Az,180))-90)<30 %front view
            set(f,'PointerShapeCData',part(:,:,2));
        else %side view
            set(f,'PointerShapeCData',part(:,:,3));
        end
        delete(findall(ax{1},'Type','light'))
        camlight(-15,30), camlight(15,30)
    case 'drag component'
        L = BD.X(end)-BD.X(1);
        switch part
            case {'WG','WGtip'}
                PT_In = WG_In; PT = WG; plnf = 1;
            case {'HT','HTtip'}
                PT_In = HT_In; PT = HT; plnf = 1;
            case {'VT','VTtip'}
                PT_In = VT_In; PT = VT;  plnf = 1;
            case {'NP{1}','NP{1}tip'}
                PT_In = NP_In{1}; PT = NP{1}; plnf = 1;
            case {'NP{2}','NP{2}tip'}
                PT_In = NP_In{2}; PT = NP{2}; plnf = 1;
            case {'NP{3}','NP{3}tip'}
                PT_In = NP_In{3}; PT = NP{3}; plnf = 1;
            case 'NP{4}'
                PT_In = NP_In{4}; PT = NP{4}; plnf = 1;
            case {'NB{1}'}
                PT_In = NB_In{1}; PT = NB{1}; plnf = 0;
            case {'NB{2}'}
                PT_In = NB_In{2}; PT = NB{2}; plnf = 0;
            otherwise
                return
        end
        set(tabs,'SelectedTab',get(PT_In(1,1),'Parent'))
        
        %Update
        [Az,El] = view; Az = rem(Az,360);
        theta = atan2d(dy,dx); ds = sqrt(dx^2+dy^2);
        psi = -Az; if psi>180, psi = psi - 360; end
        if psi>90
            psi = 180-(180-psi)*sind(El);
        elseif psi<-90
            psi = -180+(180+psi)*sind(El);
        elseif abs(psi)<80
            psi = psi*sind(El);
        end
        rho = 90-Az; if rho>180, rho = rho - 360; end
        if rho>90
            rho = 180-(180-rho)*sind(El);
        elseif rho<-90
            rho = -180+(180+rho)*sind(El);
        elseif abs(rho)<80
            rho = rho*sind(El);
        end
        phi = 90;
        fudge = [(sind(El)+abs(cosd(Az)))/2,(sind(El)+abs(sind(Az)))/2,1/2];
        fudge = fudge*2;
        DX = ds*cosd(theta-psi)*fudge(1)*L;         %dot product with x-axis
        DY = ds*cosd(theta-rho)*fudge(2)*L*dir;     %dot product with y-axis
        DZ = ds*cosd(theta-phi)*cosd(El)*fudge(3)*L;%dot product with z-axis
        if plnf
            if abs(DX)>abs(DY) && abs(DX)>abs(DZ)
                set(PT_In(14),'String',num2str(round(PT.X+DX,2)))
                AID(PT_In(14),0,'update')
            elseif abs(DY)>abs(DX) && abs(DY)>abs(DZ)
                PT.Y = PT.Y+DY; if abs(PT.Y)<L/50, PT.Y = 0; end
                set(PT_In(15),'String',num2str(round(PT.Y,2)))
                AID(PT_In(15),0,'update')
            elseif abs(DZ)>abs(DX) && abs(DZ)>abs(DY)
                set(PT_In(16),'String',num2str(round(PT.Z+DZ,2)))
                AID(PT_In(16),0,'update')
            end
        else
            if abs(DX)>abs(DY) && abs(DX)>abs(DZ)
                set(PT_In(1,8),'String',num2str(round(PT.X0+DX,2)))
                AID(PT_In(1,8),0,'update')
            elseif abs(DY)>abs(DX) && abs(DY)>abs(DZ)
                PT.Y0 = PT.Y0+DY; if abs(PT.Y0)<L/50, PT.Y0 = 0; end
                set(PT_In(1,9),'String',num2str(round(PT.Y0,2)))
                AID(PT_In(1,9),0,'update')
            elseif abs(DZ)>abs(DX) && abs(DZ)>abs(DY)
                set(PT_In(1,10),'String',num2str(round(PT.Z0+DZ,2)))
                AID(PT_In(1,10),0,'update')
            end
        end
    case 'drag report'
        reports = get(f,'UserData');
        space = strfind(part,' ');
        i = str2double(part(space+1:end));
        for j=1:length(reports{i,1})
            pos = get(reports{i,1}(j),'Position');
            pos(1) = pos(1) + dx;
            pos(2) = pos(2) + dy;
            set(reports{i,1}(j),'Position',pos);
        end
        set(f,'UserData',reports);
    case 'drag line'
        a = ancestor(a,'Axes');
     	pt_new = a.CurrentPoint; pt_old = a.UserData;
        if isempty(pt_old), pt_old = pt_new; end
        dx = pt_new(1,1) - pt_old(1,1);
        dy = pt_new(1,2) - pt_old(1,2);
        a.UserData = pt_new;
        if dx || dy
            tab_list = get(tabs,'Children');
            if abs(dy)>abs(dx)
                set(tabs,'SelectedTab',tab_list(4))
                if strcmp(a.Tag,'Stability')
                    obj = F_In(5);
                    CL = pt_new(1,2);
                    dCL = CL - AC.CL; delta = dCL/AC.CLdf;
                    set(obj,'String',num2str(F.DELTA+delta))
                else
                    obj = E_In(5);
                    Cm_new = pt_new(1,2);
                    dCm = Cm_new - AC.Cm; delta = dCm/AC.Cmde;
                    CL = AC.CL + AC.CLde*delta;
                    set(obj,'String',num2str(E.DELTA+delta))
                end
            else
                set(tabs,'SelectedTab',tab_list(6))
                obj = AERO_In(1);
                alpha_new = pt_new(1,1); CL = AC.CL0+AC.CLa*alpha_new;
                set(obj,'String',num2str(round(alpha_new,2)))
            end
            mach_new = sqrt(2*AERO.WT/(CL*WG.S(end)*ATM.D))/ATM.a;
            if strcmp(get(opt(14),'Checked'),'on'); mach_new=mach_new*12; end
            set(AERO_In(3),'String',num2str(mach_new))
            AID(obj,0,'update')
            return
        end
    case 'drag axes'
        pt_new = a.CurrentPoint;
        dx = pt_new(1,1) - pt_old(1,1);
        dy = pt_new(1,2) - pt_old(1,2);
        a.XLim = a.XLim - dx;
        a.YLim = a.YLim - dy;
        pt_new = pt_old;
        %uistack(a,'Top') axes(a)
    case 'pan'
        %set(gcf,'Pointer','fleur')
        pos = a.Position;
        pos(1) = pos(1) + dx;
        pos(2) = pos(2) + dy;
        a.Position = pos;
    case 'drag image'
        set(gcf,'Pointer','hand')
        pos = get(ax{4}{1},'Position');
        pos(1) = pos(1)+dx; pos(2) = pos(2)+dy;
        ax{4}{1}.Position = pos;
    case 'scale image'
        set(gcf,'Pointer','topr')
        pos = get(ax{4}{1},'Position');
        pos(1) = pos(1)-dx/2; pos(2) = pos(2)-dy/2;
        pos(3) = pos(3)+dx; pos(4) = pos(4)+dy;
        ax{4}{1}.Position = pos;
    case 'scale image 2'
        pos = get(ax{4}{1},'Position');
        w_h=pos(3)/pos(4);
        if abs(dx)>abs(dy)
            dy = w_h*dx; set(gcf,'Pointer','top')
        else
            dx = dy/w_h; set(gcf,'Pointer','right')
        end
        pos(1) = pos(1)-dx/2; pos(2) = pos(2)-dy/2;
        pos(3) = pos(3)+dx; pos(4) = pos(4)+dy;
        ax{4}{1}.Position = pos;
end
a.UserData = pt_new;

end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% RELEASE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function Release(f,~,pt_original)
global ax opt tabs WG WG_In HT HT_In VT VT_In BD BD_In NB NB_In NP NP_In

%Disable Drag
f.WindowButtonMotionFcn = '';
f.Pointer = 'arrow';
%if ~strcmp(f.Pointer,'watch'), set(f,'Pointer','arrow'), end

%Check if Dragged
dragged = ~isequal(pt_original,f.CurrentPoint);
surface = strcmp(get(gco,'Type'),'surface');
line = strcmp(get(gco,'Type'),'quiver') || strcmp(get(gco,'Type'),'line');
aero = strcmp(ax{1}.Tag,'Aerodynamics');

%Distinguish Click Type
click = get(f,'SelectionType');
open = strcmp(click,'open');
inch = get(opt(14),'Checked');
if strcmp(inch,'on'), unit = 'in'; else, unit = 'ft'; end

%Clear Existing Lines
if ~isempty(ax{2}{11}), delete(ax{2}{11}), ax{2}{11} = []; end

%Prevent Triple Click and Component Selection Fix
if strcmp(ax{1}.Tag,'Geometry')
    if isempty(ax{3}) && iscell(ax{3})
        dragged = 0; 
    else
        if ax{3}==0, pause(0.2), ax{3} = []; return, end
    end
    if open, ax{3} = 0; end
end

%Jump to Part
part = get(gco,'Tag'); if isempty(part), part = ''; end
tab_list = get(tabs,'Children');

%Only if not dragged
if surface && ~dragged
    if ~strcmp(click,'alt')
        
        %Wait for Double Click
        if ~open && ~iscell(ax{3}) && strcmp(ax{1}.Tag,'Geometry')
            %pause(0.2), 
            if ~isempty(ax{3}) && ~iscell(ax{3}), return, end
        end
        switch part
            case 'WG'
                select = tabs.SelectedTab==tab_list(1); %already on tab
                set(tabs,'SelectedTab',tab_list(1))
                if open && ~aero
                    Profile_Sketcher(0,0,'Wing Airfoil',unit,{'side',1})
                else
                    [Az,El] = view(ax{1});
                    click_pos = Data_Point(f);
                    x1 = click_pos(1); y1 = abs(click_pos(2));
                    Planform_Select(f,Az,El,WG,WG_In,x1,y1,select)
                end
            case 'HT'
                select = tabs.SelectedTab==tab_list(2);
                set(tabs,'SelectedTab',tab_list(2))
                if open && ~aero
                    Profile_Sketcher(0,0,'HT Airfoil',unit,{'side',1})
                else
                    [Az,El] = view(ax{1});
                    click_pos = Data_Point(f);
                    x1 = click_pos(1); y1 = abs(click_pos(2));
                    Planform_Select(f,Az,El,HT,HT_In,x1,y1,select)
                end
            case 'VT'
                select = tabs.SelectedTab==tab_list(3);
                set(tabs,'SelectedTab',tab_list(3))
                if open && ~aero
                    Profile_Sketcher(0,0,'VT Airfoil',unit,{'top',1})
                else
                    [Az,El] = view(ax{1});
                    click_pos = Data_Point(f);
                    x1 = click_pos(1); y1 = click_pos(3);
                    Planform_Select(f,Az,El,VT,VT_In,x1,y1,select,'v')
                end
            case 'WGtip'
                set(tabs,'SelectedTab',tab_list(1))
                if open && ~aero
                    Profile_Sketcher(0,0,'Wing Airfoil',unit,{'side',2})
                else
                    set(gco,'UserData','CHRDTP')
                    if ~iscell(ax{3}) 
                        set(f,'CurrentObject',WG_In(3))
                        AID(WG_In(3),0,'update')
                    end
                end
            case 'HTtip'
                set(tabs,'SelectedTab',tab_list(2))
                if open && ~aero
                    Profile_Sketcher(0,0,'HT Airfoil',unit,{'side',2})
                else
                    set(gco,'UserData','CHRDTP')
                    if iscell(ax{3})
                        set(f,'CurrentObject',HT_In(3))
                        AID(HT_In(3),0,'update')
                    end
                end
            case 'VTtip'
                set(tabs,'SelectedTab',tab_list(3))
                if open && ~aero
                    Profile_Sketcher(0,0,'VT Airfoil',unit,{'top',2})
                else
                    set(gco,'UserData','CHRDTP')
                    if ~iscell(ax{3}) 
                        set(f,'CurrentObject',VT_In(3))
                        AID(VT_In(3),0,'update')
                    end
                end
            case {'F','A','E','R'}
                set(tabs,'SelectedTab',tab_list(4))
            case 'BD'
                select = tabs.SelectedTab==tab_list(5); %already on tab
                set(tabs,'SelectedTab',tab_list(5))
                if open && ~aero
                    Profile_Sketcher(0,0,'Fuselage',unit)
                elseif select
                    click_pos = Data_Point(f);
                    [~,n] = min(abs(BD.X-click_pos(1)));
                    [~,N] = min(abs(BD.X(BD.N)-BD.X(n)));
                    set(BD_In(:,N),'Enable','on')
                    set(BD_In(1,N),'String',num2str(n))
                    set(BD_In(2,N),'String',num2str(round(BD.X(n),1)))
                    set(f,'CurrentObject',BD_In(3,N))
                    if isempty(get(BD_In(3,N),'String'))
                        set(BD_In(3,N),'String',num2str(round(BD.P(n),1)))
                    end
                    AID(BD_In(3,N),0,'update')
                end
                
            case {'NP{1}'}
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'Wing 2'), break, end
                end
                select = tabs.SelectedTab==tab_list(i);
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                    Profile_Sketcher(0,0,'Wing 2 Airfoil',unit,{'side',1})
                else
                    [Az,El] = view(ax{1});
                    click_pos = Data_Point(f);
                    x1 = click_pos(1); y1 = abs(click_pos(2));
                    Planform_Select(f,Az,El,NP{1},NP_In{1},x1,y1,select)
                end
            case {'NP{2}'}
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'HT 2'), break, end
                end
                select = tabs.SelectedTab==tab_list(i);
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                    Profile_Sketcher(0,0,'HT 2 Airfoil',unit,{'side',1})
                else
                    [Az,El] = view(ax{1});
                    click_pos = Data_Point(f);
                    x1 = click_pos(1); y1 = abs(click_pos(2));
                    Planform_Select(f,Az,El,NP{2},NP_In{2},x1,y1,select)
                end
            case {'NP{3}'}
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'VT 2'), break, end
                end
                select = tabs.SelectedTab==tab_list(i);
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                    Profile_Sketcher(0,0,'VT 2 Airfoil',unit,{'top',1})
                else
                    [Az,El] = view(ax{1});
                    click_pos = Data_Point(f);
                    x1 = click_pos(1); y1 = click_pos(3);
                    Planform_Select(f,Az,El,NP{3},NP_In{3},x1,y1,select,'v')
                end
            case {'NP{4}'}
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'Prop'), break, end
                end
                select = tabs.SelectedTab==tab_list(i);
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                else
                    [Az,El] = view(ax{1});
                    click_pos = Data_Point(f);
                    x1 = click_pos(1); y1 = click_pos(3);
                    Planform_Select(f,Az,El,NP{4},NP_In{4},x1,y1,select,'v')
                end
            case 'NP{1}tip'
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'Wing 2'), break, end
                end
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                    Profile_Sketcher(0,0,'Wing 2 Airfoil',unit,{'side',2})
                else
                    set(gco,'UserData','CHRDTP')
                    if ~iscell(ax{3}) 
                        set(f,'CurrentObject',NP_In{1}(3))
                        AID(NP_In{1}(3),0,'update')
                    end
                end
            case 'NP{2}tip'
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'HT 2'), break, end
                end
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                    Profile_Sketcher(0,0,'HT 2 Airfoil',unit,{'side',2})
                else
                    set(gco,'UserData','CHRDTP')
                    if ~iscell(ax{3}) 
                        set(f,'CurrentObject',NP_In{2}(3))
                        AID(NP_In{2}(3),0,'update')
                    end
                end
            case 'NP{3}tip'
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'VT 2'), break, end
                end
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                    Profile_Sketcher(0,0,'VT 2 Airfoil',unit,{'top',2})
                else
                    set(gco,'UserData','CHRDTP')
                    if ~iscell(ax{3}) 
                        set(f,'CurrentObject',NP_In{3}(3))
                        AID(NP_In{3}(3),0,'update')
                    end
                end
            case {'NB{1}'}
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'Body 2'), break, end
                end
                select = tabs.SelectedTab==tab_list(i); %already on tab
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                    Profile_Sketcher(0,0,'Body 2',unit),
                elseif select
                    click_pos = Data_Point(f);
                    [~,n] = min(abs(NB{1}.X+NB{1}.X0-click_pos(1)));
                    [~,N] = min(abs(NB{1}.X(NB{1}.N)-NB{1}.X(n)));
                    set(NB_In{1}(:,N),'Enable','on')
                    set(NB_In{1}(1,N),'String',num2str(n))
                    set(NB_In{1}(2,N),'String',num2str(round(NB{1}.X(n),1)))
                    set(f,'CurrentObject',NB_In{1}(3,N))
                    if isempty(get(NB_In{1}(3,N),'String'))
                        set(NB_In{1}(3,N),'String',num2str(round(NB{1}.P(n),1)))
                    end
                    AID(NB_In{1}(3,N),0,'update')
                end
            case {'NB{2}'}
                for i=6:length(tab_list)
                    if strcmp(get(tab_list(i),'Title'),'Body 3'), break, end
                end
                select = tabs.SelectedTab==tab_list(i); %already on tab
                set(tabs,'SelectedTab',tab_list(i))
                if open && ~aero
                    Profile_Sketcher(0,0,'Body 3',unit)
                elseif select
                    click_pos = Data_Point(f);
                    [~,n] = min(abs(NB{2}.X+NB{2}.X0-click_pos(1)));
                    [~,N] = min(abs(NB{2}.X(NB{2}.N)-NB{2}.X(n)));
                    set(NB_In{2}(:,N),'Enable','on')
                    set(NB_In{2}(1,N),'String',num2str(n))
                    set(NB_In{2}(2,N),'String',num2str(round(NB{2}.X(n),1)))
                    set(f,'CurrentObject',NB_In{1}(3,N))
                    if isempty(get(NB_In{1}(3,N),'String'))
                        set(NB_In{2}(3,N),'String',num2str(round(NB{2}.P(n),1)))
                    end
                    AID(NB_In{2}(3,N),0,'update')
                end
        end

    else %Adjust Weights & Balance
        cg_data = get(opt(1),'UserData');
        prompt{1} = ['Component X-CG Location, ',unit];
        prompt{2} = ['Component Z-CG Location, ',unit];
        wt_fraction = [3,12,12,2,3,12,12,24,10,10];
        frac = cell(1,length(wt_fraction));
        if strcmp(unit,'in') && BD.X(end)<120
            prompt{3} = 'Component Weight, oz';
            wt_fraction = wt_fraction*16;
        else
            prompt{3} = 'Component Weight, lb';
        end
        for i=1:length(frac), frac{i}=sprintf('/%.2f',wt_fraction(i)); end
        cancel=0;
        switch part
            case {'WG','WGtip','F','A'}
                
                %Wing
                part = 'Wing'; marker = 'g.'; k=1;
                if ~strcmp(cg_data{1,k},'0')
                    default = cg_data(:,k);
                else
                    default={'WG.xmac+WG.cbar(end)/3','0',['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                WG.XCG=eval(in{1}); WG.ZCG=eval(in{2}); WG.WT=eval(in{3});
                X=WG.X+WG.XCG;      Z=WG.Z+WG.ZCG;      Y=WG.Y+WG.SSPN/2;
                
            case {'HT','HTtip','E'}
                
                %Horizontal Tail
                part = 'Horizontal Tail'; marker = 'r.'; k=2;
                if ~strcmp(cg_data{1,k},'0')
                    default = cg_data(:,k);
                else
                    default={'HT.xmac+HT.cbar/2','0',['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                HT.XCG=eval(in{1}); HT.ZCG=eval(in{2}); HT.WT=eval(in{3});
                X=HT.X+HT.XCG;      Z=HT.Z+HT.ZCG;      Y=HT.Y+HT.SSPN/2;
                
            case {'VT','VTtip','R'}
                
                %Vertical Tail
                part = 'Vertical Tail'; marker = 'c.'; k=3;
                if ~strcmp(cg_data{1,k},'0')
                    default = cg_data(:,k);
                else
                    ydef = 'VT.ymac/2';
                    default={'VT.xmac+VT.cbar/2',ydef,['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                VT.XCG=eval(in{1}); VT.ZCG=eval(in{2}); VT.WT=eval(in{3});
                X=VT.X+VT.XCG;      Z=VT.Z+VT.ZCG;      Y=VT.Y+VT.SSPN/2;
                
            case 'BD'
                
                %Wing
                part = 'Body'; marker = 'b.'; k=4;
                %if isfield(BD,'XCG')
                if ~strcmp(cg_data{1,k},'0')
                    default = cg_data(:,k);
                else
                    xdef='(BD.X(end)-BD.X(1))/2';
                    zdef='mean((BD.ZU+BD.ZL)/2)';
                    default={xdef,zdef,['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                BD.XCG=eval(in{1}); BD.ZCG=eval(in{2}); BD.WT=eval(in{3});
                X=BD.X(1)+BD.XCG;   Z=BD.ZCG;           Y=0;
                
            case {'NP{1}'}
                
                %Wing 2
                part = 'Wing 2'; marker = 'g.'; k=5;
                %if isfield(NP{k-4},'XCG')
                if ~strcmp(cg_data{1,k},'0')
                    xdef = 'NP{1}.xmac+NP{1}.cbar/3';
                    default={xdef,'0',['AERO.WT',frac{k}]};
                else
                    default={'WG.xmac+WG.cbar/3','0',['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                NP{k-4}.XCG=eval(in{1});   	NP{k-4}.ZCG=eval(in{2});
                X=NP{k-4}.X+NP{k-4}.XCG;    Z=NP{k-4}.Z+NP{k-4}.ZCG;   Y=0;
                NP{k-4}.WT=eval(in{3});
                
            case {'NP{2}'}
                
                %Wing 2
                part = 'Horizontal Tail 2'; marker = 'r.'; k=6;
                %if isfield(NP{k-4},'XCG')
                if ~strcmp(cg_data{1,k},'0')
                    xdef = 'NP{2}.xmac+NP{2}.cbar/2';
                    default={xdef,'0',['AERO.WT',frac{k}]};
                else
                    default={'WG.xmac+WG.cbar(end)/3','0',['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                NP{k-4}.XCG=eval(in{1});   	NP{k-4}.ZCG=eval(in{2});
                X=NP{k-4}.X+NP{k-4}.XCG;    Z=NP{k-4}.Z+NP{k-4}.ZCG;   Y=0;
                NP{k-4}.WT=eval(in{3});
                
            case {'NP{3}'}
                
                %Wing 2
                part = 'Vertical Tail 2'; marker = 'c.'; k=7;
                %if isfield(NP{k-4},'XCG')
                if ~strcmp(cg_data{1,k},'0')
                    default = cg_data(:,k);
                else
                    xdef = 'NP{3}.xmac+NP{3}.cbar/2';
                    zdef = 'NP{3}.ymac/2';
                    default={xdef,zdef,['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                NP{k-4}.XCG=eval(in{1});   	NP{k-4}.ZCG=eval(in{2});
                X=NP{k-4}.X+NP{k-4}.XCG;    Z=NP{k-4}.Z+NP{k-4}.ZCG;   Y=0;
                NP{k-4}.WT=eval(in{3});
                
            case {'NP{4}'}
                
                %Propeller
                part = 'Propeller'; marker = 'm.'; k=8;
                %if isfield(NP{k-4},'XCG')
                if ~strcmp(cg_data{1,k},'0')
                    default = cg_data(:,k);
                else
                    default={'0','0',['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                NP{k-4}.XCG=eval(in{1});   	NP{k-4}.ZCG=eval(in{2});
                X=NP{k-4}.X+NP{k-4}.XCG;    Z=NP{k-4}.Z+NP{k-4}.ZCG;   Y=0;
                NP{k-4}.WT=eval(in{3});
                
            case 'NB{1}'
                
                %Body 2
                part = 'Body 2'; marker = 'c.'; k=9;
                %if isfield(NB{k-8},'XCG')
                if ~strcmp(cg_data{1,k},'0')
                    default = cg_data(:,k);
                else
                    xdef='(NB{1}.X(end)-NB{1}.X(1))/2';
                    zdef='mean((NB{1}.ZU+NB{1}.ZL)/2)';
                    default={xdef,zdef,['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                NB{k-8}.XCG=eval(in{1});   	NB{k-8}.ZCG=eval(in{2});
                X=NB{k-8}.X0+NB{k-8}.XCG;   Z=NB{k-8}.Z0+NB{k-8}.ZCG;  Y=0;
                NB{k-8}.WT=eval(in{3});
                
            case 'NB{2}'
                
                %Body 3
                part = 'Body 3'; marker = 'c.'; k=10;
                %if isfield(NB{k-8},'XCG')
                if ~strcmp(cg_data{1,k},'0')
                    default = cg_data(:,k);
                else
                    xdef='(NB{2}.X(end)-NB{2}.X(1))/2';
                    zdef='mean((NB{2}.ZU+NB{2}.ZL)/2)';
                    default={xdef,zdef,['AERO.WT',frac{k}]};
                    default{3}='0';
                end
                in = inputdlg(prompt,[part,' Weight'],1,default);
                if isempty(in), in = default; cancel=1; end
                NB{k-8}.XCG=eval(in{1});   	NB{k-8}.ZCG=eval(in{2});
                X=NB{k-8}.X0+NB{k-8}.XCG;   Z=NB{k-8}.Z0+NB{k-8}.ZCG;  Y=0;
                NB{k-8}.WT=eval(in{3});
                
            otherwise
                
                k=0;
        end
        
        %Plot Component CG Location
        g = []; %temporary plot handle
        if ~cancel && k
            set(ax{2}{k},'FaceColor','interp')
            g(1) = plot3(ax{1},X,0,Z,marker,'MarkerSize',25);
            wt = eval(in{3}); wt_unit = prompt{3}(end-1:end);
            str = sprintf('   %s Weight: %.2f %s\n   (X=%.2f %s, Z=%.2f %s)',...
                part,wt,wt_unit,X,unit,Z,unit);
            g(2) = text(X,0,Z,str);
            set(opt(2),'Tag','cg')
            set(findall(ax{1},'FaceAlpha',1),'FaceAlpha',0.3)
        end
        
        %Update Weights/Balance Array
        t = 0.5; %pause time
        cg_data(:,k) = in; set(opt(1),'UserData',cg_data)
        if ~strcmp(get(opt(1),'Checked'),'on')
            pause(t)
            AID(0,0,'update')
            if ~isempty(g), delete(g), end
        else
            AID(0,0,'update')
            pause(t)
            if ~isempty(g), delete(g), end
        end
    end
    
    %Clear Saved Point
    ax{1}.UserData  = [];
    
elseif aero && line && ~dragged

    %Rotate Model Axes
    N=10; %steps for cool animation
    [Az0,El0]=view(ax{1});
    Az = Az0;	dAz=(-90-Az)/N;  
    El = El0;   dEl=-El0/N; 

    %If Beyond 10 Deg
    if abs(dAz)>10/N || abs(dEl)>10/N
        for n=1:N
            El=El+dEl;  Az=Az+dAz;
            view(ax{1},[Az,El])
            delete(findall(ax{1},'Type','light'))
            camlight(-15,30), camlight(15,30)
            pause(0.001)
        end
    else
        view(ax{1},[-90,0])
    end
    
else
    
    %Update
    ax{1}.UserData  = []; 
    
    %Reset Selection Boxes
    gray = [0.94,0.94,0.94];
    set(findall(gcf,'Style','edit'),'BackgroundColor',gray,...
        'ForegroundColor',[0,0,0])
    if strcmp(get(gco,'Type'),'figure') && strcmp(click,'normal')
        set(tabs,'SelectedTab',tab_list(6))
        AID(0,0,'update')
    end
    
end

end

function Planform_Select(f,Az,El,PT,PT_In,x1,y1,select,type)
global ax

%Collect Click/Geometry Data
if nargin<7, select = 0; end, n = 0;
c = [PT.CHRDR,PT.CHRDBP,PT.CHRDTP];
x = [PT.X,PT.Xbrk,PT.Xtip];
if nargin<9, type='h'; end
if ~strcmp(type,'v')
    y = [PT.Y,PT.Y+PT.SSPNOP,PT.Y+PT.SSPN];
else
    y = [PT.Z,PT.Z+PT.SSPNOP,PT.Z+PT.SSPN];
end
if ~PT.SSPNOP, c(2) = []; x(2) = []; y(2) = []; end
x0 = interp1(y,x,y1,'linear');  c0 = interp1(y,c,y1,'linear');
x2 = (x1-x0)/c0;                %chordwise position (0-1)
y2 = (y1-y(1))/(y(end)-y(1));   %spanwise position (0-1)
ybreak = (y(2)-y(1))/(y(end)-y(1)); %spanwise break (0-1)

%Select Parameter
if y2<0.1 %within 10% span of root
    n = 1; %adjust root chord
    set(gco,'UserData','CHRDR')
elseif y2>0.9 %within 10% span of tip
    n = 3; %adjust tip chord
    set(gco,'UserData','CHRDTP')
elseif x2<0.25 %within 25% chord of LE
    if abs(El)>15 || abs(abs(rem(Az,180))-90)>=30 %swp %strcmp(type,'v') || 
        if PT.SSPNOP && y2>ybreak
            n = 7; set(gco,'UserData','SAVSO')
        else
            n = 6; set(gco,'UserData','SAVSI')
        end
    else %adjust dihedral
        if PT.SSPNOP && y2>ybreak
            n = 10; set(gco,'UserData','DHDADO')
        else
            n = 9; set(gco,'UserData','DHDADI')
        end
    end
elseif x2>0.75 %within 25% chord of TE
    n = 4; set(gco,'UserData','SSPN')
elseif select
%     if ~PT.SSPNOP
%         answr = questdlg('Create spanwise break point?');
%     else
%         answr='';
%     end
    answr = 'Yes';
    if isempty(answr) || strcmp(answr,'Yes') 
        if ~strcmp(type,'v')
            set(PT_In(5),'String',sprintf('%.1f',y1-PT.Y))  %break span
        else
            set(PT_In(5),'String',sprintf('%.1f',y1-PT.Z))  %break span
        end
        set(PT_In(2),'String',sprintf('%.1f',c0))       %break chord
        if ~PT.SSPNOP
            part = get(gco,'Tag');
%         	set(PT_In(7),'String',get(PT_In(6),'String'))   %sweep
%           set(PT_In(10),'String',get(PT_In(9),'String'))  %dihedral
        	set(PT_In(7),'String',[part,'.','SAVSI'])   %sweep
            set(PT_In(10),'String',[part,'.','DHDADI'])  %dihedral
        end
    else
        return
    end
    n = 2; set(gco,'UserData','CHRDBP') %adjust break chord
end
if n && ~iscell(ax{3})
    set(f,'CurrentObject',PT_In(n))
    AID(PT_In(n),0,'update')
end

end

function click_pos = Data_Point(f)

%Get Surface Data from abbreviated DataCursorManager function
fp = hgconvertunits(f,[f.CurrentPoint 0 0],f.Units,'pixels',f);
hMode = getuimode(f,'Exploration.Datacursor'); hTarget = gco;
if isempty(hMode), hMode = uimode(f,'Exploration.Datacursor'); end
hTool = matlab.graphics.shape.internal.DataCursorManager(hMode);
%hTool.SnapToDataVertex = 'off';
hTip = hTool.createDatatip(hTarget,fp(1:2));
data_point = getCursorInfo(hTool);
if ~isempty(data_point)
    click_pos = data_point.Position;
    delete(hTool), delete(hTip)
    activateuimode(f,'')
else
    click_pos = [-999,-999,-999];
end

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%% REPORT %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% ADD REPORT %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function Add_Report(h,~,f)
global AC AERO ATM WG HT VT BD NP NB Results ax
 
variable = h.UserData;
if ~isempty(strtrim(variable)) && isempty(strfind(variable,'='))
    value = num2str(eval(variable));
else
    value = 'Define output variable';
end
f.Units = 'pixels';
pt = f.CurrentPoint; pt = round(pt/20)*20; %snap to position
pos_delete = [pt(1)-10,pt(2)+10,20,20];
pos_plot = [pt(1)-10,pt(2)-10,20,20];
pos_edit = [pt(1)+10,pt(2)-10,120,20];
pos_output = [pt(1)+130,pt(2)-10,110,16];
pos_1 = [pt(1)+10,pt(2)+10,60,20];
pos_2 = [pt(1)+70,pt(2)+10,60,20];
pos_text = [pt(1)+10,pt(2)+10,120,16];
reports = get(f,'UserData');
if isempty(reports)
    reports = cell(1,2);
    reports{1,1} = zeros(1,5);
else
    reports{end+1,1} = zeros(1,5);
end
choices = {'AC','AERO','ATM','WG','HT','VT','BD','NP','NB','Results'};

%Adjust Sizing for OSX
if ~ispc
    pos_edit(3)=pos_edit(3)+40;
    pos_1(3)=pos_1(3)+20;
    pos_2(1)=pos_2(1)+20;
    pos_2(3)=pos_2(3)+20;
    pos_output(1)=pos_output(1)+40;
end

%UIControls
red = [0.9,0.7,0.7]; 
reports{end,1}(1) = uicontrol(f,'Style','pushbutton','Position',pos_delete,...
    'String','X','Callback',{@Delete_Report,f},'BackgroundColor',red,...
    'USerData',0,'Units','normalized');
reports{end,1}(2) = uicontrol(f,'Style','pushbutton','Position',pos_plot,...
    'String','|_','Callback',{@Plot_Report,f},...
    'USerData',0,'Units','normalized');
reports{end,1}(3) = uicontrol(f,'Style','edit','Position',pos_edit,...
    'String',variable,'Callback',{@AID,'update'},...
    'USerData',0,'Units','normalized');
reports{end,1}(4) = uicontrol(f,'Style','text','Position',pos_output,...
    'String',value,'HorizontalAlignment','left','Units','normalized');

%Variable List
if isempty(strtrim(variable))
    reports{end,1}(5) = uicontrol(f,'Style','popupmenu','Position',pos_1,...
        'String',choices,'Units','normalized');
    reports{end,1}(6) = uicontrol(f,'Style','popupmenu','Position',pos_2,...
        'String',fields(eval(choices{1})),'Units','normalized');
    set(reports{end,1}(5),'Callback',{@DropDown_1,reports})
    set(reports{end,1}(6),'Callback',{@DropDown_2,reports})
else
    string = get(h,'Label');
    reports{end,1}(5) = uicontrol(f,'Style','text','Position',pos_text,...
        'String',string,'Units','normalized');
    reports{end,1}(6) = uicontrol(f,'Style','text','Visible','off','Units',...
        'normalized');
end

%Tag
set(reports{end,1},'Tag',['Report ',num2str(size(reports,1))])

%Create Plot
plot_pos(1) = pos_edit(1);
plot_pos(2) = pos_edit(2)-pos_edit(3)-10;
plot_pos(3:4) = pos_edit(3);
ax{6}{end+1} = axes(f,'Units','pixels','Position',plot_pos);
ax{6}{end}.Units = 'normalized'; ax{6}{end}.Visible = 'off';

%Update
f.Units = 'normalized';
f.UserData = reports;
AID(0,0,'update')

end

function DropDown_1(h,~,reports)%%%%%%%%%%%%%%% COMPONENT %%%%%%%%%%%%%%%%%
global AC AERO ATM WG HT VT BD NP NB Results

%Identify Selected Report
space = strfind(h.Tag,' ');
i = str2double(h.Tag(space+1:end));
choices = get(h,'String');
selection = get(h,'Value');
variable = choices{selection};
if strcmp(choices{selection},'NP')
    inform = {'The elements of this cell array correspond to:',...
        '   {1}: Wing 2','   {2}: HT 2','   {3}: VT 2','   {4}: Prop'};
    helpdlg(inform,'NP Info')
    variable = [variable,'{1}'];
elseif strcmp(choices{selection},'NB')
    inform = {'The elements of this cell array correspond to:',...
        '   {1}: Body 2','   {2}: Body 3'};
    helpdlg(inform,'NB Info')
    variable = [variable,'{1}'];
elseif strcmp(choices{selection},'Results')
    inform = {'The elements of this cell array correspond to:',...
        '   {1}: DATCOM Results','   {2}: ASCDM Results',...
        '   {3}: Tornado Results','   {4}: AVL Results'};
    helpdlg(inform,'Results Info')
    variable = [variable,'{1}'];
end
if isempty(eval(variable))
    set(reports{i,1}(6),'String',{''})
else
    set(reports{i,1}(6),'String',fields(eval(variable)))
end

end

function DropDown_2(h,~,reports)%%%%%%%%%%%%%%% PARAMETER %%%%%%%%%%%%%%%%%
global AC AERO ATM WG HT VT BD NP NB Results

%Identify Selected Report
space = strfind(h.Tag,' ');
i = str2double(h.Tag(space+1:end));
choices_1 = get(reports{i,1}(5),'String');
select_1 = get(reports{i,1}(5),'Value');
if select_1>7, choices_1{select_1} = [choices_1{select_1},'{1}']; end
choices_2 = get(h,'String');
select_2 = get(h,'Value');
output_str = [choices_1{select_1},'.',choices_2{select_2}];
input_str = get(reports{i,1}(3),'String');
if isempty(input_str), input_str = ' '; end
switch input_str(end)
    case {'*','/','+','-','(','='}
        set(reports{i,1}(3),'String',[input_str,output_str]);
    otherwise
        set(reports{i,1}(3),'String',output_str);
end

%Update
AID(0,0,'update')

end

function Delete_Report(h,~,f)%%%%%%%%%%%%%% DELETE REPORT %%%%%%%%%%%%%%%%%
global ax

reports = get(f,'UserData');
space = strfind(h.Tag,' ');
i = str2double(h.Tag(space+1:end));
delete(reports{i,1}), reports(i,:)=cell(1,2);
delete(ax{6}{i}), ax{6}{i} = [];

%Update
set(f,'UserData',reports)
AID(0,0,'update')

end

function Plot_Report(h,~,f)%%%%%%%%%%%%%%%% PLOT REPORT %%%%%%%%%%%%%%%%%%%
global ax

space = strfind(h.Tag,' ');
i = str2double(h.Tag(space+1:end));
blue = [0.8,0.9,1]; gray = [0.94,0.94,0.94];
if strcmp(ax{6}{i}.Visible,'off')
    ax{6}{i}.Visible = 'on';
    set(h,'BackgroundColor',blue)
else
    ax{6}{i}.Visible = 'off';
    delete(findall(ax{6}{i},'Type','line'))
    reports = get(f,'UserData'); reports{i,2} = [];
    set(f,'UserData',reports);
    set(h,'BackgroundColor',gray)
end

end

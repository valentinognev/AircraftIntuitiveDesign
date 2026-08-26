%Design Aircraft Fuselage
function Profile_Sketcher(~,~,type,unit,mode)
global WG WG_In HT HT_In VT VT_In NP NP_In BD BD_In NB NB_In ...
    New Original L Pos thresh ax select opt opt2 cmp

%mode = {view ('side' or 'top'), station (1-N)}

%Close Existing Body Design
if iscell(ax{3})
    for i=1:length(ax{3})
        if ~isempty(ax{3}{i}), delete(ax{3}{i}), ax{3}{i} = []; end
    end
end

%Rotate Model Axes
N=30; %steps for cool animation
[Az0,El0]=view(ax{1});
Az = Az0;	dAz=-Az/N;  El = El0;

if nargin>4 %toggle view
    if strcmp(mode{1},'top')
        dEl=(90-El0)/N;
    else
        dEl=-El0/N;
    end
else
    if El0>45
        dEl=(90-El0)/N; mode{1}='top';
    else
        dEl=-El0/N; mode{1}='side';
    end
    mode{2} = [];
end

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
    if abs(El0)>45, El=90; else, El=0; end
    view(ax{1},[0,El])
end

%Selection Type
select = 0; %tracks type of input and selected points
% 1: node on upper surface selected
% 2: node on lower surface selected
% 3: nodes on both surfaces selected

%Collect Variables
switch type
    case 'Fuselage'
        X0=0; Z0=0; PT = BD; PT_In = BD_In;
        NX=BD.NX; X=BD.X; L=BD.X(end)-BD.X(1);
        if strcmp(mode{1},'top')
            ZU=BD.R; ZL=-ZU;
        else
            ZU=BD.ZU; ZL=BD.ZL;
        end
    case 'Body 2'
        n = 1; X0=NB{n}.X0; PT = NB{1}; PT_In = NB_In{1};
        NX=NB{n}.NX; X=NB{n}.X+X0; L=NB{n}.X(end)-NB{n}.X(1);
        if strcmp(mode{1},'top')
            Z0=NB{n}.Y0; ZU=Z0+NB{n}.R; ZL=Z0-NB{n}.R;
        else
            Z0=NB{n}.Z0; ZU=NB{n}.ZU+Z0; ZL=NB{n}.ZL+Z0;
        end
    case 'Body 3'
        n = 2; X0=NB{n}.X0; PT = NB{2}; PT_In = NB_In{2};
        NX=NB{n}.NX; X=NB{n}.X+X0; L=NB{n}.X(end)-NB{n}.X(1);
        if strcmp(mode{1},'top')
            Z0=NB{n}.Y0; ZU=Z0+NB{n}.R; ZL=Z0-NB{n}.R;
        else
            Z0=NB{n}.Z0; ZU=NB{n}.ZU+Z0; ZL=NB{n}.ZL+Z0;
        end
    case 'Wing Airfoil'
        PT = WG; PT_In = WG_In;      
    case 'HT Airfoil'
        PT = HT; PT_In = HT_In;
    case 'VT Airfoil'
        PT = VT; PT_In = VT_In;
    case 'Wing 2 Airfoil'
        PT = NP{1}; PT_In = NP_In{1};
    case 'HT 2 Airfoil'
        PT = NP{2}; PT_In = NP_In{2};
    case 'VT 2 Airfoil'
        PT = NP{3}; PT_In = NP_In{3};
end

%Extract Airfoil Data
if ~isempty(mode{2})
    if mode{2}>length(PT.DATA), PT.DATA{mode{2}} = PT.DATA{1}; end
    data = PT.DATA{mode{2}};
    NX = ceil(length(data)/2);
    if mod(length(data),2), data(NX+1:end+1,:) = data(NX:end,:); end %even
    if mode{2}==2
        X0 = PT.Xtip; Z0 = PT.Ztip; L = PT.CHRDTP;
        if strcmp(mode{1},'top'), Z0 = Z0+PT.Y; else, Z0 = Z0P+PT.Z; end
    elseif mode{2}==1
        X0 = PT.X; L = PT.CHRDR;
        if strcmp(mode{1},'top'), Z0 = PT.Y; else, Z0 = PT.Z; end
    end
    X = fliplr(data(1:NX,1)')*L;
    ZU = data(end-NX+1:end,2)'*L;
    ZL = fliplr(data(1:NX,2)')*L;
    X = X+X0; ZU = ZU+Z0; ZL = ZL+Z0;
    if mean(ZL)>mean(ZU)
        Z = ZL; ZL = ZU; ZU = Z;
    end
end

%Write to New Profile Data
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL; 
Original=New; if isfield(PT,'N'), Original.N = PT.N; end
Original.Az0 = Az0;	Original.El0 = El0;

%Draw Parameters (click speed)
thresh = 0.02*L; %what error threshold qualifies clicking a point or line?

%Create Figure (in location of plot axes)
f0 = ancestor(ax{1},'figure'); %base figure
f=figure('NumberTitle','off','MenuBar','none','Units','normalized');
set(f,'Name',[type,' Design'])
fpos = f0.Position; %main figure
apos = ax{1}.Position; %main axes
f.Position = [fpos(1:2),0,0] + apos.*[fpos(3:4),fpos(3:4)];
ax{3} = axes(f,'Units','normalized','Position',[0,0,1,1]);
set(ax{3},{'Xlim','YLim','ZLim'},get(ax{1},{'Xlim','YLim','ZLim'}))

%Context Menu
c = uicontextmenu;
f.UIContextMenu = c;
uimenu(c,'Label','Background','Enable','off')
uimenu(c,'Label','========','Enable','off')
uimenu(c,'Label','Load','Callback',{@Image,c})
opt2(3)=uimenu(c,'Label','Adjust','Checked','Off','Callback',{@Image});
opt2(5)=uimenu(c,'Label','Flip','Callback',{@Image});
uimenu(c,'Label','Rotate','Callback',{@Image});
opt2(4)=uimenu(c,'Label','Hide','Callback',{@Image,c},'UserData',[0,0,1,1]);

%Initialize Background Image
if ~isempty(ax{4}) && isvalid(ax{4}{3})
    
    %Maintain Image Position
    ipos=ax{4}{1}.Position; %main image
    shift = (ipos(1:2)-apos(1:2))./apos(3:4);
    scale = ipos(3:4)./apos(3:4);
    ax{5}{1}=axes(f,'Units','normalized','Position',[shift,scale]);
    uistack(ax{5}{1},'bottom')
    ax{5}{2} = ax{4}{2};
    %if length(size(ax{5}{2}))>2, ax{5}{2} = rgb2gray(ax{5}{2}); end
    ax{5}{3} = imshow(ax{5}{2}); ax{5}{3}.UIContextMenu = c;
    if strcmp(ax{4}{1}.XDir,'reverse')
        ax{5}{1}.XDir = 'reverse'; set(opt2(5),'Checked','on')
    end
    set(ax{5}{1},'HandleVisibility','off','Visible','off')
end

%Initialize Aircraft Plot
[Az,El] = view(ax{1}); handle = [Az,El]; hold(ax{3},'on')
if get(cmp(1),'Value'), ax{2}{1} = Plot_Planform(WG,'wing',ax{3},50,20,1,''); end
if get(cmp(2),'Value'), ax{2}{2} = Plot_Planform(HT,'ht',ax{3},50,10,1,'');   end
if get(cmp(3),'Value'), ax{2}{3} = Plot_Planform(VT,'vt',ax{3},50,10,1,'');   end
if get(cmp(4),'Value'), ax{2}{4} = Plot_Body(BD,ax{3},360,'',0); end
part = {'wing 2','ht 2','vt 2','prop'};
for n=1:length(NP) %plot additional planforms
    if ~isempty(NP_In{n}) && get(cmp(4+n),'Value')
        ax{2}{4+n} = Plot_Planform(NP{n},part{n},ax{3},10,10,1);
    end
end
for n=1:length(NB) %plot additional bodies
    if ~isempty(NB_In{n}) && get(cmp(8+n),'Value')
        ax{2}{8+n} = Plot_Body(NB{n},ax{3},36,'',n);
    end
end

%Figure Properties
colormap(get(opt(7),'UserData'))    %colormap([1,1,1])
shading(ax{3},'interp')             %Interpolated shading
lighting(ax{3},'gouraud')           %Smooth airplane mesh
material(ax{3},'metal')             %Apply material
camlight headlight                  %Apply a light source
axis(ax{3},'off')                   %Set axis visibility off
view(ax{3},handle)                  %Apply view rotation
axis(ax{3},'equal')                 %Correct aspect ratio
camva(ax{3},camva(ax{1}))           %Zoom/Turn off stretch-to-fit

%Initialize Plot
zero = zeros(size(X));
if strcmp(mode{1},'top')
    ax{2}{11}=plot3(X,zero+Z0,zero,'k--',X,ZU,zero,'k-o',X,ZL,zero,'k-o');
    if strcmp(type,'Fuselage') && isempty(ax{5}) 
        ax{3}.YLim = [min([ax{1}.YLim(1),0,ZL]),max([ax{1}.YLim(2),0,ZU])];
    end
    if ~isempty(mode{2}), set(ax{2}{11}(1),'YData',(ZU+ZL)/2), end %camber
else
    ax{2}{11}=plot3(X,zero,zero+Z0,'k--',X,zero,ZU,'k-o',X,zero,ZL,'k-o');
    if strcmp(type,'Fuselage') && isempty(ax{5})
        ax{3}.ZLim = [min([ax{1}.ZLim(1),0,ZL]),max([ax{1}.ZLim(2),0,ZU])];
    end
    if ~isempty(mode{2}), set(ax{2}{11}(1),'ZData',(ZU+ZL)/2), end %camber line
end
if strcmp(type,'Fuselage') && isempty(ax{5})
    ax{3}.XLim = [min([ax{1}.XLim(1),0,X]),max([ax{1}.XLim(2),L,X])];
end
alpha(0.2)

%Prescribed Geometry
geom = uimenu(f,'Label','Geometry');
if strcmp(type,'Fuselage')
    geom_cb= {@Geometry,type,mode,X0,Z0};
    uimenu(geom,'Label','Small Jet','Callback',geom_cb);
    uimenu(geom,'Label','Airliner','Callback',geom_cb);
    uimenu(geom,'Label','NACA','Callback',geom_cb)
elseif ~isempty(strfind(type,'Body'))
    geom_cb= {@Geometry,type,mode,X0,Z0};
    uimenu(geom,'Label','Turbofan Engine','Callback',geom_cb);
    af_in = uimenu(geom,'Label','Airfoil');
    uimenu(geom,'Label','NACA','Callback',geom_cb)
else
    geom_cb= {@Geometry,type,mode,X0,Z0,PT};
    if mode{2}==2
        uimenu(geom,'Label','Match Root','Callback',geom_cb); 
    else
        uimenu(geom,'Label','Match Tip','Callback',geom_cb); 
    end
    af_in = uimenu(geom,'Label','Airfoil');
    uimenu(af_in,'Label','NACA','Callback',geom_cb)
    uimenu(af_in,'Label','Load Data','Callback',geom_cb)
    uimenu(af_in,'Label','Paste Points','Callback',geom_cb)
    uimenu(geom,'Label','Flat Plate','Callback',geom_cb);
end
uimenu(geom,'Label','Ellipse/Other','Callback',geom_cb,'UserData',...
    {'N=22;    t=linspace(pi,0,N);','AR=4;    X=1/2+cos(t)/2;',...
    'M=1;     ZU=sin(t).^M/2/AR;','SC=1;    ZL=-ZU/SC;'});

%Symmetry
sym = uimenu(f,'Label','Symmetry');
opt2(1) = uimenu(sym,'Label','Force Symmetry','Callback',@setting);
if strcmp(mode{1},'top') || ~isempty(strfind(type,'Body'))
    set(opt2(1),'Checked','on')
end
surface(1) = uimenu(sym,'Label','Copy Upper Surface');
surface(2) = uimenu(sym,'Label','Copy Lower Surface');
for i=1:length(surface)
    set(surface(i),'Callback',{@Symmetry,i,type,mode})
end

%Length
l_scale = uimenu(f,'Label','Scale Length');
scale(1) = uimenu(l_scale,'Label',sprintf('50%% (L=%.1f %s)',L/2,unit));
scale(2) = uimenu(l_scale,'Label',sprintf('80%% (L=%.1f %s)',4*L/5,unit));
scale(3) = uimenu(l_scale,'Label',sprintf('125%% (L=%.1f %s)',5*L/4,unit));
scale(4) = uimenu(l_scale,'Label',sprintf('200%% (L=%.1f %s)',2*L,unit));
scale(5) = uimenu(l_scale,'Label','Specify Length');

%Width/Height
if strcmp(mode{1},'top')
    w_scale = uimenu(f,'Label','Scale Width');
else
    w_scale = uimenu(f,'Label','Scale Height');
end
scale(6) = uimenu(w_scale,'Label','50%');
scale(7) = uimenu(w_scale,'Label','80%');
scale(8) = uimenu(w_scale,'Label','125%');
scale(9) = uimenu(w_scale,'Label','200%');
scale(10) = uimenu(w_scale,'Label','Specify');
for i=1:length(scale)
    set(scale(i),'Callback',{@Scale,scale,i,unit,mode,type})
end

%Settings
settings = uimenu(f,'Label','Settings');
opt2(2) = uimenu(settings,'Label','Auto-Add Points','Callback',@setting);
if strcmp(type,'Fuselage') && ~strcmp(mode{1},'top')
    set(opt2(2),'Checked','on')
end
opt2(6) = uimenu(settings,'Label','Prevent Crossover',...
    'Checked','on','Callback',@setting);
res = uimenu(settings,'Label','Resolution/Detail');
option(1) = uimenu(res,'Label','Fine');
option(2) = uimenu(res,'Label','Medium','Checked','on');
option(3) = uimenu(res,'Label','Coarse');
dist = uimenu(settings,'Label','Default Spacing');
spacing(1) = uimenu(dist,'Label','Equal');
spacing(2) = uimenu(dist,'Label','Nosey');
spacing(3) = uimenu(dist,'Label','Current');
for i=1:length(option)
    set(option(i),'Callback',{@Sensitivity,option,i})
end
for i=1:length(spacing)
    set(spacing(i),'Callback',{@Distribution,spacing,i,type,mode})
end

%Help
help = uimenu(f,'Label','Help');
uimenu(help,'Label','Quick Start','Callback',@doc);
uimenu(help,'Label','','Enable','off');
uimenu(help,'Label','Profile:','Enable','off');
uimenu(help,'Label','===================','Enable','off');
uimenu(help,'Label','Scroll - Zoom','Enable','off');
uimenu(help,'Label','Left Click - Drag Selection','Enable','off');
uimenu(help,'Label','Center/Shift Click - Draw/Select','Enable','off');
uimenu(help,'Label','Right Click - Options/Pan','Enable','off');
uimenu(help,'Label','===================','Enable','off');
uimenu(help,'Label','','Enable','off');
uimenu(help,'Label','Background Image:','Enable','off');
uimenu(help,'Label','===================','Enable','off');
uimenu(help,'Label','Scroll - Scale Image','Enable','off');
uimenu(help,'Label','Left Click - Drag Image*','Enable','off');
uimenu(help,'Label','*if adjust option enabled','Enable','off');
uimenu(help,'Label','Right Click - Options','Enable','off');
uimenu(help,'Label','===================','Enable','off');
uimenu(help,'Label','','Enable','off');

%Functions
x0 = 0.1; dx = 0.225;
if ~isempty(mode{2})
    uicontrol('Style','Pushbutton','String','Analyze with Panel Method',...
        'Units','normalized','Position',[0,0.05,1,0.05],...
        'Callback',{@Save,type,1,mode,X0})
    uicontrol('Style','Pushbutton','String','Update Geometry','Units',...
        'normalized','Position',[0,0,1,0.05],...
        'Callback',{@Save,type,0,mode,X0})
else
    uicontrol('Style','Pushbutton','String','Save & Close','Units',...
        'normalized','Position',[0,0,1,0.1],...
        'Callback',{@Save,type,0,mode,X0})
end
buttons = {'Top View','Smooth','Add/Remove Point','Reset'};
cbacks = {{@Change_View,type,unit,mode,X0},{@Smooth,type,mode},...
    {@Point,type,mode},{@Reset,type,mode,PT_In}};
if ~isempty(mode{2})
    if mode{2}==2
        buttons{1} = 'Root Airfoil';
    elseif mode{2}==1
        buttons{1} = 'Tip Airfoil';
    end
elseif strcmp(mode{1},'top')
    buttons{1} = 'Side View';
end
for i=1:length(buttons)
    pos=[x0+(i-1)*dx,0.9,0.15,0.1];
    uicontrol('Style','Pushbutton','String',buttons{i},'Units',...
        'normalized','Position',pos,'Callback',cbacks{i})
end
len = sprintf('Length = %.2f %s',L,unit);
Pos=uicontrol('Style','text','String',len,'Units','normalized',...
    'Position',[0.4,0.1,0.2,0.05]);

%Set Mouse Control Callbacks
set(f,'WindowButtonDownFcn',{@Press,type,unit,mode,PT_In})
set(ax{2}{11},'ButtonDownFcn',{@Press,type,unit,mode,PT_In})
set(f,'WindowButtonUpFcn',{@Release,mode,PT_In})
set(f,'WindowScrollWheelFcn',@Scroll)
%set(f,'DeleteFcn',{@Save,type,0,mode{1}})
set(f,'DeleteFcn',{@Reset,type,mode,PT_In})

end

function doc(~,~)%%%%%%%%%%%%%%%%%%% QUICK DOCUMENTATION %%%%%%%%%%%%%%%%%%

%Help Message
waitfor(helpdlg({'- Center/Shift Click and drag from a point to draw profile','',...
    '- Center/Shift Click and drag from elsewhere to select multiple points','',...
    '- Smooth/Remove Point options can be applied to a selection','',...
    '- Click centerline to drag entire profile','',...
    '- Click above/below profile to drag entire surface'},'Quick Start Guide'))

end

function Change_View(~,~,type,unit,mode,X0)%%%%%%%% CHANGE VIEW %%%%%%%%%%%

%Save and Reload Profile Sketcher
Save(0,0,type,0,mode,X0)
if ~isempty(mode{2})
    if mode{2}==2
        mode{2} = 1;
    elseif mode{2}==1
        mode{2} = 2;
    end
else
    if strcmp(mode{1},'top')
        mode{1} = 'side';
    else
        mode{1} = 'top';
    end
end
Profile_Sketcher(0,0,type,unit,mode)

end

function Image(handle,~,c)%%%%%%%%%%%%%%%% IMAGE TOGGLE %%%%%%%%%%%%%%%%%%%
global ax opt2 lib_path

%Figure
f = ancestor(handle,'figure');

%Toggle
if strcmp(handle.Label,'Load')
    %if exist('3Views','dir'), cd 3Views, fl = 1; else, fl = 0; end
    [File,Path]=uigetfile({'*.png;*.jpg;*.gif','Image Files'},...
        'Choose Background Image File',fullfile(lib_path,'3Views')); 
    %if fl, cd .., end
    fname=[Path,File];
    if ~isempty(File) && ischar(File)
        if ~isempty(ax{5}) && isvalid(ax{5}{1}), cla(ax{5}{1}), end
        ax{5}{1}=axes(f,'Units','normalized','Position',[0,0,1,1]);
        uistack(ax{5}{1},'bottom')
        ax{5}{2} = imread(fname);
        %if length(size(ax{5}{2}))>2, ax{5}{2} = rgb2gray(ax{5}{2}); end
        ax{5}{3} = imshow(ax{5}{2}); ax{5}{3}.UIContextMenu = c;
        set(ax{5}{1},'HandleVisibility','off','Visible','off')
    end
    f.Pointer = 'hand';
    set(opt2(3:4),'Checked','on')
elseif strcmp(handle.Label,'Adjust') && ~isempty(ax{5})
    if strcmp(handle.Checked,'off')
        handle.Checked = 'on';
        f.Pointer = 'hand';
    else
        handle.Checked = 'off';
        f.Pointer = 'arrow';
    end
elseif strcmp(handle.Label,'Flip') && ~isempty(ax{5})
    if strcmp(handle.Checked,'off')
        handle.Checked = 'on';
        set(ax{5}{1},'Xdir','reverse')
    else
        handle.Checked = 'off';
        set(ax{5}{1},'Xdir','normal')
    end
elseif strcmp(handle.Label,'Rotate') && ~isempty(ax{5})
        ax{5}{3}.CData = imrotate(ax{5}{3}.CData,90);
elseif strcmp(handle.Label,'Hide') && ~isempty(ax{5})
    if strcmp(handle.Checked,'on')
        ax{5}{3} = imshow(ax{5}{2}); ax{5}{3}.UIContextMenu = c;
        handle.Checked = 'off';
    else
        delete(ax{5}{3})
        set(opt2(3),'Checked','on')
        handle.Checked = 'on';
    end
end
end

%% %%%%%%%%%%%%%%%%%%%%%%%%% MOUSE FUNCTIONS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Press(p,~,type,unit,mode,PT_In)%%%%%%%%%%%%%% PRESS %%%%%%%%%%%%%%
global ax New opt2

%Click Info
f=ancestor(p,'figure');
click=get(f,'SelectionType');

%Check if Controlling Image or Plot
if strcmp(get(opt2(3),'Checked'),'on') && ~isempty(ax{5}) %image
    ax{3}.UserData = f.CurrentPoint;
    if strcmp(click,'normal')
        set(f,'WindowButtonMotionFcn',{@Drag,f,'drag image'})
    elseif strcmp(click,'extend')
        set(f,'WindowButtonMotionFcn',{@Drag,f,'scale image'})
    elseif strcmp(click,'alt')
        set(f,'WindowButtonMotionFcn',{@Drag,f,'scale image 2'})
    end
else %plot
    dat = {New.X,New.ZL,New.ZU};
    if strcmp(click,'normal') || isempty(click) %drag
        set(f,'WindowButtonMotionFcn',{@Hold,f,0,type,unit,mode,dat,PT_In})
    elseif strcmp(click,'extend') %draw
        set(f,'WindowButtonMotionFcn',{@Hold,f,1,type,unit,mode,dat,PT_In})
    elseif strcmp(click,'alt') %pan
        ax{3}.UserData = f.CurrentPoint;
        f.WindowButtonMotionFcn = {@Drag,f,'pan'};
    end
end
end

function Hold(~,~,f,draw,type,unit,mode,dat,PT_In)%%%%%%%%% HOLD %%%%%%%%%%
global Pos select thresh New L ax opt2 Original

NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;
X1 = dat{1}; ZL1 = dat{2}; ZU1 = dat{3};

%Current Point
pt=ax{3}.CurrentPoint;
if strcmp(mode{1},'top') 
    x=pt(1,1); y=pt(1,2);
    if strcmp(type,'Fuselage') && isempty(ax{5}) 
        ax{3}.YLim = [min([ax{1}.YLim(1),0,y,ZL]),max([ax{1}.YLim(2),0,y,ZU])];
    end
else
    x=pt(1,1); y=pt(1,3);
    if strcmp(type,'Fuselage') && isempty(ax{5})
        ax{3}.ZLim = [min([ax{1}.ZLim(1),0,y,ZL]),max([ax{1}.ZLim(2),0,y,ZU])];
    end
end
if strcmp(type,'Fuselage') && isempty(ax{5}) && length(f.UserData)~=4
    ax{3}.XLim = [min([ax{1}.XLim(1),0,x,X]),max([ax{1}.XLim(2),L,x,X])];
end
drag_pt=0; drag_select=0; 
symmetry = strcmp(get(opt2(1),'Checked'),'on');
auto_add = strcmp(get(opt2(2),'Checked'),'on');

%Dragging a Point
blue = [0.8,0.9,1]; 
if ~isempty(ax{3}.UserData)
    i = ax{3}.UserData; %selected point
    drag_pt = 1;
end

%Tag Surface
if isempty(ax{3}.Tag)
    [~,closex] = min(abs(X-x));
    if abs(ZU(closex)-y)<abs(ZL(closex)-y)
        ax{3}.Tag = 'upper';
    else
        ax{3}.Tag = 'lower';
    end
end

%Adjust Upper or Lower Surface
if strcmp(ax{3}.Tag,'upper') %upper surface
    
    %Proximity
    if ~drag_pt
        ds = sqrt((x-X).^2+(y-ZU).^2);
        [ds,i] = min(ds);
    end
    
    %Point or Line
    if drag_pt
        
        %Drag Selected Node
        X(i)=x; ZU(i)=y; 
        
        %Update Station Position
        if isempty(strfind(type,'Airfoil'))
            set(PT_In(2,i==Original.N),'String',num2str(round(X(i),2)),...
                'Enable','on','BackgroundColor',blue)
        end
        
    elseif ds<thresh && ~select(1) && length(select)==1 && ~draw
        
        %Select Node
        X(i)=x; ZU(i)=y;
        ax{3}.UserData = i;
        
    else
        
        %Interpolate Position on Line
        left = find(x>=X,1,'last');
        if isempty(left)
            left = 1; line = ZU(left); right = 2;
        elseif left==NX
            left = NX-1; right = NX; line = ZU(right);
        else
            right = left+1;
            line = interp1(X(left:right),ZU(left:right),x,'linear');
        end
        
        %Determine Selection Type
        if length(f.UserData)==4
            
            %Point
            [closex,i] = min(abs(x-X));
            if closex<thresh/4, ZU(i) = y; end
            
            %Line
            if x>X(left) && x<X(right)
                
                %Draw Controls
                dx = f.UserData(3); dy = f.UserData(4);
                if x>f.UserData(1) %moving right
                    ZU(X>f.UserData(1) & X<x) = y;  %skipped over a point
                    ZU(right)=ZU(right)+y-line;     %extrapolate node
                elseif x<f.UserData(1) %moving left
                    ZU(X<f.UserData(1) & X>x) = y;  %skipped over a point
                    ZU(left)=ZU(left)+y-line;       %extrapolate node
                elseif dx>0 %moving right
                    ZU(right)=ZU(right)+y-line; %extrapolate node
                elseif dx<0 %moving left
                    ZU(left)=ZU(left)+y-line;   %extrapolate node
                else
                    ZU(right)=ZU(right)+y-line; %extrapolate node
                    if dy && ds>thresh/2 && auto_add %add points
                    Point(x,y,type,mode)
                    NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;
                    end
                end
                dx = x-f.UserData(1); dy = y-f.UserData(2);
                f.UserData = [x,y,dx,dy];
            end
            
        elseif (draw && abs(y-line)>1.5*thresh) || select(1)==4
            
            %Create Selection Box
            if isempty(f.UserData), f.UserData = [x,y]; end
            pos = [f.UserData(1:2),x,y]; select = 4;
            xpos(1) = min([pos(1),pos(3)]); xpos(2) = max([pos(1),pos(3)]);
            ypos(1) = min([pos(2),pos(4)]); ypos(2) = max([pos(2),pos(4)]);
            f.UserData(3:6) = [xpos,fliplr(xpos)]; %x1,x2,x2,x1 for patch
            f.UserData(7:10) = [ypos(1),ypos(1),ypos(2),ypos(2)];
            
        elseif length(select)>1
            
            %Drag Selection Nodes
            if x<X(find(select,1,'first'))
                y0 = ZU(find(select,1,'first'));
            elseif x>X(find(select,1,'last'))
                y0 = ZU(find(select,1,'last'));
            else
                y0 = line;
            end
            ZU(select==1|select==3)=ZU(select==1|select==3)+y-y0;
            ZL(select==2|select==3)=ZL(select==2|select==3)+y-y0;
            
        elseif select(1)==1 || y>(line+1.5*thresh)
            
            %Drag Entire Surface
            select = 1;
            ZU=ZU+y-line;
            
        elseif select(1)==3 || y<(line-1.5*thresh)
            
            %Drag Entire Body
            select = 3;
            center=((ZU(left)-ZL(left))/2+(ZU(right)-ZL(right))/2)/2;
            center=(ZL(left)+ZL(right))/2+center;
            ZL=ZL+y-center;     ZU=ZU+y-center;
            drag_select = 1;
            
            %Re-draw Center Axis
            if ~isempty(strfind(type,'Body'))
                n = str2double(type(end))-1;
                center_x = (X(1)+X(end))/2;
                X = X+x-center_x;
                set(PT_In(1,8),'String',num2str(round(X(1),2)),...
                    'Enable','on','BackgroundColor',blue)
                zero = zeros(size(X));
                if strcmp(mode{1},'top')
                    set(PT_In(1,9),'String',num2str(round(center,2)),...
                        'Enable','on','BackgroundColor',blue)
                    set(ax{2}{11}(1),'XData',X,'YData',zero+center)
                else
                    set(PT_In(1,10),'String',num2str(round(center,2)),...
                        'Enable','on','BackgroundColor',blue)
                    set(ax{2}{11}(1),'XData',X,'ZData',zero+center)
                end
            elseif ~isempty(strfind(type,'Airfoil'))
                center_x = min(X)+(max(X)-min(X))/3;
                X = X+x-center_x; camber = (ZU+ZL)/2;
                set(PT_In(14),'String',num2str(round(X(1),2)),...
                    'Enable','on','BackgroundColor',blue)
                if strcmp(mode{1},'top')
                    set(PT_In(15),'String',num2str(round(center,2)),...
                        'Enable','on','BackgroundColor',blue)
                    set(ax{2}{11}(1),'XData',X,'YData',camber)
                else
                    set(PT_In(16),'String',num2str(round(center,2)),...
                        'Enable','on','BackgroundColor',blue)
                    set(ax{2}{11}(1),'XData',X,'ZData',camber)
                end
            end
            
        else
            
            %Drag Single Section (toggle on draw mode)
            if ~draw
                ZU(left) = ZU(left)+y-line;
            else
                f.UserData = [x,y,0,0];
            end
            ZU(right)=ZU(right)+y-line;
            
        end
    end
    
    %Clean Up
    if strcmp(get(opt2(6),'Checked'),'on')
        ZU(ZU<ZL)=ZL(ZU<ZL);
    end
    if symmetry && select(1)~=3
        if strcmp(mode{1},'top')
            center = ax{2}{11}(1).YData(1);
        else
            center = ax{2}{11}(1).ZData(1);
        end
        ZL=2*center-ZU; %force symmetry
    elseif ~drag_select && length(select)==1 && select<3
        %Sort
        ZL(i) = interp1(X1,ZL1,X(i),'linear','extrap'); %interpolate
    end
    
else %lower surface
    
    %Proximity
    if ~drag_pt
        ds = sqrt((x-X).^2+(y-ZL).^2);
        [ds,i] = min(ds);
    end
    
    %Point or Line
    if drag_pt
        
        %Drag Selected Node
        ZL(i)=y; X(i)=x;
        
       	%Update Station Position
        if isempty(strfind(type,'Airfoil'))
            set(PT_In(2,i==Original.N),'String',num2str(round(X(i),2)),...
                'Enable','on','BackgroundColor',blue)
        end
        
    elseif ds<thresh && ~select(1) && length(select)==1 && ~draw
        
        %Select Node
        X(i)=x; ZL(i)=y;
        ax{3}.UserData = i;
        
    else
        
        %Interpolate Position on Line
        left = find(x>=X,1,'last');
        if isempty(left)
            left = 1; line = ZL(left); right = 2;
        elseif left==NX
            left = NX-1; right = NX; line = ZL(right);
        else
            right = left+1;
            line = interp1(X(left:right),ZL(left:right),x,'linear');
        end
        
        %Determine Selection Type
        if length(f.UserData)==4
            
            %Point
            [closex,i] = min(abs(x-X));
            if closex<thresh/4, ZL(i) = y; end
            
            %Line
            if x>X(left) && x<X(right)
                
                %Draw Controls
                dx = f.UserData(3); dy = f.UserData(4);
                if x>f.UserData(1) %moving right
                    ZL(X>f.UserData(1) & X<x) = y;  %skipped over a point
                    ZL(right)=ZL(right)+y-line;     %extrapolate node
                elseif x<f.UserData(1) %moving left
                    ZL(X<f.UserData(1) & X>x) = y;  %skipped over a point
                    ZL(left)=ZL(left)+y-line;       %extrapolate node
                elseif dx>0 %moving right
                    ZL(right)=ZL(right)+y-line; %extrapolate node
                elseif dx<0 %moving left
                    ZL(left)=ZL(left)+y-line;   %extrapolate node
                else
                    ZL(right)=ZL(right)+y-line; %extrapolate node
                    if dy && ds>thresh/2 && auto_add %add points
                    Point(x,y,type,mode)
                    NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;
                    end
                end
                dx = x-f.UserData(1); dy = y-f.UserData(2);
                f.UserData = [x,y,dx,dy];
            end
            
        elseif (draw && abs(y-line)>1.5*thresh) || select(1)==4
            
            %Create Selection Box
            if isempty(f.UserData), f.UserData = [x,y]; end
            pos = [f.UserData(1:2),x,y]; select = 4;
            xpos(1) = min([pos(1),pos(3)]); xpos(2) = max([pos(1),pos(3)]);
            ypos(1) = min([pos(2),pos(4)]); ypos(2) = max([pos(2),pos(4)]);
            f.UserData(3:6) = [xpos,fliplr(xpos)]; %x1,x2,x2,x1 for patch
            f.UserData(7:10) = [ypos(1),ypos(1),ypos(2),ypos(2)];
            
        elseif length(select)>1 
            
            %Drag Selection Nodes
            if x<X(find(select,1,'first'))
                y0 = ZU(find(select,1,'first'));
            elseif x>X(find(select,1,'last'))
                y0 = ZL(find(select,1,'last'));
            else
                y0 = line;
            end
            ZU(select==1|select==3)=ZU(select==1|select==3)+y-y0;
            ZL(select==2|select==3)=ZL(select==2|select==3)+y-y0;
            
        elseif select(1)==2 || y<(line-1.5*thresh)
            
            %Drag Entire Surface
            select = 2;
            ZL=ZL+y-line;
            
        elseif select(1)==3 || y>(line+1.5*thresh)
            
            %Drag Entire Body
            select = 3;
            center=((ZU(left)-ZL(left))/2+(ZU(right)-ZL(right))/2)/2;
            center=(ZL(left)+ZL(right))/2+center;
            ZL=ZL+y-center;     ZU=ZU+y-center;
            drag_select = 1;
            
            %Re-draw Center Axis
            if ~isempty(strfind(type,'Body'))
                n = str2double(type(end))-1;
                center_x = (X(1)+X(end))/2;
                X = X+x-center_x;
                set(PT_In(1,8),'String',num2str(round(X(1),2)),...
                    'Enable','on','BackgroundColor',blue)
                zero = zeros(size(X));
                if strcmp(mode{1},'top')
                    set(PT_In(1,9),'String',num2str(round(center,2)),...
                        'Enable','on','BackgroundColor',blue)
                    set(ax{2}{11}(1),'XData',X,'YData',zero+center)
                else
                    set(PT_In(1,10),'String',num2str(round(center,2)),...
                        'Enable','on','BackgroundColor',blue)
                    set(ax{2}{11}(1),'XData',X,'ZData',zero+center)
                end
            elseif ~isempty(strfind(type,'Airfoil'))
                center_x = min(X)+(max(X)-min(X))/3;
                X = X+x-center_x; camber = (ZU+ZL)/2;
                set(PT_In(14),'String',num2str(round(X(1),2)),...
                    'Enable','on','BackgroundColor',blue)
                if strcmp(mode{1},'top')
                    set(PT_In(15),'String',num2str(round(center,2)),...
                        'Enable','on','BackgroundColor',blue)
                    set(ax{2}{11}(1),'XData',X,'YData',camber)
                else
                    set(PT_In(16),'String',num2str(round(center,2)),...
                        'Enable','on','BackgroundColor',blue)
                    set(ax{2}{11}(1),'XData',X,'ZData',camber)
                end
            end
            
        else
            
            %Drag Single Section (toggle on draw mode)
            if ~draw
                ZL(left) = ZL(left)+y-line;
            else
                f.UserData = [x,y,0,0];
            end
            ZL(right)=ZL(right)+y-line;
            
        end
    end
    
    %Clean Up
 	if strcmp(get(opt2(6),'Checked'),'on')
        ZL(ZL>ZU)=ZU(ZL>ZU);
    end
    if symmetry && select(1)~=3
        if strcmp(mode{1},'top')
            center = ax{2}{11}(1).YData(1);
        else
            center = ax{2}{11}(1).ZData(1);
        end
        ZU=2*center-ZL; %force symmetry
    elseif ~drag_select && length(select)==1 && select<3
        ZU(i) = interp1(X1,ZU1,X(i),'linear','extrap'); %interpolate
    end
    
end

%Plot
if strcmp(mode{1},'top')
    set(ax{2}{11}(2),'XData',X,'YData',ZU)
    set(ax{2}{11}(3),'XData',X,'YData',ZL)
    if length(f.UserData)>4
        if length(ax{2})>11, delete(ax{2}{12}), end
        zero = zeros(1,4);
        ax{2}{12} = patch(f.UserData(3:6),f.UserData(7:10),zero,[0,0,0]);
    end
    if length(select)>1
        delete(ax{2}{12})
        zero=zeros(size(X(select==1|select==3)));
        ax{2}{12}=plot3(X(select==1|select==3),ZU(select==1|select==3),zero,'k.',...
            'MarkerSize',25);
        delete(ax{2}{13})
        zero=zeros(size(X(select==2|select==3)));
        ax{2}{13}=plot3(X(select==2|select==3),ZL(select==2|select==3),zero,'k.',...
            'MarkerSize',25);
    end
else
    set(ax{2}{11}(2),'XData',X,'ZData',ZU)
    set(ax{2}{11}(3),'XData',X,'ZData',ZL)
    if length(f.UserData)>4
        if length(ax{2})>11, delete(ax{2}{12}), end
        zero=zeros(1,4);
        ax{2}{12} = patch(f.UserData(3:6),zero,f.UserData(7:10),[0,0,0]);
    end
    if length(select)>1
        delete(ax{2}{12})
        zero=zeros(size(X(select==1|select==3)));
        ax{2}{12}=plot3(X(select==1|select==3),zero,ZU(select==1|select==3),'k.',...
            'MarkerSize',25);
        delete(ax{2}{13})
        zero=zeros(size(X(select==2|select==3)));
        ax{2}{13}=plot3(X(select==2|select==3),zero,ZL(select==2|select==3),'k.',...
            'MarkerSize',25);
    end
end
Pos.String = sprintf('(x=%.2f %s, z=%.2f %s)',x,unit,y,unit);

%Update
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL;
Update_Plot(type,mode)

end

function Release(f,~,mode,PT_In)%%%%%%%%%%%%%% RELEASE %%%%%%%%%%%%%%%%%%%%
global select New ax

%Collect Updated Body Parameters
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;
gray = [0.94,0.94,0.94]; 
set(findall(PT_In,'Style','edit'),'BackgroundColor',gray)

%Check for Selection Box
if length(select)>1 || select(1) < 4 %no selection box
    if length(ax{2})>12
        delete(ax{2}{12})
        delete(ax{2}{13})
    end
    select = 0;
elseif select==4 %selection box
    
    %Delete box
    delete(ax{2}{12}), ax{2}{12}=[];
    
    %Reset Axis Limits
    if strcmp(mode{1},'top')
        ax{3}.YLim = [min([ax{1}.YLim(1),0,ZL]),max([ax{1}.YLim(2),0,ZU])];
    else
        ax{3}.ZLim = [min([ax{1}.ZLim(1),0,ZL]),max([ax{1}.ZLim(2),0,ZU])];
    end
    ax{3}.XLim = [min([ax{1}.XLim(1),X]),max([ax{1}.XLim(2),X])];
    
    %Selected Nodes
    select = 0*X;
    xpos = f.UserData(3:4); ypos = f.UserData(8:9);
    for i=1:NX %1-upper 2-lower 3-both
        if X(i)>=xpos(1) && X(i)<=xpos(2) && ZU(i)>ypos(1) && ZU(i)<ypos(2)
            select(i) = 1;
        end
        if X(i)>=xpos(1) && X(i)<=xpos(2) && ZL(i)>ypos(1) && ZL(i)<ypos(2)
            if select(i), select(i) = 3; else, select(i) = 2; end
        end
    end
    if strcmp(mode{1},'top')
        zero = zeros(size(X(select==1|select==3)));
        ax{2}{12}=plot3(X(select==1|select==3),ZU(select==1|select==3),zero,'k.',...
            'MarkerSize',25);
        zero = zeros(size(X(select==2|select==3)));
        ax{2}{13}=plot3(X(select==2|select==3),ZL(select==2|select==3),zero,'k.',...
            'MarkerSize',25);
    else
        zero = zeros(size(X(select==1|select==3)));
        ax{2}{12}=plot3(X(select==1|select==3),zero,ZU(select==1|select==3),'k.',...
            'MarkerSize',25);
        zero = zeros(size(X(select==2|select==3)));
        ax{2}{13}=plot3(X(select==2|select==3),zero,ZL(select==2|select==3),'k.',...
            'MarkerSize',25);
    end
end

%Reset Drag Callback
f.WindowButtonMotionFcn = '';
f.UserData = [];
ax{3}.UserData = [];
ax{3}.Tag = '';

end

function Update_Plot(type,mode,NACA)%%%%%%%%%%% UPDATE PLOT %%%%%%%%%%%%%%%
global New ax L WG HT VT NP AERO_In

%Collect Updated Body Parameters
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;

%Update
PT.NX=NX; PT.X=X; PT.R=ZU-(ZU+ZL)/2; PT.ZU=ZU; PT.ZL=ZL;
if strcmp(type,'Fuselage')
    ax{2}{4} = Plot_Body(PT,ax{3},360,'',0,ax{2}{4});
    %ax{2}{4}.EdgeColor = 'none';
    uistack(ax{2}{4},'bottom')
elseif strcmp(type,'Body 2')
    PT.X0=X(1); PT.X=X-X(1); PT.Z0=0;
    if strcmp(mode{1},'top'), PT.Y0=mean((ZU+ZL)/2); end
    ax{2}{9} = Plot_Body(PT,ax{3},360,'',1,ax{2}{9});
  	set(ax{2}{9},'EdgeColor','none')
elseif strcmp(type,'Body 3')
    PT.X0=X(1); PT.X=X-X(1); PT.Z0=0;
    if strcmp(mode{1},'top'), PT.Y0=mean((ZU+ZL)/2); end
    ax{2}{10} = Plot_Body(PT,ax{3},360,'',1,ax{2}{10});
   	set(ax{2}{10},'EdgeColor','none')
elseif ~isempty(strfind(type,'Airfoil'))
    switch type
        case 'Wing Airfoil'
            if nargin>2, set(AERO_In(8+mode{2}),'String',NACA), end
            PT = WG; n=1; label = 'wing';
        case 'HT Airfoil'
            if nargin>2, set(AERO_In(11),'String',NACA), end
            PT = HT; n=2; label = 'ht';
        case 'VT Airfoil'
            PT = VT; n=3; label = 'vt';
        case 'Wing 2 Airfoil'
            PT = NP{1}; n=5; label = 'wing 2';
        case 'HT 2 Airfoil'
            PT = NP{2}; n=6; label = 'ht 2';
        case 'VT 2 Airfoil'
            PT = NP{3}; n=7; label = 'vt 2';
    end
    if strcmp(mode{1},'top')
        Z0=get(ax{2}{11}(1),'YData'); Z0=Z0(1);
    else
        Z0=get(ax{2}{11}(1),'ZData'); Z0=Z0(1);
    end
    X0 = X(1);
 	if mode{2}==2%if controlling tip rather than root
        Z0 = Z0-(PT.Ztip-PT.Z); X0 = X(1)-(PT.Xtip-PT.X); 
    end
    if strfind(label,'vt')
        PT.Y = Z0; PT.X = X0; 
    else
        PT.Z = Z0; PT.X = X0; 
    end
    delete(ax{2}{n})
    X = (X-X(1))/L; ZU = (ZU-Z0)/L; ZL = (ZL-Z0)/L;
    PT.DATA{mode{2}}=[fliplr(X),X;fliplr(ZL),ZU]';
    ax{2}{n} = Plot_Planform(PT,label,ax{3},50,50,1,'');
  	set(ax{2}{n},'EdgeColor','none')
end
alpha(0.2)

end

function setting(handle,~)%%%%%%%%%%%%%%%% SETTINGS TOGGLE %%%%%%%%%%%%%%%%

%Toggle Options
if strcmp(handle.Checked,'off')
    handle.Checked = 'on';
else
    handle.Checked = 'off';
end

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%% PLOT FUNCTIONS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Point(x,y,type,mode)%%%%%%%%%%%%%% POINT %%%%%%%%%%%%%%%%%%%
global New thresh ax select

%Collect Updated Body Parameters
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;

%If Multiple Points Selected
if length(select)>1
    NX=NX-length(find(select)); X(select>0)=[]; ZU(select>0)=[]; ZL(select>0)=[];
    delete(ax{2}{12}), delete(ax{2}{13}), select = 0;
else
    
    %Select Point
    if ~isnumeric(x) && length(select)==1
        manual = 1;
        ginput(1); %[x,y] only works on x-y plane
        pt=get(ax{3},'CurrentPoint');
        if strcmp(mode{1},'top')
            x=pt(1,1); y=pt(1,2);
        else
            x=pt(1,1); y=pt(1,3);
        end
    else
        manual = 0; %automated input (from draw mode)
    end
    x_check=find(abs(X-x)<thresh);
    if length(x_check)>1
        [closey1,i1]=min((ZU(x_check)-y).^2+(X(x_check)-x).^2);
        [closey2,i2]=min((ZU(x_check)-y).^2+(X(x_check)-x).^2);
        if closey1<closey2, i=x_check(i1); else, i=x_check(i2); end
        closex=abs(X(i)-x);
    else
        [closex,i]=min(abs(X-x));
    end
    
    if abs(ZU(i)-y)<abs(ZL(i)-y) %Upper Surface
        closey=abs(ZU(i)-y);
        if closex<thresh && closey<thresh && manual %Remove Point
            NX=NX-1; X(i)=[]; ZU(i)=[]; ZL(i)=[];
        else %Add Point
            NX=NX+1;
            if x<X(i)   %insert left
                X(i:NX) = X(i-1:NX-1);      X(i)=x;
                ZU(i:NX) = ZU(i-1:NX-1);    ZU(i)=y;
            else        %insert right
                X(i+1:NX) = X(i:NX-1);      X(i+1)=x;
                ZU(i+1:NX) = ZU(i:NX-1);    ZU(i+1)=y;
            end
            ZL = interp1(New.X,New.ZL,X,'linear','extrap');
        end
        if strcmp(mode{1},'top'), ZL=-ZU; end
    else %Lower Surface
        closey=abs(ZL(i)-y);
        if closex<thresh && closey<thresh && manual %Remove Point
            NX=NX-1; X(i)=[]; ZU(i)=[]; ZL(i)=[];
        else %Add Point
            NX=NX+1;
            if x<X(i)   %insert left
                X(i:NX) = X(i-1:NX-1);      X(i)=x;
                ZL(i:NX) = ZL(i-1:NX-1);    ZL(i)=y;
            else        %insert right
                X(i+1:NX) = X(i:NX-1);      X(i+1)=x;
                ZL(i+1:NX) = ZL(i:NX-1);    ZL(i+1)=y;
            end
            ZU = interp1(New.X,New.ZU,X,'linear','extrap');
        end
        if strcmp(mode{1},'top'), ZU=-ZL; end
    end
end

%Plot
zero=zeros(1,length(X));
if strcmp(mode{1},'top')
    set(ax{2}{11}(2),'XData',X,'YData',ZU,'ZData',zero)
    set(ax{2}{11}(3),'XData',X,'YData',ZL,'ZData',zero)   
else
    set(ax{2}{11}(2),'XData',X,'YData',zero,'ZData',ZU)
    set(ax{2}{11}(3),'XData',X,'YData',zero,'ZData',ZL)
end
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL;
Update_Plot(type,mode)

end

function Symmetry(~,~,i,type,mode)%%%%%%%%%%%%%%% SYMMETRY %%%%%%%%%%%%%%%%
global New ax opt2 select

%Turn on "Force Symmetry"
set(opt2,'Checked','on')

%Fit Points to 2nd-Order Polynomial
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;

%Choose Upper or Lower Surface to Copy
if strcmp(mode{1},'top')
    center = ax{2}{11}(1).YData(1);
else
    center = ax{2}{11}(1).ZData(1);
end
switch i
    case 1 %Copy Upper Surface Coordinates to Lower Surface
        if length(select)>1
            ZL(select>0) = 2*center-ZU(select>0);
        else
            ZL = 2*center-ZU;
        end
    case 2 %Copy Lower Surface Coordinates to Upper Surface
        if length(select)>1
            ZU(select>0) = 2*center-ZL(select>0);
        else
            ZU = 2*center-ZL;
        end
end

%Adjust Axes if Necessary
%Current Point
if strcmp(mode{1},'top') 
    if strcmp(type,'Fuselage') && isempty(ax{5}) 
        ax{3}.YLim = [min([ax{1}.YLim(1),0,ZL]),max([ax{1}.YLim(2),0,ZU])];
    end
else
    if strcmp(type,'Fuselage') && isempty(ax{5})
        ax{3}.ZLim = [min([ax{1}.ZLim(1),0,ZL]),max([ax{1}.ZLim(2),0,ZU])];
    end
end

%Plot
if strcmp(mode{1},'top')
    set(ax{2}{11}(2),'XData',X,'YData',ZU)
    set(ax{2}{11}(3),'XData',X,'YData',ZL)   
else
    set(ax{2}{11}(2),'XData',X,'ZData',ZU)
    set(ax{2}{11}(3),'XData',X,'ZData',ZL)
end
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL;
Update_Plot(type,mode)

end

function Smooth(~,~,type,mode)%%%%%%%%%%%%%% SMOOTH %%%%%%%%%%%%%%%%%
global New select ax thresh

%Fit Points to 2nd-Order Polynomial
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;

%Conditional Smoothing (Selected Points)
top = 1;
bottom = 1;
if length(select)>1
    X = X(select>0);
    if isempty(find(select==1|select==3,1)), top = 0; end
    if isempty(find(select==2|select==3,1)), bottom = 0; end
    ZU = ZU(select>0);
    ZL = ZL(select>0); 
    NX = length(X);
end

%Eliminate Corners
flatten = 'No';
dx = (X(2:end)-X(1:end-1)); wt = dx/(X(end)-X(1));
m_upper=(ZU(2:end)-ZU(1:end-1))./dx;
m_lower=(ZL(2:end)-ZL(1:end-1))./dx;
if top && mean(abs(m_upper.*wt))<thresh/20 && length(select)>1
    flatten = questdlg('Flatten selection to horizontal?');
    if strcmp(flatten,'Yes'), ZU(:) = mean(ZU); end
elseif bottom && mean(abs(m_lower.*wt))<thresh/20 && length(select)>1
  	flatten = questdlg('Flatten selection to horizontal?');
    if strcmp(flatten,'Yes'), ZL(:) = mean(ZL); end
elseif NX<=3 
  	flatten = questdlg('Flatten selection to horizontal?');
    if strcmp(flatten,'Yes'), ZU(:) = mean(ZU); ZL(:) = mean(ZL); end
end
if ~strcmp(flatten,'Yes')
    for i=2:NX-1
        if i==2, r=i-1:i+2; elseif i==NX-1, r=i-2:i+1; else, r=i-2:i+2; end
        %Upper Surface
        if abs(m_upper(i)-m_upper(i-1))>0.01 && top
            ZU(r)=polyval(polyfit(X(r),ZU(r),2),X(r));
        end
        %Lower Surface
        if abs(m_lower(i)-m_lower(i-1))>0.1 && bottom
            ZL(r)=polyval(polyfit(X(r),ZL(r),2),X(r));
        end
        
        %Fix Flipped Surfaces
        flipped=find((ZU-ZL)<0);
        if ~isempty(flipped)
            Z_temp=ZU(flipped);
            ZU(flipped)=ZL(flipped);
            ZL(flipped)=Z_temp;
        end
    end
end

%Re-structure
if length(select)>1
    ZU2 = ZU;       ZU = New.ZU;
    ZL2 = ZL;       ZL = New.ZL;
    NX = New.NX;    X = New.X;
    ZU(select>0) = ZU2;
    ZL(select>0) = ZL2;
   	delete(ax{2}{12})
	delete(ax{2}{13})
    if strcmp(mode{1},'top')
        zero = zeros(size(X(select==1|select==3)));
        ax{2}{12}=plot3(X(select==1|select==3),ZU(select==1|select==3),zero,'k.',...
            'MarkerSize',25);
        zero = zeros(size(X(select==2|select==3)));
        ax{2}{13}=plot3(X(select==2|select==3),ZL(select==2|select==3),zero,'k.',...
            'MarkerSize',25);
    else
        zero = zeros(size(X(select==1|select==3)));
        ax{2}{12}=plot3(X(select==1|select==3),zero,ZU(select==1|select==3),'k.',...
            'MarkerSize',25);
        zero = zeros(size(X(select==2|select==3)));
        ax{2}{13}=plot3(X(select==2|select==3),zero,ZL(select==2|select==3),'k.',...
            'MarkerSize',25);
    end
end

%Plot
if strcmp(mode{1},'top')
    set(ax{2}{11}(2),'XData',X,'YData',ZU)
    set(ax{2}{11}(3),'XData',X,'YData',ZL)   
else
    set(ax{2}{11}(2),'XData',X,'ZData',ZU)
    set(ax{2}{11}(3),'XData',X,'ZData',ZL)
end
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL;
Update_Plot(type,mode)

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%% RESET %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Reset(~,~,type,mode,PT_In)
global New Original BD select ax opt

%Reset to Initial Values
select = 0;
NX=Original.NX; X=Original.X; ZU=Original.ZU; ZL=Original.ZL; 

if ~strcmp(ax{3}.Tag,'save')
    if strcmp(type,'Fuselage')
        N = Original.N;
        for i=1:length(N), set(PT_In(2,i),'String',num2str(X(N(i)))), end
    elseif ~isempty(strfind(type,'Body'))
        N = Original.N;
        for i=1:length(N), set(PT_In(2,i),'String',num2str(X(N(i))-X(1))), end
        set(PT_In(1,8),'String',num2str(X(1)))
        if strcmp(mode{1},'top')
            set(PT_In(1,9),'String',num2str((ZU(1)+ZL(1))/2))
        else
            set(PT_In(1,10),'String',num2str((ZU(1)+ZL(1))/2))
        end
    else
        set(PT_In(14),'String',num2str(X(1)))
        if strcmp(mode{1},'top')
            set(PT_In(15),'String',num2str((ZU(1)+ZL(1))/2))
        else
            set(PT_In(16),'String',num2str((ZU(1)+ZL(1))/2))
        end
    end
end

%Plot
zero=zeros(1,length(X));
if strcmp(mode{1},'top')
    set(ax{2}{11}(2),'XData',X,'YData',ZU,'ZData',zero)
    set(ax{2}{11}(3),'XData',X,'YData',ZL,'ZData',zero)   
else
    set(ax{2}{11}(2),'XData',X,'YData',zero,'ZData',ZU)
    set(ax{2}{11}(3),'XData',X,'YData',zero,'ZData',ZL)
end
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL;
if strcmp(ax{3}.BeingDeleted,'on') %closing
   
    delete(ax{2}{11})
    delete(findall(ax{1},'Type','surface'))
    delete(findall(ax{1},'Type','line'))
    delete(findall(ax{1},'Type','text'))
    ax{2} = cell(1,11); ax{3} = [];
    if strcmp(get(opt(3),'Checked'),'on')
        D = BD.X(end)/2; axes(ax{1})
        plot3(ax{1},[0,0],1.25*[-D,D],[0,0],'k');
        text(0,1.35*D,0,'y');
        plot3(ax{1},[-0.4*D,2.4*D],[0,0],[0,0],'k');
        text(2.45*D,0,0,'x');
        plot3(ax{1},[0,0],[0,0],0.7*[-D,D],'k');
        text(0,0,0.8*D,'z');
    end
    if strcmp(ax{1}.Tag,'Aerodynamics')
        ax{3} = axes('Position',[0.41,0.15,0.5,0.3]);
    end

    AID(0,0,'update')
    pause(0.01) %allow time for update
    
    %Rotate Model Axes
    N=30; %steps for cool animation
    Az0 = Original.Az0; El0 = Original.El0;
    Az = 0;     dAz=(Az0-Az)/N;  
    if strcmp(mode{1},'top')
        El = 90;    dEl=-(90-El0)/N;
    else
        El = 0;     dEl=El0/N;  
    end
    
    %If Beyond 10 Deg
    if abs(dAz)>10/N || abs(dEl)>10/N
        axes(ax{1})
        for n=1:N
            El=El+dEl;  Az=Az+dAz;
            view(ax{1},[Az,El])
            delete(findall(ax{1},'Type','light'))
            camlight(-15,30), camlight(15,30)
            pause(0.001)
        end
    else
        if abs(El0)>45, El=90; else, El=0; end
        view(ax{1},[0,El])
    end
else
    Update_Plot(type,mode)
end

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SAVE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Save(~,~,type,analyze,mode,X0)
global ax New Original WG WG_In HT HT_In VT VT_In BD BD_In ...
    NP NP_In NB NB_In L

%Collect Updated New Parameters
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;

%Assign New S Values
S=pi*ZU.^2;

%Update
switch type
    case 'Fuselage'
        if NX>11
        	XP = linspace(X(1),X(end),11); 
            N = interp1(X,1:NX,XP,'nearest','extrap'); 
            if length(unique(N))<NX, N = [1:10,NX]; end
        else
            N = 1:NX; 
        end
        P = interp1(BD.X,BD.P,X(N),'linear','extrap');
        for i=1:min([NX,11])
            set(BD_In(1,i),'String',num2str(N(i)))
            set(BD_In(2,i),'String',num2str(round(X(N(i)),2)))
          	set(BD_In(3,i),'String',num2str(round(P(i),1)))
        end
        set(BD_In(1:3,i+1:11),'String','') 
        if ~range(P), set(BD_In(3,2:length(N)-1),'String',''), end
        BD.NX=NX; BD.X=X; BD.S=S; BD.N=N; 
        left = find(X<Original.X(1)); right = find(X>Original.X(end));
        if strcmp(mode{1},'top') 
            BD.R=ZU;
            if L==(Original.X(end)-Original.X(1)) %|| NX~=Original.NX
                ZU=interp1(Original.X,BD.ZU,X,'spline','extrap');
                ZL=interp1(Original.X,BD.ZL,X,'spline','extrap');
                ZU(left) = BD.ZU(1); ZU(right) = BD.ZU(end);
                ZL(left) = BD.ZL(1); ZL(right) = BD.ZL(end);
                BD.ZU = ZU; BD.ZL = ZL;
            end
        else
            BD.ZU=ZU; BD.ZL=ZL;
            if L==(Original.X(end)-Original.X(1)) %|| NX~=Original.NX
                R=interp1(Original.X,BD.R,X,'spline','extrap');
                R(left) = BD.R(1); R(right) = BD.R(end);
                BD.R = R;
            end
        end
    case 'Body 2'
        X=X-X(1); n = 1;
        if NX>7
        	XP = linspace(X(1),X(end),7); 
            N = interp1(X,1:NX,XP,'nearest','extrap'); 
            if length(unique(N))<NX, N = [1:6,NX]; end
        else
            N = 1:NX; 
        end
        P = interp1(NB{n}.X,NB{n}.P,X(N),'linear','extrap');
        for i=1:min([NX,7])
            set(NB_In{n}(1,i),'String',num2str(N(i)))
            set(NB_In{n}(2,i),'String',num2str(round(X(N(i)),2)))
            set(NB_In{n}(3,i),'String',num2str(round(P(i),1)))
        end
        set(NB_In{n}(1:3,i+1:7),'String','')
        if ~range(P), set(NB_In{n}(3,2:min([NX,7])-1),'String',''), end
        set(NB_In{n}(1,8),'String',num2str(round(New.X(1),2)))
        NB{n}.NX=NX; NB{n}.X=X; NB{n}.S=S; NB{n}.N=N; center=mean((ZU+ZL)/2); 
        left=find(X+X0<Original.X(1)); right=find(X+X0>Original.X(end));
        if strcmp(mode{1},'top')
            set(NB_In{n}(1,9),'String',num2str(round(center,2)))
            NB{n}.R = ZU-center;
            if L==(Original.X(end)-Original.X(1)) %|| NX~=Original.NX
                ZU=interp1(Original.X,NB{n}.ZU,X+X0,'spline','extrap');
                ZL=interp1(Original.X,NB{n}.ZL,X+X0,'spline','extrap');
                ZU(left) = NB{n}.ZU(1); ZU(right) = NB{n}.ZU(end);
                ZL(left) = NB{n}.ZL(1); ZL(right) = NB{n}.ZL(end);
                NB{n}.ZU = ZU; NB{n}.ZL = ZL;
            end
        else
            set(NB_In{n}(1,10),'String',num2str(round(center,2)))
            NB{n}.ZU=ZU-center; NB{n}.ZL=ZL-center;
            if L==(Original.X(end)-Original.X(1)) %|| NX~=Original.NX
                R=interp1(Original.X,NB{n}.R,X+X0,'spline','extrap');
                R(left) = NB{n}.R(1); R(right) = NB{n}.R(end);
                NB{n}.R = R;
            end
        end
    case 'Body 3'
        X=X-X(1); n = 2;
        if NX>7
        	XP = linspace(X(1),X(end),7); 
            N = interp1(X,1:NX,XP,'nearest','extrap'); 
            if length(unique(N))<NX, N = [1:6,NX]; end
        else
            N = 1:NX; 
        end
        P = interp1(NB{n}.X,NB{n}.P,X(N),'linear','extrap');
        for i=1:min([NX,7])
            set(NB_In{n}(1,i),'String',num2str(N(i)))
            set(NB_In{n}(2,i),'String',num2str(round(X(N(i)),2)))
            set(NB_In{n}(3,i),'String',num2str(round(P(i),1)))
        end
        set(NB_In{n}(1:3,i+1:7),'String','')
        if ~range(P), set(NB_In{n}(3,2:min([NX,7])-1),'String',''), end
        set(NB_In{n}(1,8),'String',num2str(round(New.X(1),2)))
        NB{n}.NX=NX; NB{n}.X=X; NB{n}.S=S; NB{n}.N=N; center=mean((ZU+ZL)/2); 
        left=find(X+X0<Original.X(1)); right=find(X+X0>Original.X(end));
        if strcmp(mode{1},'top')
            set(NB_In{n}(1,9),'String',num2str(round(center,2)))
            NB{n}.R = ZU-center;
            if L==(Original.X(end)-Original.X(1)) %|| NX~=Original.NX
                ZU=interp1(Original.X,NB{n}.ZU,X+X0,'spline','extrap');
                ZL=interp1(Original.X,NB{n}.ZL,X+X0,'spline','extrap');
                ZU(left) = NB{n}.ZU(1); ZU(right) = NB{n}.ZU(end);
                ZL(left) = NB{n}.ZL(1); ZL(right) = NB{n}.ZL(end);
                NB{n}.ZU = ZU; NB{n}.ZL = ZL;
            end
        else
            set(NB_In{n}(1,10),'String',num2str(round(center,2)))
            NB{n}.ZU=ZU-center; NB{n}.ZL=ZL-center;
            if L==(Original.X(end)-Original.X(1)) %|| NX~=Original.NX
                R=interp1(Original.X,NB{n}.R,X+X0,'spline','extrap');
                R(left) = NB{n}.R(1); R(right) = NB{n}.R(end);
                NB{n}.R = R;
            end
        end
    case 'Wing Airfoil'
        [WG,WG_In] = Airfoil_Analysis(WG,WG_In,mode,analyze);
    case 'HT Airfoil'
        [HT,HT_In] = Airfoil_Analysis(HT,HT_In,mode,analyze);
    case 'VT Airfoil'
        [VT,VT_In] = Airfoil_Analysis(VT,VT_In,mode,analyze);
    case 'Wing 2 Airfoil'
        [NP{1},NP_In{1}] = Airfoil_Analysis(NP{1},NP_In{1},mode,analyze);
    case 'HT 2 Airfoil'
        [NP{2},NP_In{2}] = Airfoil_Analysis(NP{2},NP_In{2},mode,analyze);
    case 'VT 2 Airfoil'
        [NP{3},NP_In{3}] = Airfoil_Analysis(NP{3},NP_In{3},mode,analyze);
end

%Close Window
%delete(findall(ax{1},'Type','surface'))
f=ancestor(ax{3},'figure'); set(ax{3},'Tag','save')
if isvalid(f), close(f), end

%Update
% ax{2}=cell(1,10); ax{3} = []; axes(ax{1})
% if strcmp(type,'Fuselage')||strcmp(type,'Body 2')||strcmp(type,'Body 3')
%     AID(0,0,'update','fuse')
% else
%     AID(0,0,'update')
% end

end

function [PT,PT_In] = Airfoil_Analysis(PT,PT_In,mode,analyze)%%% AIRFOIL %%
global New L ax

%Perform Analysis for Selected Airfoil
X=New.X; ZU=New.ZU; ZL=New.ZL; 
if strcmp(mode{1},'top')
    Z0=get(ax{2}{11}(1),'YData'); Z0=Z0(1);
else
    Z0=get(ax{2}{11}(1),'ZData'); Z0=Z0(1);
end
X = (X-X(1))/L; ZU = (ZU-Z0)/L; ZL = (ZL-Z0)/L;
if ZU(1) == ZL(1) %correct leading edge
    XU = X(2:end); ZU = ZU(2:end);
else
    XU = [X(1)-1e-6,X]; ZU=[(ZL(1)+ZU(1))/2,ZU];
end
if mode{2}>length(PT.DATA), PT.DATA{mode{2}} = PT.DATA{1}; end
data = PT.DATA{mode{2}};
PT.DATA{mode{2}}=[fliplr(X),XU;fliplr(ZL),ZU]';
if length(data) ~= length(PT.DATA) || any(any(abs(PT.DATA-data)>1e-8))
    PT.NACA{mode{2}}='Data.'; %if profile adjusted
end
PT.TC = max(PT.DATA{mode{2}}(:,2))-min(PT.DATA{mode{2}}(:,2));
set(PT_In(11),'String',sprintf('%.2f',PT.TC))
if analyze, PT=Lift_Curve_Slope(PT,mode{2}); end

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%% SENSITIVITY %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Sensitivity(~,~,option,i)
global thresh L

%Check Option
switch i
    case 1
        set(option(1),'Checked','on')
        set(option(2),'Checked','off')
        set(option(3),'Checked','off')
        thresh = 0.005*L;
    case 2
        set(option(1),'Checked','off')
        set(option(2),'Checked','on')
        set(option(3),'Checked','off')
        thresh = 0.02*L;
    case 3
        set(option(1),'Checked','off')
        set(option(2),'Checked','off')
        set(option(3),'Checked','on')
        thresh = 0.1*L;
end

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%% DISTRIBUTION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Distribution(~,~,option,i,type,mode)
global New ax L

%Collect Updated Body Parameters
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;

%Check Option
switch i
    case 1
        set(option(1),'Checked','on')
        set(option(2),'Checked','off')
        set(option(3),'Checked','off')
        DX = 0:L/(NX-1):L;
        ZU=interp1(X,ZU,DX,'linear','extrap');
        ZL=interp1(X,ZL,DX,'linear','extrap');
        X = DX;
    case 2
        set(option(1),'Checked','off')
        set(option(2),'Checked','on')
        set(option(3),'Checked','off')
        switch NX
            case 11
                DX = [0,0.025,0.05,0.075,0.1,0.15,0.25,0.5,0.75,0.9,1]*L;
                ZU=interp1(X,ZU,DX,'linear','extrap');
                ZL=interp1(X,ZL,DX,'linear','extrap');
                X = DX;
        end
    case 3
        set(option(1),'Checked','off')
        set(option(2),'Checked','off')
        set(option(3),'Checked','on')
end

%Plot
zero=zeros(1,length(X));
if strcmp(mode{1},'top')
    set(ax{2}{11}(2),'XData',X,'YData',ZU,'ZData',zero)
    set(ax{2}{11}(3),'XData',X,'YData',ZL,'ZData',zero)   
else
    set(ax{2}{11}(2),'XData',X,'YData',zero,'ZData',ZU)
    set(ax{2}{11}(3),'XData',X,'YData',zero,'ZData',ZL)
end
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL;
Update_Plot(type,mode)

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%% SCALE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Scale(~,~,scale,i,unit,mode,type)
global L Pos New ax

%Collect Updated Body Parameters
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;

%Scale Length
switch i
    case 1
        L = L/2;    X=X(1)+(X-X(1))/2;
    case 2
        L = L*4/5;  X=X(1)+(X-X(1))*4/5;
    case 3
        L = L*5/4;  X=X(1)+(X-X(1))*5/4;
    case 4
        L = L*2;    X=X(1)+(X-X(1))*2;
    case 5
        len = inputdlg(sprintf('Length, %s',unit),'Scale',1,{num2str(L)});
        l = eval(len{1}); X=X(1)+(X-X(1))*l/L; L = l;
    case 6
        ZU = ZU/2;      ZL = ZL/2;
    case 7
        ZU = 4*ZU/5;    ZL = 4*ZL/5;
    case 8
        ZU = 5*ZU/4;    ZL = 5*ZL/4;
    case 9
        ZU = 2*ZU;      ZL = 2*ZL;
    case 10
        sf = inputdlg('Scaling Factor','Scale',1,{'1'});
        sf = eval(sf{1}); ZU = sf*ZU; ZL = sf*ZL;
end

if i<6
    %Update Values
    set(scale(1),'Label',sprintf('50%% (L=%.1f %s)',L/2,unit));
    set(scale(2),'Label',sprintf('80%% (L=%.1f %s)',4*L/5,unit));
    set(scale(3),'Label',sprintf('125%% (L=%.1f %s)',5*L/4,unit));
    set(scale(4),'Label',sprintf('200%% (L=%.1f %s)',2*L,unit));
    len = sprintf('Length = %.2f %s',L,unit);
    set(Pos,'String',len,'BackgroundColor',[0,1,0])
end

%Plot
if strcmp(mode{1},'top')
    set(ax{2}{11}(2),'XData',X,'YData',ZU)
    set(ax{2}{11}(3),'XData',X,'YData',ZL)   
else
    set(ax{2}{11}(2),'XData',X,'ZData',ZU)
    set(ax{2}{11}(3),'XData',X,'ZData',ZL)
end
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL;
Update_Plot(type,mode)

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%% GEOMETRY %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function Geometry(handle,~,type,mode,X0,Z0,PT)
global New ax BD NB L

%Collect Updated Body Parameters
NX=New.NX; X=New.X; ZU=New.ZU; ZL=New.ZL;

%Scale Length
NACA = ''; 
switch get(handle,'Label')
    case 'Match Root'
        data = PT.DATA{1};
        NX = ceil(length(data)/2);
        if mod(length(data),2), data(NX+1:end+1,:) = data(NX:end,:); end %even
        X = fliplr(data(1:NX,1)');
        ZU = data(end-NX+1:end,2)';
        ZL = fliplr(data(1:NX,2)');
        if mean(ZL)>mean(ZU)
            Z = ZL; ZL = ZU; ZU = Z;
        end
    case 'Match Tip'
        if 2>length(PT.DATA), PT.DATA{2} = PT.DATA{1}; end
        data = PT.DATA{2};
        NX = ceil(length(data)/2);
        if mod(length(data),2), data(NX+1:end+1,:) = data(NX:end,:); end %even
        X = fliplr(data(1:NX,1)');
        ZU = data(end-NX+1:end,2)';
        ZL = fliplr(data(1:NX,2)');
        if mean(ZL)>mean(ZU)
            Z = ZL; ZL = ZU; ZU = Z;
        end
    case 'NACA'
        inpts = {'Input NACA Designation','Number of Points'};
        default = {'0012','120'};
        if isempty(strfind(type,'Airfoil')), default{2} = '24'; end
        outpts = inputdlg(inpts,'Airfoil Input',1,default);
        NACA = outpts{1}; N = eval(outpts{2});
        Data = NACA_Panel_Maker(N,NACA);
        NX=floor(length(Data)/2); X=fliplr(Data(1:NX,1)');
        ZU=Data(end-NX+1:end,2)'; ZL=fliplr(Data(1:NX,2)');
        if mean(ZL)>mean(ZU), Z=ZL; ZL=ZU; ZU=Z; end
    case 'Load Data'
        PT.NACA{mode{2}} = 'Load_pts.';
        [Data,NACA]=Panel_Points(PT,mode{2}); if isempty(Data), return, end
        NX=floor(length(Data)/2); X=fliplr(Data(1:NX,1)');
        ZU=Data(end-NX+1:end,2)'; ZL=fliplr(Data(1:NX,2)');
        if mean(ZL)>mean(ZU), Z=ZL; ZL=ZU; ZU=Z; end
    case 'Paste Points'
        PT.NACA{mode{2}} = 'Type_pts.';
        [Data,NACA]=Panel_Points(PT,mode{2}); if isempty(Data), return, end
        NX=floor(length(Data)/2); X=fliplr(Data(1:NX,1)');
        ZU=Data(end-NX+1:end,2)'; ZL=fliplr(Data(1:NX,2)');
        if mean(ZL)>mean(ZU), Z=ZL; ZL=ZU; ZU=Z; end
    case 'Flat Plate'
        NX=11; X=linspace(0,1,NX); ZU=0.05*ones(1,NX); ZL=-ZU; 
        NX=12; X(end+1)=X(end); ZU(end+1)=0; ZL(end+1)=0; %fix TE
    case 'Small Jet'
        X = [0.0747 0.2897 3.3305 3.8220 4.5899 5.0506 5.6342 14.2010 19.0404 21.6058 24]/24;
        if strcmp(type,'Fuselage') && strcmp(mode{1},'top')
            BD.ZU = [0.0384 0.2841 1.1442 1.4206 1.8175 2.0042 2.1270 2.1241 2.0814 2.0790 2.0789]*L/24;
            BD.ZL = [-0.0900 -0.1943 -0.39 -0.4 -0.4 -0.4 -0.4 -0.3 0.5 1.1442 1.7277]*L/24;
            ZU = [0.1312 0.3061 1.1807 1.2973 1.4139 1.4139 1.4139 1.1224 0.7142 0.4810 0.2478]/24;
            ZL = -ZU;
        elseif strcmp(type,'Fuselage')
            ZU = [0.0384 0.2841 1.1442 1.4206 1.8175 2.0042 2.1270 2.1241 2.0814 2.0790 2.0789]/24;
            ZL = [-0.0900 -0.1943 -0.39 -0.4 -0.4 -0.4 -0.4 -0.3 0.5 1.1442 1.7277]/24;
            BD.R = [0.1312 0.3061 1.1807 1.2973 1.4139 1.4139 1.4139 1.1224 0.7142 0.4810 0.2478]*L/24;
        end
        NX = length(X);
        L = L+1e-6; %don't interpolate R/ZU/ZL upon save
    case 'Airliner'
        X = [0.3000 0.6000 1 1.7000 2.6000 18.7000 19.6000 21.2000 22.2000 23.1000 24]/24;
        if strcmp(type,'Fuselage') && strcmp(mode{1},'top')
            BD.ZU = [-0.0125 0.5339 0.9962 1.3325 1.5006 1.4943 1.4677 1.4003 1.2964 1.1740 1.0819]*L/24;
            BD.ZL = [-0.0125 -0.3058 -0.5694 -0.8046 -0.9791 -0.9689 -0.8411 -0.4208 -0.0846 0.3356 0.7439]*L/24;
            ZU = [0.0 0.4538 0.7524 1.0420 1.2123 1.2135 1.1912 0.9484 0.7338 0.4304 0.1362]/24;
            ZL = -ZU;
        elseif strcmp(type,'Fuselage')
            ZU = [-0.0125 0.5339 0.9962 1.3325 1.5006 1.4943 1.4677 1.4003 1.2964 1.1740 1.0819]/24;
            ZL = [-0.0125 -0.3058 -0.5694 -0.8046 -0.9791 -0.9689 -0.8411 -0.4208 -0.0846 0.3356 0.7439]/24;
            BD.R = [0.0 0.4538 0.7524 1.0420 1.2123 1.2135 1.1912 0.9484 0.7338 0.4304 0.1362]*L/24;
        end
        NX = length(X);
        L = L+1e-6; %don't interpolate R/ZU/ZL upon save
        
    case 'Turbofan Engine'
        if strcmp(type,'Body 2') 
            n = 1;
        elseif strcmp(type,'Body 3')
            n = 2;
        else
            return
        end
        L0 = BD.X(end)-BD.X(1);
        X = [0 -0.1700 -0.2000 -0.0400 0.4700 1.5800 2.2726 1.8153 2.4885 3.0800]/24*L0/L;
        R = [0.6231 0.6532 0.7542 0.8803 1.0160 0.9730 0.7582 0.4628 0.2211 0]/24*L0;
        if strcmp(mode{1},'top')
            ZU = R/L;       NB{n}.ZU = R;     
           	ZL = -R/L;  	NB{n}.ZL = -R;
        else
            ZU = R/L;       NB{n}.R = R;
            ZL = -R/L;
        end
        NX = length(X);
        L = L+1e-6; %don't interpolate R/ZU/ZL upon save
    case 'Ellipse/Other'
        inpts = {'t range','X(t)','ZU(t)','ZL(t)'};
        default = handle.UserData;
        outpts = inputdlg(inpts,'Parametric Function',1,default);
        handle.UserData = outpts;
        if ~isempty(outpts)
            eval(outpts{1});
            eval(outpts{2});
            eval(outpts{3});
            eval(outpts{4});
            NX = length(X);
        end
    otherwise
        return
end

%Correct Position
X=X*L+X0; ZL=ZL*L+Z0; ZU=ZU*L+Z0;

%Plot
zero=zeros(1,length(X));
if strcmp(mode{1},'top')
    set(ax{2}{11}(2),'XData',X,'YData',ZU,'ZData',zero)
    set(ax{2}{11}(3),'XData',X,'YData',ZL,'ZData',zero)   
else
    set(ax{2}{11}(2),'XData',X,'YData',zero,'ZData',ZU)
    set(ax{2}{11}(3),'XData',X,'YData',zero,'ZData',ZL)
end
New.NX=NX; New.X=X; New.ZU=ZU; New.ZL=ZL;
if ~isempty(NACA)
    Update_Plot(type,mode,NACA)
else
    Update_Plot(type,mode)
end

end

function Scroll(~,object)%%%%%%%%%%%%%%%%% SCROLL %%%%%%%%%%%%%%%%%%%%%%%
global ax

obj = gco;
if ~isempty(obj) && strcmp(obj.Type,'image')
    obj = ax{5}{1}; pos = obj.CurrentPoint;
    x0 = pos(1,1);              y0 = pos(1,2);
    xlim = obj.XLim;            ylim = obj.YLim;
    xrange = xlim(2)-xlim(1);   yrange = ylim(2)-ylim(1);
    xp = (x0-xlim(1))/xrange;   yp = (y0-ylim(1))/yrange;
    dx = -xrange/10*object.VerticalScrollCount;
    dy = -yrange/10*object.VerticalScrollCount;
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
    cm = camva(ax{3});
    camva(ax{3},cm-object.VerticalScrollCount/20)
end
end

function Drag(~,~,f,choice)%%%%%%%%%%%%%%%%%%% DRAG %%%%%%%%%%%%%%%%%%%%%%%
global ax

%Mouse Position
pt_old = ax{3}.UserData;
pt_new = f.CurrentPoint;
dx = pt_new(1,1) - pt_old(1,1);
dy = pt_new(1,2) - pt_old(1,2);

%Drag Type
switch choice
    case 'pan'
        pos = ax{3}.Position;
        pos(1) = pos(1) + dx;
        pos(2) = pos(2) + dy;
        ax{3}.Position = pos;
    case 'drag image'
        pos = ax{5}{1}.Position;
        pos(1) = pos(1)+dx; pos(2) = pos(2)+dy;
        ax{5}{1}.Position = pos;
    case 'scale image'
        pos = ax{5}{1}.Position;
        pos(3) = pos(3)+dx; pos(4) = pos(4)+dy;
        ax{5}{1}.Position = pos;
    case 'scale image 2'
        pos = ax{5}{1}.Position;
        w_h=pos(3)/pos(4);
        if abs(dx)>abs(dy), dy = w_h*dx; else, dx = dy/w_h; end
        pos(3) = pos(3)+dx; pos(4) = pos(4)+dy;
        ax{5}{1}.Position = pos;
end
ax{3}.UserData = pt_new;

end



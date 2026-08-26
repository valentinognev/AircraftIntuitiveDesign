function DATCOM_IO(CaseID,type,choice,cg_calc,unit)

%Read/Write DATCOM for005.dat input file
if nargin<5
    Read_DATCOM(CaseID,type);
else
    %if exist('Models','dir') && isempty(strfind(CaseID,'.dat'))
        %cd Models, fl = 1;  else, fl = 0; end
    Write_DATCOM(CaseID,type,choice,cg_calc,unit);
    %if fl, cd .., end
end

end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%% READ %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function Read_DATCOM(Fn,P)
global WG_In WG HT_In HT VT_In VT BD_In BD AERO_In AERO ...
    F_In F A_In A E_In E R_In R NP NB Results opt

re_initialize = 0;
Cfid = ''; Pfid = '';
if ~iscell(Fn)
    fid=fopen([P,Fn]); var = '';
    while isempty(strfind(var,'ID'))
        line = fgetl(fid);
        if ~isempty(line), in=textscan(line,'%s\t%s'); end
        var = in{1}{1}; val = in{2}{1};
        if strcmp(var,'DIM') && ~strcmpi(val,unit)
            re_initialize = 1;
            if strcmpi(val,'in')
                set(opt(14),'Checked','on')
            else
                set(opt(14),'Checked','off')
            end
        end
    end
    if strfind(var,'CASEID')
        Cfid = fid; ID = line(8:end);
    else
        Pfid = fid;
    end
else
    fid=fopen([P,Fn{1}]); var = '';
    while isempty(strfind(var,'ID'))
        line = fgetl(fid);
        if ~isempty(line), in=textscan(line,'%s\t%s'); end
        var = in{1}; val = in{2};
        if iscell(var), var=var{1}; val=line(8:end); end
        if strcmp(var,'DIM') && ~strcmpi(val,unit)
            re_initialize = 1;
            if strcmpi(val,'in')
                set(opt(14),'Checked','on')
            else
                set(opt(14),'Checked','off')
            end
        end
    end
    if strfind(var,'CASEID')
        Cfid = fid; ID = line(8:end);
        Pfid = fopen([P,Fn{2}]);
    else
        Pfid = fid;
        Cfid = fopen([P,Fn{2}]);
        line = fgetl(Cfid); ID=line(8:end);
    end
end

%Case fid (Standard DATCOM Input fid - for005.dat)
if ~isempty(Cfid)
    
    CaseID = ID;
    set(gcf,'Tag',CaseID)
    fid = Cfid;
    
    %Retrieve Datcom Input fid
    clearvars WG HT VT F A E AC, Results = {};
    
    %Reset CG Values
    cg_data = cell(3,10);
    for i=1:3, for j=1:10, cg_data{i,j} = '0'; end, end
    set(opt(1),'UserData',cg_data)
    
    %Required Synthesesis Parameters
    AERO.XW=0; AERO.YW=0; AERO.ZW=0; AERO.ALIW=0;
    AERO.XH=0; AERO.YH=0; AERO.ZH=0; AERO.ALIH=0;
    AERO.XV=0; AERO.YV=0; AERO.ZV=0;
    AERO.NALPHA=1; AERO.NALT=1; AERO.NMACH=1;
    
    %Reset Break
    WG.SSPNOP=0; HT.SSPNOP=0; VT.SSPNOP=0;
    
    %Initialize Control Surfaces
    F.FTYPE=1; F.PHETE=0.003; F.PHETEP=0.002; F.TC=0.22; F.CB=0.3;
    E.FTYPE=1; E.PHETE=0.003; E.PHETEP=0.002; E.TC=0.22; E.CB=0.3;
    A.STYPE=1;
    
    %Categorize Variables
    Text=''; while ~feof(fid), Text=strcat(Text,fgetl(fid)); end
    Index=[1,strfind(Text,'='),length(Text)];
    Elem=Text(Index(1):Index(2)-1);
    Fix_1=strfind(Elem,'(1)');   Elem(Fix_1:Fix_1+2)=[];
    Commas=0; Spaces=strfind(Elem,' '); Money=0;
    Comp=zeros(1,length(Index)); Stay=[0 0 0 0 0 0 0];
    plt_bd=0; plt_wg=0; plt_ht=0; plt_vt=0;
    
    for k=2:length(Index)-1
        %Read Previous Variable Name
        Start=max([Commas(end),Spaces(end),Money(end)])+1;
        Name=Elem(Start:end); Name_Fix=strfind(Name,'(');
        if Name_Fix, Name(Name_Fix:end)=[]; end
        if isempty(Name), Name=sprintf('Undefined'); end
        
        %Move to the Next Value
        Elem=Text(Index(k):Index(k+1)-1);
        Fix_1=strfind(Elem,'(1)');   Elem(Fix_1:Fix_1+2)=[];
        
        %Airfoils and Thickness
        WG.NACA = {'2412'}; WG.TC = 0.12;
        HT.NACA = {'0012'}; HT.TC = 0.12;
        VT.NACA = {'0012'}; VT.TC = 0.12;
%         isempty(strfind(Elem,'NACA-W'))
%         if ~isempty(strfind(Elem,'NACA-W'))
%             dash=strfind(Elem,'-'); space=strfind(Elem,' $');
%             WG.NACA={Elem(dash(end)+1:space(1)-1)};
%             WG.TC=str2double(WG.NACA{1}(end-1:end))/100;
%         elseif ~isempty(strfind(Elem,'NACA-H'))
%             dash=strfind(Elem,'-'); space=strfind(Elem,' $');
%             HT.NACA={Elem(dash(end)+1:space(1)-1)};
%             HT.TC=str2double(HT.NACA{1}(end-1:end))/100;
%         elseif ~isempty(strfind(Elem,'NACA-V'))
%             dash=strfind(Elem,'-'); space=strfind(Elem,' $');
%             VT.NACA={Elem(dash(end)+1:space(1)-1)};
%             VT.TC=str2double(VT.NACA{1}(end-1:end))/100;
%         end
        
        %Distinguish Components
        if ~isempty(strfind(Elem,'BODY')),  Comp(k+1)=1; plt_bd=1; end
        if ~isempty(strfind(Elem,'WGPLNF')),Comp(k+1)=2; plt_wg=1; end
        if ~isempty(strfind(Elem,'HTPLNF')),Comp(k+1)=3; plt_ht=1; end
        if ~isempty(strfind(Elem,'VTPLNF')),Comp(k+1)=4; plt_vt=1; end
        if ~isempty(strfind(Elem,'ASYFLP')),Comp(k+1)=6;            end
        if ~isempty(strfind(Elem,'SYMFLP')),Comp(k+1)=find(Stay)+1; end
        
        %Find Indices
        Commas=[0,strfind(Elem,',')];
        Spaces=[0,strfind(Elem,' ')];
        Money=[0,strfind(Elem,'$')];
        
        %Categorize Results
        I=[Commas,length(Elem)];
        if length(Money)>1, I(end)=Money(2); end
        if length(Commas)>3 %If Containing Multiple Values
            I=[1,I(2:end)]; Value = zeros(1,length(I)-1);
            for j=1:length(I)-1
                Value(j)=str2double(Elem(I(j)+1:I(j+1)-1));
            end
        else %Just One Value
            Value=str2double(Elem(2:I(2)-1));
        end
        Value(isnan(Value))=[]; %Remove any NaNs
        
        %Assign to Respective Component
        if Comp(k)==7 || (Stay(7) && Comp(k)==0)
            E.(Name)=Value; Stay=[0 0 0 0 0 0 1];
        elseif Comp(k)==6 || (Stay(6) && Comp(k)==0)
            A.(Name)=Value; Stay=[0 0 0 0 0 1 0];
        elseif Comp(k)==5 || (Stay(5) && Comp(k)==0)
            F.(Name)=Value; Stay=[0 0 0 0 1 0 0];
        elseif Comp(k)==4 || (Stay(4) && Comp(k)==0)
            VT.(Name)=Value; Stay=[0 0 0 1 0 0 0];
        elseif Comp(k)==3 || (Stay(3) && Comp(k)==0)
            HT.(Name)=Value; Stay=[0 0 1 0 0 0 0];
        elseif Comp(k)==2 || (Stay(2) && Comp(k)==0)
            WG.(Name)=Value; Stay=[0 1 0 0 0 0 0];
        elseif Comp(k)==1 || (Stay(1) && Comp(k)==0)
            BD.(Name)=Value; Stay=[1 0 0 0 0 0 0];
        else
            %Assign Uncategorized Values
            if ~isempty(Value)
                eval(sprintf('AERO.%s=str2num(''%s'');',...
                    Name,num2str(Value)))
            end
        end
    end
    fclose(fid);
    
    %Check for Airfoil Data
    choice = {};
    if isfield(WG,'XCORD')
        WG.NACA = {'Data.'}; set(AERO_In(10),'String',WG.NACA{1})
        WG.DATA{1}(:,1)=[fliplr(WG.XCORD),WG.XCORD]';
        WG.DATA{1}(:,2)=[fliplr(WG.YUPPER),WG.YLOWER]';
        WG.TC = max(WG.DATA{1}(:,2))-min(WG.DATA{1}(:,2));
    else
        set(AERO_In(9:10),'String',WG.NACA{1})
        WG.DATA={NACA_Panel_Maker(100,WG.NACA{1})};
    end
    choice{1} = WG.DATA{1};
    if isfield(HT,'XCORD')
        HT.NACA = {'Data.'}; set(AERO_In(11),'String',HT.NACA{1})
        HT.DATA{1}(:,1)=[fliplr(HT.XCORD),HT.XCORD]';
        HT.DATA{1}(:,2)=[fliplr(HT.YUPPER),HT.YLOWER]';
        HT.TC = max(HT.DATA{1}(:,2))-min(HT.DATA{1}(:,2));
    else
        set(AERO_In(11),'String',HT.NACA{1})
        HT.DATA={NACA_Panel_Maker(50,HT.NACA{1})};
    end
    choice{2} = HT.DATA{1};
    if isfield(VT,'XCORD')
        WG.NACA = {'Data.'};
        VT.DATA{1}(:,1)=[fliplr(VT.XCORD),VT.XCORD]';
        VT.DATA{1}(:,2)=[fliplr(VT.YUPPER),VT.YLOWER]';
        VT.TC = max(VT.DATA{1}(:,2))-min(VT.DATA{1}(:,2));
    else
        VT.DATA={NACA_Panel_Maker(50,VT.NACA{1})};
    end
    choice{3} = VT.DATA{1};
    
    %Fix SSPNOP
    if WG.SSPNOP, WG.SSPNOP =  WG.SSPN-WG.SSPNOP; end
    if HT.SSPNOP, HT.SSPNOP =  HT.SSPN-HT.SSPNOP; end
    if VT.SSPNOP, VT.SSPNOP =  VT.SSPN-VT.SSPNOP; end
    
    %Synthesis Parameters
    WG.X=AERO.XW; WG.Y=AERO.YW; WG.Z=AERO.ZW; WG.i=AERO.ALIW;
    HT.X=AERO.XH; HT.Y=AERO.YH; HT.Z=AERO.ZH; HT.i=AERO.ALIH;
    VT.X=AERO.XV; VT.Y=AERO.YV; VT.Z=AERO.ZV;
    
    %Default Parameters
    if isfield(BD,'X')
        X=BD.X; BD.NX=length(X); L=X(BD.NX);
    else
        L=str2double(inputdlg('Fuselage Length'));
    end
    WG_Def={L/4,L/4,L/4,L/2,L/4,0,0,0,0,0,0.12,0,0,WG.X,0,WG.Z};
    HT_Def={L/8,L/8,L/8,L/4,7*L/8,0,0,0,0,0,0.12,0,0,HT.X,0,HT.Z};
    VT_Def={L/8,L/8,L/8,L/6,7*L/8,0,0,0,0,0,0.12,0,0,VT.X,0,VT.Z};
    F_Default={L/12,L/4,L/12,L/12,0,0};
    A_Default={L/4,L/2,L/24,L/24,0,0};
    E_Default={L/12,L/4,L/24,L/24,0,0};
    R_Default={0,L/4,L/24,L/24,0,0};
    AERO_Default={'-4:4:12',0,0.03,25,L/4,0,...
        '1000','1000','2412','2412','0012'};
    
    %Initialize Planform Parameters
    RP={'CHRDR','CHRDBP','CHRDTP','SSPN','SSPNOP',...
        'SAVSI','SAVSO','CHSTAT','DHDADI','DHDADO',...
        'TC','TWISTA','i','X','Y','Z'};
    
    for k=1:length(RP)
        if ~isfield(WG,RP{k}), WG.(RP{k})=WG_Def{k}; end
        set(WG_In(k),'String',num2str(WG.(RP{k})));
        if ~isfield(HT,RP{k}), HT.(RP{k})=HT_Def{k}; end
        set(HT_In(k),'String',num2str(HT.(RP{k})))
        if ~isfield(VT,RP{k}), VT.(RP{k})=VT_Def{k}; end
        set(VT_In(k),'String',num2str(VT.(RP{k})));
    end
    
    %Initialize Control Surface Parameters
    RF={'SPANFI','SPANFO','CHRDFI','CHRDFO','DELTA'};
    for k=1:length(RF)
        if ~isfield(F,RF{k}), F.(RF{k})=F_Default{k}; end
        set(F_In(k),'String',num2str(F.(RF{k})));
        if ~isfield(E,RF{k}), E.(RF{k})=E_Default{k}; end
        set(E_In(k),'String',num2str(E.(RF{k})));
        R.(RF{k})=R_Default{k};
        set(R_In(k),'String',num2str(R.(RF{k})));
    end
    if length(F.DELTA)>1            %array of deflections
        del = F.DELTA;
        ddel = del(2:end)-del(1:end-1);
        if ~sum(ddel-ddel(1))       %uniform spacing
            del1 = num2str(del(1));
            ddel = num2str(ddel(1));
            del2 = num2str(del(end));
            set(F_In(end),'String',[del1,':',ddel,':',del2]);
        end
    end
    if length(E.DELTA)>1            %array of deflections
        del = E.DELTA;
        ddel = del(2:end)-del(1:end-1);
        if ~sum(ddel-ddel(1))       %uniform spacing
            del1 = num2str(del(1));
            ddel = num2str(ddel(1));
            del2 = num2str(del(end));
            set(E_In(end),'String',[del1,':',ddel,':',del2]);
        end
    end
    RC=[RF(1:end-1),{'DELTAL','DELTAR'}];
    for k=1:length(RC)
        if ~isfield(A,RC{k}), A.(RC{k})=A_Default{k}; end
        set(A_In(k),'String',num2str(A.(RC{k})));
    end
    if length(A.DELTAL)>1           %array of left deflections
        del = A.DELTAL;
        ddel = del(2:end)-del(1:end-1);
        if ~sum(ddel-ddel(1))       %uniform spacing
            del1 = num2str(del(1));
            ddel = num2str(ddel(1));
            del2 = num2str(del(end));
            set(A_In(end-1),'String',[del1,':',ddel,':',del2]);
        end
    end
    if length(A.DELTAR)>1           %array of right deflections
        del = A.DELTAR;
        ddel = del(2:end)-del(1:end-1);
        if ~sum(ddel-ddel(1))       %uniform spacing
            del1 = num2str(del(1));
            ddel = num2str(ddel(1));
            del2 = num2str(del(end));
            set(A_In(end),'String',[del1,':',ddel,':',del2]);
        end
    end
    
    %Initialize Body Parameters
    if ~any(setdiff(BD.R,2)) && plt_bd
        BD.R=sqrt(BD.S/pi); BD.ZU=BD.R; BD.ZL=-BD.ZU; %defined by S
    elseif ~any(setdiff(BD.ZU,2)) && plt_bd
        BD.ZU=BD.R; BD.ZL=-BD.ZU; BD.S=pi*BD.S.^2; %defined by R
    end
    if BD.NX>11
        XP = linspace(BD.X(1),BD.X(end),11);
        N = interp1(BD.X,1:BD.NX,XP,'nearest','extrap');
        if length(unique(N))<BD.NX, N = [1:10,BD.NX]; end
    else
        N = 1:BD.NX;
    end
    for i=1:min([BD.NX,11])
        set(BD_In(1,i),'String',num2str(N(i)))
        set(BD_In(2,i),'String',num2str(round(BD.X(N(i)),2)))
        %set(BD_In(3,i),'String',num2str(round(BD.P(N(i)),1)))
        set(BD_In(3,i),'String','1')
    end
    set(BD_In(1:3,i+1:7),'String',''), BD.N = N;
    
    %Initialize Aero Parameters
    RA={'ALSCHD','ALT','MACH','WT','XCG','ZCG','XI','YI'};
    for k=1:length(RA)
        if ~isfield(AERO,RA{k}), AERO.(RA{k})=AERO_Default{k}; end
        set(AERO_In(k),'String',num2str(AERO.(RA{k})))
    end
    if AERO.NALPHA>1            %array of alphas
        aoa = AERO.ALSCHD;
        da = aoa(2:end)-aoa(1:end-1);
        if ~sum(da-da(1))       %uniform spacing
            a1 = num2str(aoa(1));
            da = num2str(da(1));
            a2 = num2str(aoa(end));
            set(AERO_In(1),'String',[a1,':',da,':',a2]);
        end
    end
    if length(AERO.NALT)>1              %array of altitudes
        alt = AERO.ALT;
        da = alt(2:end)-alt(1:end-1);
        if ~sum(da-da(1))       %uniform spacing
            a1 = num2str(alt(1));
            da = num2str(da(1));
            a2 = num2str(alt(end));
            set(AERO_In(2),'String',[a1,':',da,':',a2]);
        end
    end
    if length(AERO.MACH)>1             %array of machs
        ma = AERO.MACH;
        da = ma(2:end)-ma(1:end-1);
        if ~sum(da-da(1))       %uniform spacing
            a1 = num2str(ma(1));
            da = num2str(da(1));
            a2 = num2str(ma(end));
            set(AERO_In(3),'String',[a1,':',da,':',a2]);
        end
    end
    set(AERO_In(end),'Value',AERO.XCG,'Min',BD.X(1),'Max',BD.X(end))
    
    %Load Weight/Balance Data if Available
    data = get(opt(1),'UserData');
    if isfield(WG,'XCG')
        data(:,1) = {num2str(WG.XCG); num2str(WG.ZCG); num2str(WG.WT)};
    end
    if isfield(HT,'XCG')
        data(:,2) = {num2str(HT.XCG); num2str(HT.ZCG); num2str(HT.WT)};
    end
    if isfield(VT,'XCG')
        data(:,3) = {num2str(VT.XCG); num2str(VT.ZCG); num2str(VT.WT)};
    end
    if isfield(BD,'XCG')
        data(:,4) = {num2str(BD.XCG); num2str(BD.ZCG); num2str(BD.WT)};
    end
    set(opt(1),'UserData',data)
    
    %Only Plot Loaded Components
    plot_cmp = [plt_wg,plt_ht,plt_vt,plt_bd];
    for i=1:length(plot_cmp), Viz(plot_cmp(i),0,i), end
    
end

%Parts fid (Pseudo DATCOM Input fid for Added Geometry)
if ~isempty(Pfid)
    
    %Refresh GUI to Add Tabs
    re_initialize = 1;
    
    %Categorize Variables
    fid = Pfid;
    Text=''; while ~feof(fid), Text=strcat(Text,fgetl(fid)); end
    Index=[1,strfind(Text,'='),length(Text)];
    Elem=Text(Index(1):Index(2)-1);
    Fix_1=strfind(Elem,'(1)');   Elem(Fix_1:Fix_1+2)=[];
    Commas=0; Spaces=strfind(Elem,' '); Money=0;
    Comp=zeros(1,length(Index)); Stay=[0 0 0 0 0 0];
    
    for k=1:length(Index)-1
        %Read Previous Variable Name
        Start=max([Commas(end),Spaces(end),Money(end)])+1;
        Name=Elem(Start:end); Name_Fix=strfind(Name,'(');
        if Name_Fix, Name(Name_Fix:end)=[]; end
        
        %Move to the Next Value
        Elem=Text(Index(k):Index(k+1)-1);
        Fix_1=strfind(Elem,'(1)');   Elem(Fix_1:Fix_1+2)=[];
        
        %Distinguish Components
        if ~isempty(strfind(Elem,'BD2')),   Comp(k+1)=1;end
        if ~isempty(strfind(Elem,'BD3')),   Comp(k+1)=2;end
        if ~isempty(strfind(Elem,'WG2')),   Comp(k+1)=3;end
        if ~isempty(strfind(Elem,'HT2')),   Comp(k+1)=4;end
        if ~isempty(strfind(Elem,'VT2')),   Comp(k+1)=5;end
        if ~isempty(strfind(Elem,'PROP')),  Comp(k+1)=6;end
        
        %Find Indices
        Commas=[0,strfind(Elem,',')];
        Spaces=[0,strfind(Elem,' ')];
        Money=[0,strfind(Elem,'$')];
        
        %Categorize Results
        I=[Commas,length(Elem)];
        if length(Money)>1, I(end)=Money(2); end
        if length(Commas)>3 %If Containing Multiple Values
            I=[1,I(2:end)]; Value = zeros(1,length(I)-1);
            for j=1:length(I)-1
                Value(j)=str2double(Elem(I(j)+1:I(j+1)-1));
            end
        else %Just One Value
            Value=str2double(Elem(2:I(2)-1));
        end
        Value(isnan(Value))=[]; %Remove any NaNs
        
        %Assign to Respective Component
        if Comp(k)==6 || (Stay(6) && Comp(k)==0)
            NP{4}.(Name)=Value; Stay=[0 0 0 0 0 1];
        elseif Comp(k)==5 || (Stay(5) && Comp(k)==0)
            NP{3}.(Name)=Value; Stay=[0 0 0 0 1 0];
        elseif Comp(k)==4 || (Stay(4) && Comp(k)==0)
            NP{2}.(Name)=Value; Stay=[0 0 0 1 0 0];
        elseif Comp(k)==3 || (Stay(3) && Comp(k)==0)
            NP{1}.(Name)=Value; Stay=[0 0 1 0 0 0];
        elseif Comp(k)==2 || (Stay(2) && Comp(k)==0)
            NB{2}.(Name)=Value; Stay=[0 1 0 0 0 0];
        elseif Comp(k)==1 || (Stay(1) && Comp(k)==0)
            NB{1}.(Name)=Value; Stay=[1 0 0 0 0 0];
        else
            %Assign Uncategorized Values
            if ~isempty(Value)
                eval(sprintf('AERO.%s=str2num(''%s'');',...
                    Name,num2str(Value)))
            end
        end
    end
    fclose(fid);
    
    %Body Fix (if only second body written to file)
    if isempty(NB{1}) && ~isempty(NB{2})
        NB{1}=NB{2};    NB{2}=[];
    end
    
    %Airfoil Data
    for n=1:length(NP)
        if ~isempty(NP{n})
            if isfield(NP{n},'XCORD')
                NP{n}.NACA = {'Data.'};
                NP{n}.DATA{1}(:,1)=[fliplr(NP{n}.XCORD),NP{n}.XCORD]';
                NP{n}.DATA{1}(:,2)=[fliplr(NP{n}.YUPPER),NP{n}.YLOWER]';
                NP{n}.TC = max(NP{n}.DATA{1}(:,2))-min(NP{n}.DATA{1}(:,2));
            elseif isfield(NP{n},'NACA')
                NP{n}.DATA = {NACA_Panel_Maker(100,NP{n}.NACA{1})};
            else
                NP{n}.NACA = {'0012'};
                NP{n}.DATA = {NACA_Panel_Maker(100,NP{n}.NACA{1})};
            end
            choice{n+3} = NP{n}.DATA{1};
        end
    end
    
    %Load Weight/Balance Data if Available
    data = get(opt(1),'UserData');
    for n=1:4
        if isfield(NP{n},'XCG')
            data{1,n+4} = num2str(NP{n}.XCG);
            data{2,n+4} = num2str(NP{n}.ZCG);
            data{3,n+4} = num2str(NP{n}.WT);
        end
    end
    for n=1:2
        if isfield(NB{n},'XCG')
            data{1,n+8} = num2str(NB{n}.XCG);
            data{2,n+8} = num2str(NB{n}.ZCG);
            data{3,n+8} = num2str(NB{n}.WT);
        end
    end
    set(opt(1),'UserData',data)
    
end

%Refresh GUI or Update Plot
if re_initialize
    Initialize_GUI
else
    if ~isempty(choice)
        AID(0,0,'update',choice)
    else
        AID(0,0,'update') %variables get lost here
    end
end


end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%% WRITE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function Write_DATCOM(CaseID,type,choice,cg_calc,unit)
global WG HT VT BD F A E NP NP_In NB NB_In AERO opt cmp

%Write DATCOM Input fid
if strcmp(type,'case')
    
    %Parameters
    RP={'CHRDR','CHRDBP','CHRDTP','SSPN','SSPNE','SSPNOP','SAVSI',...
        'SAVSO','CHSTAT','DHDADI','DHDADO','TC','TWISTA','X','Y','Z'};
    RF={'SPANFI','SPANFO','CHRDFI','CHRDFO'};
    RC=[RF,{'STYPE'}];
    RF=[RF,{'FTYPE','PHETE','PHETEP','TC','CB'}];
    
    %Correct VT Positions
    %Y=VT.Z; VT.Z=VT.Y; VT.Y=Y;
    
    %Check if Just Running Wing
    if max(abs([F.DELTA,A.DELTAL])) && strcmp(choice,'DATCOM')
        owg = questdlg('Run wing-only case to evaluate flaps/ailerons?');
    else
        owg = 'no thanks, I would not like to run a wing-only case';
    end
    
    %Check if Saving CG Parameters
    cg_data = get(opt(1),'UserData'); cg_check = 0;
    for i=1:length(cg_data), cg_check = cg_check + eval(cg_data{3,i}); end
    if cg_check
        if strcmp(choice,'DATCOM')
            prompt = ['CG data will not '...
                'be written to DATCOM input file. Continue anyway?'];
            go = questdlg(prompt,'Run DATCOM');
            if ~strcmp(go,'Yes'), return, end
        else
            cg_write = questdlg('Write Weight/Balance data?');
            if strcmp(cg_write,'Yes')
                cg_calc=1;
                RP = [{'XCG','ZCG','WT'},RP];
                if ~isfield(WG,'XCG')
                    k=1;                        WG.WT=eval(cg_data{3,k});
                    WG.XCG=eval(cg_data{1,k});  WG.ZCG=eval(cg_data{2,k});
                end
                if ~isfield(HT,'XCG')
                    k=2;                        HT.WT=eval(cg_data{1,k});
                    HT.XCG=eval(cg_data{1,k});  HT.ZCG=eval(cg_data{1,k});
                end
                if ~isfield(VT,'XCG')
                    k=3;                        VT.WT=eval(cg_data{3,k});
                    VT.XCG=eval(cg_data{1,k});  VT.ZCG=eval(cg_data{2,k});
                end
                if ~isfield(BD,'XCG')
                    k=4;                        BD.WT=eval(cg_data{3,k});
                    BD.XCG=eval(cg_data{1,k});  BD.ZCG=eval(cg_data{2,k});
                end
            else
                cg_calc=0;
            end
        end
    end
    
    %Fix SSPNOP (DATCOM takes the break span from the tip)
    if WG.SSPNOP, WG.SSPNOP =  WG.SSPN-WG.SSPNOP; end
    if HT.SSPNOP, HT.SSPNOP =  HT.SSPN-HT.SSPNOP; end
    if VT.SSPNOP, VT.SSPNOP =  VT.SSPN-VT.SSPNOP; end
    
    %Name fid
    if isempty(strfind(CaseID,'.dat'))
        fid=fopen([CaseID,'.dat'],'w');
    else
        fid=fopen(CaseID,'w');
    end
    if strcmp(unit,'in')
        fprintf(fid,'DIM %s\n',upper(unit));
    end
    fprintf(fid,'CASEID %s\n',CaseID);
    
    %Write Flight Conditions (FLTCON)
    fprintf(fid,' $FLTCON NALPHA=%.1f,',length(AERO.ALSCHD));
    fprintf(fid,'ALSCHD=');
    if length(AERO.ALSCHD)>10
        fprintf(fid,'%.1f,',AERO.ALSCHD(1:10));    fprintf(fid,'\n  ');
        fprintf(fid,'%.1f,',AERO.ALSCHD(11:end));
    else
        fprintf(fid,'%.1f,',AERO.ALSCHD);
    end
    fprintf(fid,'\n  NALT=%.1f,',length(AERO.ALT));
    fprintf(fid,'ALT=');       fprintf(fid,'%.1f,',AERO.ALT);
    fprintf(fid,'\n  NMACH=%.1f,',length(AERO.MACH));
    fprintf(fid,'MACH=');      fprintf(fid,'%.3f,',AERO.MACH);
    fprintf(fid,'\n  WT=%.2f,LOOP=2.0$',AERO.WT);
    
    %Write Reference Values (OPTINS)
    fprintf(fid,'\n $OPTINS SREF=%.2f,CBARR=%.2f,BLREF=%0.2f$',...
        WG.S(end),WG.cbar(end),WG.b);
    
    %Write Synthesis Parameters (SYNTHS)
    if strcmp(choice,'DATCOM') %DATCOM can't read YW and YH
        fprintf(fid,'\n $SYNTHS XCG=%.2f,ZCG=%0.2f,XW=%0.2f,ZW=%0.2f,',...
            AERO.XCG,AERO.ZCG,WG.X,WG.Z);
        fprintf(fid,'ALIW=%.2f,\n  XH=%0.2f,ZH=%0.2f,',WG.i,HT.X,HT.Z);
        fprintf(fid,'ALIH=%0.2f,XV=%0.2f,YV=%0.2f,ZV=%0.2f,VERTUP=.TRUE.$',...
            HT.i,VT.X,VT.Y,VT.Z);
    else
        fprintf(fid,'\n $SYNTHS XCG=%.2f,ZCG=%0.2f,XW=%0.2f,YW=%0.2f,ZW=%0.2f,',...
            AERO.XCG,AERO.ZCG,WG.X,WG.Y,WG.Z);
        fprintf(fid,'ALIW=%.2f,\n  XH=%0.2f,YH=%0.2f,ZH=%0.2f,',...
            WG.i,HT.X,HT.Y,HT.Z);
        fprintf(fid,'ALIH=%0.2f,XV=%0.2f,YV=%0.2f,ZV=%0.2f,VERTUP=.TRUE.$',...
            HT.i,VT.X,VT.Y,VT.Z);
    end
    
    %Save Body Parameters (BODY)
    if get(cmp(4),'Value')
        lim = 12;
        fprintf(fid,'\n $BODY NX=%.1f,ITYPE=1.0,',BD.NX);
        if cg_calc, fprintf(fid,'\n  XCG=%.2f,ZCG=%.2f,WT=%.2f,',...
                BD.XCG,BD.ZCG,BD.WT); end
        if min(BD.S)<0.01, precision='%.3f,'; else, precision = '%.2f,';end
        if BD.NX<=lim
            fprintf(fid,'\n  X=');  fprintf(fid,'%.2f,',BD.X);
            fprintf(fid,'\n  ZU='); fprintf(fid,'%.2f,',BD.ZU);
            fprintf(fid,'\n  ZL='); fprintf(fid,'%.2f,',BD.ZL);
            fprintf(fid,'\n  R=');  fprintf(fid,'%.2f,',BD.R);
            fprintf(fid,'\n  P=');  fprintf(fid,'%.2f,',BD.P);
            fprintf(fid,'\n  S=');  fprintf(fid,precision,BD.S);
        else %trim to 80 characters
            fprintf(fid,'\n  X=');  fprintf(fid,'%.2f,',BD.X(1:lim));
            fprintf(fid,'\n  ');    fprintf(fid,'%.2f,',BD.X(lim+1:end));
            fprintf(fid,'\n  ZU='); fprintf(fid,'%.2f,',BD.ZU(1:lim));
            fprintf(fid,'\n  ');    fprintf(fid,'%.2f,',BD.ZU(lim+1:end));
            fprintf(fid,'\n  ZL='); fprintf(fid,'%.2f,',BD.ZL(1:lim));
            fprintf(fid,'\n  ');    fprintf(fid,'%.2f,',BD.ZL(lim+1:end));
            fprintf(fid,'\n  R=');  fprintf(fid,'%.2f,',BD.R(1:lim));
            fprintf(fid,'\n  ');    fprintf(fid,'%.2f,',BD.R(lim+1:end));
            fprintf(fid,'\n  P=');  fprintf(fid,'%.2f,',BD.P(1:lim));
            fprintf(fid,'\n  ');    fprintf(fid,'%.2f,',BD.P(lim+1:end));
            fprintf(fid,'\n  S=');  fprintf(fid,precision,BD.S(1:lim));
            fprintf(fid,'\n  ');    fprintf(fid,precision,BD.S(lim+1:end));
        end
    end
    fprintf(fid,'$\n');
    
    %Save Planform Parameters (WGPLNF/HTPLNF/VTPLNF)
    
    %Wing Planform Data
    if length(WG.NACA{1})==6
        airfoil = str2double(WG.NACA{1}([1:2,4:6]));
    else
        airfoil = str2double(WG.NACA{1});
    end
    if isnan(airfoil) && isfield(WG,'DATA')
        fprintf(fid,' $WGPLNF ');
    else
        if isnan(airfoil), WG.NACA{1}='2412'; end
        fprintf(fid,'NACA-W-%d-%s\n $WGPLNF ',length(WG.NACA{1}),WG.NACA{1});
    end
    for i=1:length(RP)-5
        fprintf(fid,'%s=%.2f,',RP{i},WG.(RP{i}));
        if mod(i,4)==0, fprintf(fid,'\n  '); end
    end
    fprintf(fid,'TYPE=1.0$\n');
    
    %Wing airfoil Data
    if isnan(airfoil)
        for n=1:length(WG.DATA)
            fprintf(fid,' $WGSCHR NPTS=%d,\n  XCORD=',floor(length(WG.DATA{n}/2)));
            XCORD = flipud(WG.DATA{n}(1:floor(end/2),1));
            for i=1:length(XCORD)
                fprintf(fid,'%.3f,',XCORD(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            YUPPER = flipud(WG.DATA{n}(1:floor(end/2),2));
            fprintf(fid,'\n  YUPPER=');
            for i=1:length(YUPPER)
                fprintf(fid,'%.3f,',YUPPER(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            YLOWER = WG.DATA{n}(end-floor(end/2)+1:end,2);
            fprintf(fid,'\n  YLOWER=');
            for i=1:length(YLOWER)
                fprintf(fid,'%.3f,',YLOWER(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            fprintf(fid,'CLMAX=1.5$\n');
        end
    end
    
    %Horizontal Tail Planform Data
    if get(cmp(2),'Value') && ~strcmp(owg,'Yes')
        if length(HT.NACA{1})==6
            airfoil = str2double(HT.NACA{1}([1:2,4:6]));
        else
            airfoil = str2double(HT.NACA{1});
        end
        if isnan(airfoil) && isfield(HT,'DATA')
            fprintf(fid,' $HTPLNF ');
        else
            if isnan(airfoil), WG.NACA{1}='2412'; end
            fprintf(fid,'NACA-H-%d-%s\n $HTPLNF ',length(HT.NACA{1}),HT.NACA{1});
        end
        for i=1:length(RP)-5
            fprintf(fid,'%s=%.2f,',RP{i},HT.(RP{i}));
            if mod(i,4)==0, fprintf(fid,'\n  '); end
        end
        fprintf(fid,'TYPE=1.0$\n');
        
        %Horizontal Tail airfoil Data
        if isnan(airfoil) && isfield(HT,'DATA')
            fprintf(fid,' $HTSCHR NPTS=%d,\n  XCORD=',floor(length(HT.DATA/2)));
            XCORD = flipud(HT.DATA(1:floor(end/2),1));
            for i=1:length(XCORD)
                fprintf(fid,'%.3f,',XCORD(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            YUPPER = flipud(HT.DATA(1:floor(end/2),2));
            fprintf(fid,'\n  YUPPER=');
            for i=1:length(YUPPER)
                fprintf(fid,'%.3f,',YUPPER(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            YLOWER = HT.DATA(end-floor(end/2)+1:end,2);
            fprintf(fid,'\n  YLOWER=');
            for i=1:length(YLOWER)
                fprintf(fid,'%.3f,',YLOWER(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            fprintf(fid,'CLMAX=1.5$\n');
        end
    end
    
    %Vertical Tail Planform Data
    if get(cmp(3),'Value') && ~strcmp(owg,'Yes')
        if length(VT.NACA{1})==6
            airfoil = str2double(VT.NACA{1}([1:2,4:6]));
        else
            airfoil = str2double(VT.NACA{1});
        end
        if isnan(airfoil) && isfield(VT,'DATA')
            fprintf(fid,' $VTPLNF ');
        else
            if isnan(airfoil), VT.NACA{1}='0012'; end
            fprintf(fid,'NACA-V-%d-%s\n $VTPLNF ',length(VT.NACA{1}),VT.NACA{1});
        end
        for i=1:length(RP)-5
            fprintf(fid,'%s=%.2f,',RP{i},VT.(RP{i}));
            if mod(i,4)==0, fprintf(fid,'\n  '); end
        end
        fprintf(fid,'TYPE=1.0$\n');
        
        %Vertical Tail airfoil Data
        if isnan(airfoil) && isfield(VT,'DATA')
            fprintf(fid,' $VTSCHR NPTS=%d,\n  XCORD=',floor(length(VT.DATA/2)));
            XCORD = flipud(VT.DATA(1:floor(end/2),1));
            for i=1:length(XCORD)
                fprintf(fid,'%.3f,',XCORD(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            YUPPER = flipud(VT.DATA(1:floor(end/2),2));
            fprintf(fid,'\n  YUPPER=');
            for i=1:length(YUPPER)
                fprintf(fid,'%.3f,',YUPPER(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            YLOWER = VT.DATA(end-floor(end/2)+1:end,2);
            fprintf(fid,'\n  YLOWER=');
            for i=1:length(YLOWER)
                fprintf(fid,'%.3f,',YLOWER(i));
                if mod(i,10)==0, fprintf(fid,'\n  '); end
            end
            fprintf(fid,'CLMAX=1.5$\n');
        end
    end
    
    %Write Flap Parameters (SYMFLP)
    fprintf(fid,' $SYMFLP ');
    for i=1:length(RF)
        fprintf(fid,'%s=%.3f,',RF{i},F.(RF{i}));
        if i==4 && length(RF)>i, fprintf(fid,'\n  '); end
    end
    fprintf(fid,'\n  NDELTA=%0.1f,',length(F.DELTA));
    if length(F.DELTA)>10, warndlg('Limit to 10 flap deflections'), end
    fprintf(fid,'DELTA=');     fprintf(fid,'%.1f,',F.DELTA);
    fprintf(fid,'$\n');
    
    %If Considering Full Aircraft
    if ~strcmp(owg,'Yes')
        
        %Write Aileron Parameters (ASYFLP)
        fprintf(fid,' $ASYFLP ');
        for i=1:length(RC)
            fprintf(fid,'%s=%.3f,',RC{i},A.(RC{i}));
            if i==4 && length(RC)>i, fprintf(fid,'\n  '); end
        end
        fprintf(fid,'NDELTA=%0.1f,',length(A.DELTAL));
        if length(A.DELTAL)>10,warndlg('Limit to 10 deflection angles'),end
        fprintf(fid,'\n  DELTAL=');    fprintf(fid,'%.1f,',A.DELTAL);
        fprintf(fid,'\n  DELTAR=');    fprintf(fid,'%.1f,',A.DELTAR);
        fprintf(fid,'$\n');
        
        %Write Elevator Parameters (SYMFLP)
        fprintf(fid,' $SYMFLP ');
        for i=1:length(RF)
            fprintf(fid,'%s=%.3f,',RF{i},E.(RF{i}));
            if i==4 && length(RF)>i, fprintf(fid,'\n  '); end
        end
        fprintf(fid,'\n  NDELTA=%0.1f,',length(E.DELTA));
        if length(E.DELTA)>10, warndlg('Limit to 10 deflection angles'),end
        fprintf(fid,'DELTA=');     fprintf(fid,'%.1f,',E.DELTA);
        fprintf(fid,'$\n');
    end
    
    %Finish and Close
    fprintf(fid,'PLOT\nNEXT CASE');
    fclose(fid);
    
elseif strcmp(type,'parts')
    
    %Parameters
    RP={'CHRDR','CHRDBP','CHRDTP','SSPN','SSPNE','SSPNOP','SAVSI',...
        'SAVSO','CHSTAT','DHDADI','DHDADO','TWISTA','TC','X','Y','Z'};
    
    %Correct VT Positions
    %if ~isempty(NP{3}), Y=NP{3}.Z; NP{3}.Z=NP{3}.Y; NP{3}.Y=Y; end
    %if ~isempty(NP{4}), Y=NP{4}.Z; NP{4}.Z=NP{4}.Y; NP{4}.Y=Y; end
    
    %Check if Saving CG Parameters
    if choice
        data = get(opt(1),'UserData');
        RP = [{'XCG','ZCG','WT'},RP];
        for n=1:4
            if ~isempty(NP_In{n}) && ~isfield(NP{n},'XCG')
                NP{n}.XCG=eval(data{1,n+4}); NP{n}.ZCG=eval(data{1,n+4});
                NP{n}.WT=eval(data{1,n+4});
            end
        end
        for n=1:2
            if ~isempty(NB_In{n}) && ~isfield(NB{n},'XCG')
                NB{n}.XCG=eval(data{1,n+8}); NB{n}.ZCG=eval(data{1,n+8});
                NB{n}.WT=eval(data{1,n+8});
            end
        end
    end
    
    %Name fid
    if isempty(CaseID), CaseID='My First Plane'; end
    %ID2=char(inputdlg('Name Added Parts fid','Parts ID',1,{[CaseID,' Parts']}));
    %if isempty(ID2), return; end
    ID2 = [CaseID,' Parts']; 
    fid=fopen([ID2,'.dat'],'wt');
    fprintf(fid,'PARTSID %s\n',ID2);
    
    %Write Body Parameters (BODY)
    for i=1:length(NB)
        if ~isempty(NB_In{i}) && get(cmp(8+i),'Value')
            fprintf(fid,'\n $BD%d NX=%.1f,ITYPE=1.0,',i+1,NB{i}.NX);
            if choice, fprintf(fid,'\n  XCG=%.2f,ZCG=%.2f,WT=%.2f,',...
                    NB{i}.XCG,NB{i}.ZCG,NB{i}.WT); end
            fprintf(fid,'X0=%.2f,Y0=%.2f,Z0=%.2f,',...
                NB{i}.X0,NB{i}.Y0,NB{i}.Z0);
            fprintf(fid,'\n  X=');  fprintf(fid,'%.2f,',NB{i}.X);
            fprintf(fid,'\n  ZU='); fprintf(fid,'%.2f,',NB{i}.ZU);
            fprintf(fid,'\n  ZL='); fprintf(fid,'%.2f,',NB{i}.ZL);
            fprintf(fid,'\n  R=');  fprintf(fid,'%.2f,',NB{i}.R);
            fprintf(fid,'\n  P=');  fprintf(fid,'%.2f,',NB{i}.P);
            fprintf(fid,'\n  S=');  fprintf(fid,'%.2f,',NB{i}.S);
            fprintf(fid,'$\n');
        end
    end
    
    %Save Planform Parameters (Wing 2/HTail 2/VTail 2/Propeller)
    plnf = {'WG2','HT2','VT2','PROP'};
    for j=1:length(NP)
        if ~isempty(NP_In{j}) && get(cmp(4+j),'Value')
            fprintf(fid,'\n $%s ',plnf{j});
            for i=1:length(RP)
                fprintf(fid,'%s=%.2f,',RP{i},NP{j}.(RP{i}));
                if ~mod(i,4), fprintf(fid,'\n  '); end
            end
            fprintf(fid,'TYPE=1.0$\n');
            if isfield(NP{j},'DATA')
                fprintf(fid,' $%sSCHR NPTS=%d,\n  XCORD=',plnf{j},floor(length(NP{j}.DATA{1}/2)));
                XCORD = flipud(NP{j}.DATA{1}(1:floor(end/2),1));
                for i=1:length(XCORD)
                    fprintf(fid,'%.3f,',XCORD(i));
                    if mod(i,10)==0, fprintf(fid,'\n  '); end
                end
                YUPPER = flipud(NP{j}.DATA{1}(1:floor(end/2),2));
                fprintf(fid,'\n  YUPPER=');
                for i=1:length(YUPPER)
                    fprintf(fid,'%.3f,',YUPPER(i));
                    if mod(i,10)==0, fprintf(fid,'\n  '); end
                end
                YLOWER = NP{j}.DATA{1}(end-floor(end/2)+1:end,2);
                fprintf(fid,'\n  YLOWER=');
                for i=1:length(YLOWER)
                    fprintf(fid,'%.3f,',YLOWER(i));
                    if mod(i,10)==0, fprintf(fid,'\n  '); end
                end
                fprintf(fid,'CLMAX=1.5$\n');
            end
        end
    end
    
    %Finish and Close
    fprintf(fid,'PLOT\nNEXT CASE');
    fclose(fid);
    
    %Update
    AID(0,0,'update')
    
end
end
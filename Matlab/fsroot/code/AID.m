function AID(handle,~,action,choice)
%%%%%%%%%%%%%%%%%%  Aircraft Intuitive Design Tool  %%%%%%%%%%%%%%%%%%%%%%%
%                                                                         %
%                          Zachary T. Lietzau                             %
%           Embry-Riddle Aeronautical University Class of 2017            %
%     Contact me with questions/suggestions at: zaklietzau@gmail.com      %
%                                                                         %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

global ax cmp WG_In WG HT_In HT VT_In VT BD_In BD AERO_In AERO AERO_Out ...
    AC ATM F_In F A_In A E_In E R_In R NP_In NP NB_In NB Results opt tabs
%global ACOUT %experimental implementation of the ASCDM code (line 1550)
global lib_path %path to dependencies for app implementation (line 52)

%=====================================
%               TO DO:
%    (Anticipated Difficulty 1-3)
%-------------------------------------
%   -(1) More Unit Conversions
%   -(1) Propeller Stability
%     -- (Aero.m - line 501)
%   -(1) Nacelle Stability
%     -- (call Body Stability.m)
%   -(1) Inertia Inputs/Calculations
%     -- (Initialize_GUI.m - 262/643)
%   -(1) Dynamic Stability Matrices
%   -(1) Handling Qualities (1-6)
%   -(1) Propulsion Inputs
%   -(1) Link Simulink 6-DOF Model
%   -(2) Aileron Control Strip Method
%   -(2) Plot Full Datcom for013.dat
%   -(3) CAD/CFD Geometry/Mesh Export
%   -(4) Neural Network 3view Import
%=====================================

%Options
if nargin>=1 && ~strcmp(action,'initialize')
    
    %Path to App Dependencies
    %lib_path = which(fullfile('code','AID_ReadMe.txt'));
    lib_path = which(fullfile('code','AID.m'));
    lib_path = lib_path(1:end-6);
    %lib_path = %directory containing source code and supporting folders
    
    %CG
    cg_calc = strcmp(get(opt(1),'Checked'),'on');       %estimate CG
    
    %Plot Options
    transparent = strcmp(get(opt(2),'Checked'),'on');   %toggle transparent
    res = get(opt(4),'UserData');                       %resolution of plot
    shade = strcmp(get(opt(5),'Checked'),'on');         %shaded/wireframe
    angl = ~strcmp(get(opt(6),'Checked'),'on');         %shrink angled wing
    ac_color = get(opt(7),'UserData');                  %aircraft color
    
    %Calculations
    trim = get(opt(8),'UserData');                      %trim incidence/aoa
    trim_mode = trim(1); delta_max = trim(2);         	%max deflection
    downwash = strcmp(get(opt(9),'Checked'),'on');      %estimate downwash
    if ~downwash, dw = get(opt(9),'UserData'); end      %input dwash effect
    body_method = strcmp(get(opt(10),'Checked'),'on');  %Multhopp/G+W
    
    %I/O Options
    check_io = strcmp(get(opt(11),'Checked'),'on');     %check input/output
    %plotdat = strcmp(get(opt(12),'Checked'),'on');     %plot DATCOM output
    %loadvar = strcmp(get(opt(13),'Checked'),'on');     %load DD variables
    
    %General
    inch = strcmp(get(opt(14),'Checked'),'on');         %inches
    if inch, unit = 'in'; else, unit = 'ft'; end        %or feet
    if inch, kts = 0; else, kts = 1; end
    %kts = strcmp(get(opt(17),'Checked'),'on');         %knots
    check_error = strcmp(get(opt(15),'Checked'),'on');  %toggle error check
    lim = get(opt(15),'UserData');                      %error limits
    
end

%Initialize GUI
if nargin<1
    clc
    clear -global
    close all
    AID(0,0,'initialize',24)
    
elseif strcmp(action,'initialize')%%%%%%%%% INITIALIZE %%%%%%%%%%%%%%%%%%%%
    
    %Initialize GUI
    Initialize_GUI(choice)
    
    %Initialize Plot
    AID(0,0,'update','init')
    
elseif strcmp(action,'make')%%%%%%%%%%%%%%%%% MAKE %%%%%%%%%%%%%%%%%%%%%%%%
    
    %Save Check
    %     CaseID = get(gcf,'Tag');
    %     if isempty(CaseID)
    %         sv=questdlg('Save current design?','Save','Yes','No','Yes');
    %         if strcmp(sv,'Yes'), AID(0,0,'save',''), end
    %         if ~strcmp(sv,'No'), choice = ''; end
    %     end
    
    %Delete Added Geometry
    tab_list = get(tabs,'Children');
    add_part = get(tab_list(7),'Children');
    set(findall(gcf,'Style','checkbox'),'Value',1)
    AID('Geometry',0,'change_ax')
    
    %Choose to Design a New Aircraft or Update Existing
    switch choice
        case 'New'
            
            %Scale
            L=inputdlg(['Fuselage Length, ',unit],'Body',1,{'24'});
            if ~isempty(L)
                L=eval(L{1});
                NP_In=cell(1,4);    NP=NP_In;
                NB_In=cell(1,2);    NB=NB_In;
                for i=8:length(tab_list), delete(tab_list(i)), end
                set(add_part,'Visible','on')
                set(tabs,'SelectedTab',tab_list(1))
                delete(findall(ax{1},'Type','surface'))
                delete(findall(ax{1},'Type','line'))
                ax{2} = cell(1,11);
                clearvars -except unit L
                AID(0,0,'initialize',L), return
            end
            
        case {'Load','Models'} %MATLAB Sve File
            
            if strcmp(choice,'Load')
                pname = '';
            else
                pname = fullfile(lib_path,'Models');
            end
            
            %Retrieve MATLAB Save File
            clearvars WG HT VT AERO F A E AC, Results = cell(1,4);
            [Fn,P]=uigetfile({'*.mat;*.dat;*.txt','All Input Types';...
                '*.mat','MATLAB Save Files';'*.dat','DATCOM for005'},...
                'Choose Save/Input File',pname,'MultiSelect','on');
            if isempty(Fn) || isnumeric(Fn), return, end
            if iscell(Fn) && sum(~cellfun(@isempty,strfind(Fn,'.mat')))
                warndlg(['Loading only first selected file, ',Fn{1}])
                Fn = Fn{1};
            elseif iscell(Fn) || isempty(strfind(Fn,'.mat'))
                DATCOM_IO(Fn,P), return
            end
            NP_In=cell(1,4);    NP=NP_In;
            NB_In=cell(1,2);    NB=NB_In;
            for i=8:length(tab_list), delete(tab_list(i)), end
            set(add_part,'Visible','on')
            set(tabs,'SelectedTab',tab_list(1))
            delete(findall(ax{1},'Type','surface'))
            delete(findall(ax{1},'Type','line'))
            ax{2} = cell(1,11);
            load([P,Fn]); CaseID = Fn(1:end-4); set(gcf,'Tag',CaseID)
            
            %Initialize Planform Parameters
            RP={'CHRDR','CHRDBP','CHRDTP','SSPN','SSPNOP',...
                'SAVSI','SAVSO','CHSTAT','DHDADI','DHDADO',...
                'TC','TWISTA','i','X','Y','Z'};
            for k=1:length(RP)
                set(WG_In(k),'String',num2str(WG.(RP{k})));
                set(HT_In(k),'String',num2str(HT.(RP{k})));
                set(VT_In(k),'String',num2str(VT.(RP{k})));
            end
            
            %Initialize Control Surface Parameters
            RF={'SPANFI','SPANFO','CHRDFI','CHRDFO','DELTA'};
            for k=1:length(RF)
                set(F_In(k),'String',num2str(F.(RF{k})));
                set(E_In(k),'String',num2str(E.(RF{k})));
                set(R_In(k),'String',num2str(R.(RF{k})));
            end
            if length(F.DELTA)>1            %array of deflections
                del = F.DELTA; ddel = del(2:end)-del(1:end-1);
                if ~sum(ddel-ddel(1))       %uniform spacing
                    del1 = num2str(del(1));
                    ddel = num2str(ddel(1));
                    del2 = num2str(del(end));
                    set(F_In(end),'String',[del1,':',ddel,':',del2]);
                end
            end
            if length(E.DELTA)>1            %array of deflections
                del = E.DELTA; ddel = del(2:end)-del(1:end-1);
                if ~sum(ddel-ddel(1))       %uniform spacing
                    del1 = num2str(del(1));
                    ddel = num2str(ddel(1));
                    del2 = num2str(del(end));
                    set(E_In(end),'String',[del1,':',ddel,':',del2]);
                end
            end
            if length(R.DELTA)>1            %array of deflections
                del = R.DELTA; ddel = del(2:end)-del(1:end-1);
                if ~sum(ddel-ddel(1))       %uniform spacing
                    del1 = num2str(del(1));
                    ddel = num2str(ddel(1));
                    del2 = num2str(del(end));
                    set(R_In(end),'String',[del1,':',ddel,':',del2]);
                end
            end
            RC=[RF(1:end-1),{'DELTAL','DELTAR'}];
            for k=1:length(RC)
                set(A_In(k),'String',num2str(A.(RC{k})));
            end
            if length(A.DELTAL)>1           %array of left deflections
                del = A.DELTAL; ddel = del(2:end)-del(1:end-1);
                if ~sum(ddel-ddel(1))       %uniform spacing
                    del1 = num2str(del(1));
                    ddel = num2str(ddel(1));
                    del2 = num2str(del(end));
                    set(A_In(end-1),'String',[del1,':',ddel,':',del2]);
                end
            end
            if length(A.DELTAR)>1           %array of right deflections
                del = A.DELTAR; ddel = del(2:end)-del(1:end-1);
                if ~sum(ddel-ddel(1))       %uniform spacing
                    del1 = num2str(del(1));
                    ddel = num2str(ddel(1));
                    del2 = num2str(del(end));
                    set(A_In(end),'String',[del1,':',ddel,':',del2]);
                end
            end
            
            %Initialize Body Parameters
            if BD.NX>11
                XP = linspace(BD.X(1),BD.X(end),11);
                N = interp1(BD.X,1:BD.NX,XP,'nearest','extrap');
                if length(unique(N))<BD.NX, N = [1:10,BD.NX]; end
            else
                N = 1:BD.NX;
            end
            for i=1:min([BD.NX,11])
                set(BD_In(1,i),'String',num2str(N(i)))
                set(BD_In(2,i),'String',num2str(BD.X(N(i))))
                set(BD_In(3,i),'String',num2str(BD.P(N(i))))
            end
            set(BD_In(1:3,i+1:7),'String',''), BD.N = N;
            
            %Initialize Aero Parameters
            RA={'ALSCHD','ALT','MACH','WT','XCG','ZCG','XI','YI'};
            for k=1:length(RA)
                set(AERO_In(k),'String',num2str(AERO.(RA{k})))
            end
            if length(AERO.ALSCHD)>1	%array of alphas
                aoa = AERO.ALSCHD; da = aoa(2:end)-aoa(1:end-1);
                if ~sum(da-da(1))       %uniform spacing
                    a1 = num2str(aoa(1));
                    da = num2str(da(1));
                    a2 = num2str(aoa(end));
                    set(AERO_In(1),'String',[a1,':',da,':',a2]);
                end
            end
            if length(AERO.ALT)>1     	%array of altitudes
                alt = AERO.ALT; da = alt(2:end)-alt(1:end-1);
                if ~sum(da-da(1))       %uniform spacing
                    a1 = num2str(alt(1));
                    da = num2str(da(1));
                    a2 = num2str(alt(end));
                    set(AERO_In(2),'String',[a1,':',da,':',a2]);
                end
            end
            if length(AERO.MACH)>1  	%array of machs
                ma = AERO.MACH; da = ma(2:end)-ma(1:end-1);
                if ~sum(da-da(1))       %uniform spacing
                    a1 = num2str(ma(1));
                    da = num2str(da(1));
                    a2 = num2str(ma(end));
                    set(AERO_In(3),'String',[a1,':',da,':',a2]);
                end
            end
            set(AERO_In(end),'Value',AERO.XCG,'Min',BD.X(1),'Max',BD.X(end))
            if ispc, path_brk='\'; else, path_brk = '/'; end %PC uses \
            for i=1:length(WG.NACA)
                i1=strfind(WG.NACA{i},path_brk); i2=strfind(WG.NACA{i},'.');
                if ~isempty(i1) && ~isempty(i2) %airfoil
                    set(AERO_In(8+i),'String',WG.NACA{i}(i1(end)+1:i2(end)-1));
                elseif ~isempty(i2)
                    set(AERO_In(8+i),'String',WG.NACA{i}(1:i2(end)-1));
                else
                    set(AERO_In(8+i),'String',WG.NACA{i});
                end
            end
            if length(WG.DATA)<2, set(AERO_In(10),'String',get(AERO_In(9),'String')), end
            i1=strfind(HT.NACA{1},path_brk); i2=strfind(HT.NACA{1},'.');
            if ~isempty(i1) && ~isempty(i2)                 %airfoil
                set(AERO_In(11),'String',HT.NACA{1}(i1(end)+1:i2(end)-1));
            elseif ~isempty(i2)
                set(AERO_In(11),'String',HT.NACA{1}(1:i2(end)-1));
            else
                set(AERO_In(11),'String',HT.NACA{1});
            end
            
            %Only Make Selected Components Visible
            for i=1:4, Viz(plot_cmp(i),0,i), end
            
            %Check for Added Parts
            re_initialize = 0;
            for n=1:4, re_initialize = re_initialize||~isempty(NP{n}); end
            for n=1:2, re_initialize = re_initialize||~isempty(NB{n}); end
            
            %Unit
            if strcmp(unit,'in')
                if strcmp(get(opt(14),'Checked'),'off'), re_initialize = 1; end
                set(opt(14),'Checked','on')
                set(opt(17),'Checked','off')
            else
                if strcmp(get(opt(14),'Checked'),'on'), re_initialize = 1; end
                set(opt(14),'Checked','off')
                set(opt(17),'Checked','on')
            end
            
            %Load CG Data
            if exist('cg_data','var'), set(opt(1),'UserData',cg_data), end
            
            %Refresh GUI
            if re_initialize, Initialize_GUI, return, end
            
        case 'D' %DATCOM Input File
            
            %Choose Input File
            %if exist('Models','dir'), cd Models, fl = 1; else, fl = 0; end
            [Fn,P]=uigetfile({'*.dat;*.txt;','Text Files'},...
                'Choose Datcom Input File(s)',fullfile(lib_path,'Models'),...
                'MultiSelect','on');
            %if fl, cd .., end
            if ~isempty(Fn) && ~isnumeric(Fn)
                DATCOM_IO(Fn,P)
            else
                AID(0,0,'update'), return
            end
            
    end
    
elseif strcmp(action,'update')%%%%%%%%%%%%%%%%% UPDATE %%%%%%%%%%%%%%%%%%%%
    
    %Update Option
    if nargin<4, choice = get(handle,'Tag'); end
    if iscell(choice) && length(choice)>=3
        WG.DATA{1} = choice{1};
        HT.DATA{1} = choice{2};
        VT.DATA{1} = choice{2};
        i = 0;
        for n=1:4
            if ~isempty(NP{n})
                i = i+1; NP{n}.DATA{1} = choice{3+i};
            end
        end
        choice = [];
    end
    
    %Either Update All or Adjust CG
    if ~strcmp(choice,'cg')
        
        %Initialize Global Aircraft Variable
        if isempty(AC), AC.alpha=0; end
        
        %List Datcom Parameters
        RP={'CHRDR','CHRDBP','CHRDTP','SSPN','SSPNOP','SAVSI','SAVSO',...
            'CHSTAT','DHDADI','DHDADO','TC','TWISTA','i','X','Y','Z'};
        RF={'SPANFI','SPANFO','CHRDFI','CHRDFO','DELTA'};
        RC=[RF(1:end-1),{'DELTAL','DELTAR'}];
        RA={'ALSCHD','ALT','MACH','WT','XCG','ZCG','XI','YI'};
        
        %Reset Background Color
        gray = [0.94,0.94,0.94]; blue = [0.8,0.9,1];
        set(findall(gcf,'Style','edit'),'BackgroundColor',gray)
        if isprop(handle,'Style') && strcmp(get(handle,'Style'),'edit')
            set(handle,'BackGroundColor',blue)
        end
        
        %Allow Variable Assignment for Empty Inputs
        if handle~=0, set(handle,'String',strtrim(get(handle,'String'))), end
        if handle~=0 && strcmp(get(handle,'String'),'='), handle.String = ''; end
        if handle~=0 && isempty(get(handle,'String')) && ...
                isnan(str2double(get(handle,'Tag'))) && ... %not BD_In
                ~isempty(get(handle,'Tag')) %not AERO_In
            allow_click_select = strcmp(ax{1}.Tag,'Geometry');
            if allow_click_select; ax{3} = {}; end %select mode on
            while isempty(handle.String)
                set(gcf,'Pointer','watch')
                waitforbuttonpress; pause(0.2)
                if strcmp(get(gco,'Type'),'surface') && allow_click_select
                    part = get(gco,'Tag');
                    if ~isempty(strfind(part,'tip'))
                        part = part(1:end-3);
                    end
                    if isempty(strfind(part,'BD')) && isempty(strfind(part,'NB'))
                        comp = get(gco,'UserData');
                        if ~isempty(comp)
                            handle.String = [part,'.',comp];
                        end
                    end
                elseif strcmp(get(gco,'Type'),'uicontrol')
                    if ~isempty(strfind(get(gco,'Tag'),'.'))
                        handle.String = get(gco,'Tag');
                    else
                        handle.String = get(gco,'String');
                    end
                end
            end
            if allow_click_select; ax{3} = []; end %select mode off
            set(gcf,'Pointer','arrow')
            if strcmp(get(get(handle,'parent'),'Type'),'uitab')
                set(tabs,'SelectedTab',get(handle,'parent'))
            end
        end
        
        %Error Check Planforms
        check_error = check_error && strcmp(get(gco,'Type'),'uicontrol')...
            && strcmp(get(gco,'Style'),'edit');
        if check_error
            if lim(3)==0, lim(3)=get(opt(16),'UserData'); end
            mn={lim(3),lim(3),lim(3),lim(3),0,-lim(2),-lim(2),0,-lim(2),...
                -lim(2),0.01,-lim(2),-lim(2),-lim(1),-lim(1),-lim(1)};
            mx={lim(1),lim(1),'CHRDR',lim(1),'SSPN',lim(2),lim(2),1,...
                lim(2),lim(2),0.99,lim(2),lim(2),lim(1),lim(1),lim(1)};
            Error_Check(WG,WG_In,mn,mx)
            Error_Check(HT,HT_In,mn,mx)
            Error_Check(VT,VT_In,mn,mx)
            for n=1:length(NP)
                if ~isempty(NP{n}), Error_Check(NP{n},NP_In{n},mn,mx), end
            end
        end
        
        %Update Planforms
        for i=1:length(RP), WG.(RP{i})=eval(get(WG_In(i),'String')); end
        for i=1:length(RP), HT.(RP{i})=eval(get(HT_In(i),'String')); end
        for i=1:length(RP), VT.(RP{i})=eval(get(VT_In(i),'String')); end
        for n=1:length(NP)
            if ~isempty(NP_In{n})
                for i=1:length(RP)
                    NP{n}.(RP{i})=eval(get(NP_In{n}(i),'String'));
                end
                NP{n}.SSPNE=NP{n}.SSPN;
            end
        end
        
        %Update Break Span
        if ~WG.SSPNOP, set(WG_In([7,10]),'Enable','off')
        else, set(WG_In([7,10]),'Enable','on'), end
        if ~HT.SSPNOP, set(HT_In([7,10]),'Enable','off')
        else, set(HT_In([7,10]),'Enable','on'), end
        if ~VT.SSPNOP, set(VT_In([7,10]),'Enable','off')
        else, set(VT_In([7,10]),'Enable','on'), end
        if handle==WG_In(2) && ~WG.SSPNOP
            WG.SSPNOP=WG.SSPN/2; set(WG_In(5),'String',num2str(WG.SSPNOP))
        elseif handle==HT_In(2) && ~HT.SSPNOP
            HT.SSPNOP=HT.SSPN/2; set(HT_In(5),'String',num2str(HT.SSPNOP))
        elseif handle==VT_In(2) && ~VT.SSPNOP
            VT.SSPNOP=VT.SSPN/2; set(VT_In(5),'String',num2str(VT.SSPNOP))
        end
        for n=1:length(NP)
            if ~isempty(NP_In{n})
                if ~NP{n}.SSPNOP, set(NP_In{n}([7,10]),'Enable','off')
                else, set(NP_In{n}([7,10]),'Enable','on'), end
                if handle==NP_In{n}(2)
                    NP{n}.SSPNOP = NP{n}.SSPN/2;
                    set(NP_In{n}(5),'String',num2str(NP{n}.SSPNOP))
                end
                if handle==NP_In{n}(11)
                    TC0 = max(NP{n}.DATA{1}(:,2))-min(NP{n}.DATA{1}(:,2));
                    for i=1:length(NP{n}.DATA)
                        NP{n}.DATA{i}(:,2) = NP{n}.DATA{i}(:,2)*max([NP{n}.TC,0.01])/TC0;
                    end
                end
            end
        end
        
        %Update NACA if Thickness Changed
        if length(WG.NACA{1})==6
            airfoil = str2double(WG.NACA{1}([1:2,4:end]));
        else
            airfoil = str2double(WG.NACA{1});
        end
        if handle==WG_In(11)
            TC0 = max(WG.DATA{1}(:,2))-min(WG.DATA{1}(:,2));
            for i=1:length(WG.DATA)
                WG.DATA{i}(:,2) = WG.DATA{i}(:,2)*max([WG.TC,0.01])/TC0;
            end
            if ~isnan(airfoil) && airfoil
                if WG.TC>=0.1
                    WG.NACA{1}(end-1:end)=num2str(WG.TC*100);
                    WG.NACA{2}(end-1:end)=num2str(WG.TC*100);
                else
                    WG.NACA{1}(end-1:end)=['0',num2str(WG.TC*100)];
                    WG.NACA{2}(end-1:end)=['0',num2str(WG.TC*100)];
                end
                set(AERO_In(9),'String',WG.NACA{1})
                set(AERO_In(10),'String',WG.NACA{2})
            end
        elseif handle==HT_In(11)
            TC0 = max(HT.DATA{1}(:,2))-min(HT.DATA{1}(:,2));
            for i=1:length(HT.DATA)
                HT.DATA{i}(:,2) = HT.DATA{i}(:,2)*max([HT.TC,0.01])/TC0;
            end
            if ~isnan(airfoil) && airfoil
                if HT.TC>=0.1
                    HT.NACA{1}(end-1:end)=num2str(HT.TC*100);
                else
                    HT.NACA{1}(end-1:end)=['0',num2str(HT.TC*100)];
                end
                set(AERO_In(11),'String',HT.NACA{1})
            end
        elseif handle==VT_In(11)
            TC0 = max(VT.DATA{1}(:,2))-min(VT.DATA{1}(:,2));
            for i=1:length(VT.DATA)
                VT.DATA{1}(:,2) = VT.DATA{1}(:,2)*max([VT.TC,0.01])/TC0;
            end
        end
        
        %Error Check Controls
        if check_error
            mn={0,0,0,0,-lim(2),-lim(2)};
            mx={lim(1),lim(1),lim(1),lim(1),lim(2),lim(2)};
            Error_Check(F,F_In,mn,mx)
            Error_Check(A,A_In,mn,mx)
            Error_Check(E,E_In,mn,mx)
            Error_Check(R,R_In,mn,mx)
            if handle==A_In(5), set(A_In(6),'String',get(A_In(5),'String')), end
            if handle==A_In(6), set(A_In(5),'String',get(A_In(6),'String')), end
        end
        
        %Update Flaps
        for i=1:length(RF)-1, F.(RF{i})=eval(get(F_In(i),'String'));end
        deltas=get(F_In(end),'String');    F.DELTA=str2double(deltas);
        if ~isempty(strfind(deltas,':')),  F.DELTA=eval(deltas);    end
        if isnan(F.DELTA), F.DELTA=eval(['[',deltas,']']);          end
        
        %Update Ailerons
        for i=1:length(RC)-2, A.(RC{i})=eval(get(A_In(i),'String'));end
        deltals=get(A_In(end-1),'String');A.DELTAL=str2double(deltals);
        if ~isempty(strfind(deltals,':')), A.DELTAL=eval(deltals);  end
        if isnan(A.DELTAL), A.DELTAL=eval(['[',deltals,']']);       end
        deltars=get(A_In(end),'String');  A.DELTAR=str2double(deltars);
        if ~isempty(strfind(deltars,':')), A.DELTAR=eval(deltars);  end
        if isnan(A.DELTAR), A.DELTAR=eval(['[',deltars,']']);       end
        
        %Update Elevator
        for i=1:length(RF)-1, E.(RF{i})=eval(get(E_In(i),'String'));end
        deltas=get(E_In(end),'String');    E.DELTA=str2double(deltas);
        if ~isempty(strfind(deltas,':')),  E.DELTA=eval(deltas);    end
        if isnan(E.DELTA), E.DELTA=eval(['[',deltas,']']);          end
        
        %Update Rudder
        for i=1:length(RF)-1, R.(RF{i})=eval(get(R_In(i),'String'));end
        deltas=get(R_In(end),'String');    R.DELTA=str2double(deltas);
        if ~isempty(strfind(deltas,':')),  R.DELTA=eval(deltas);    end
        if isnan(R.DELTA), R.DELTA=eval(['[',deltas,']']);          end
        
        %Force Circular Cross-Sections
        if nargin>3 && strcmp(choice,'Fuselage') %circularize
            [~,El] = view(ax{1});
            if El>45
                BD.ZU = BD.R; BD.ZL = -BD.R;
            else
                BD.R=(BD.ZU-BD.ZL)/2;
            end
        end
        
        %Update Fuselage Station Inputs
        if get(cmp(4),'Value'), set(BD_In,'Enable','on'), end
        if BD.NX<11
            set(BD_In(:,BD.NX+1:end-1),'Enable','off','String','')
        end
        if ~isnan(str2double(choice)) &&  strcmp(choice(1),'0')
            choice = ['0',get(BD_In(1,str2double(choice)),'String')];
        end
        %(11 control points for arbitrary number of stations)
        N = get(BD_In(1,1:11),'String'); P = ones(1,min([BD.NX,11]));
        for i=1:length(P)
            if handle==BD_In(1,i) || handle==BD_In(2,i) %correct inputs
                N0 = get(BD_In(1,i),'String'); %station
                if strfind(N0,'.') %prevent decimal inputs
                    set(BD_In(1,i),'String',N0(1:strfind(N0,'.')-1))
                end
                if str2double(N0)<1
                    set(BD_In(1,i),'String','1')
                elseif str2double(N0)>BD.NX
                    set(BD_In(1,i),'String',num2str(BD.NX))
                end
                for j=1:min([BD.NX,11]) %prevent overlap (identical values)
                    Nmatch = i~=j && strcmp(N0,N{j});
                    Nhigh = j>i && eval(N0)>=eval(N{j});
                    Nlow = j<i && eval(N0)<eval(N{j});
                    if Nmatch || Nhigh || Nlow
                        set(BD_In(1,1:11),'BackgroundColor',gray)
                        set(BD_In(1,i),'String',sprintf('%d',BD.N(i)))
                        set(gcf,'CurrentObject',BD_In(1,j))
                        set(BD_In(1,j),'BackgroundColor',blue)
                    end
                end
            end
            if handle==BD_In(1,i)
                N = eval(get(BD_In(1,i),'String'));
                choice = ['0',num2str(N)];
                set(BD_In(2,i),'String',num2str(round(BD.X(N),1)))
            end
            P0 = get(BD_In(3,i),'String');
            if ~isempty(P0)
                P(i) = eval(P0);
                BD.N(i) = eval(get(BD_In(1,i),'String'));
                BD.X(BD.N(i)) = eval(get(BD_In(2,i),'String'));
            else
                P(i) = NaN;
            end
            if P(i)<0 %quick error check
                P(i)=0; set(BD_In(3,i),'String','0')
            elseif P(i)>10
                P(i)=10; set(BD_In(3,i),'String','10')
            end
        end
        if length(unique(BD.X))<length(BD.X)
            [~,i1] = unique(BD.X,'stable');
            for i=2:BD.NX
                if isempty(find(i==i1,1)), BD.X(i) = BD.X(i-1)+1e-6; end
            end
        end
        set(BD_In(1:2,isnan(P)),'Enable','off')
        if length(P)<11, set(BD_In(:,11),'Enable','off'), end
        Nin = BD.N(~isnan(P)); Pin = P(~isnan(P));
        BD.P = interp1(BD.X(Nin),Pin,BD.X,'linear','extrap');
        
        %Update Secondary/Tertiary Bodies
        for n=1:2
            if ~isempty(NB_In{n}) && get(cmp(8+n),'Value')
                NB{n}.X0 = eval(get(NB_In{n}(1,8),'String'));
                NB{n}.Y0 = eval(get(NB_In{n}(1,9),'String'));
                NB{n}.Z0 = eval(get(NB_In{n}(1,10),'String'));
                
                %Force Circular Cross-Sections
                check = sprintf('Body %d',n);
                if strcmp(choice,check)
                    [~,El] = view(ax{1});
                    if El>45
                        NB{n}.ZU = NB{n}.R; NB{n}.ZL = -NB{n}.R;
                    else
                        NB{n}.R=(NB{n}.ZU-NB{n}.ZL)/2;
                    end
                end
                
                %Update Fuselage Station Inputs
                if get(cmp(8+n),'Value'), set(NB_In{n}(:,1:7),'Enable','on'), end
                if NB{n}.NX<7
                    set(NB_In{n}(:,NB{n}.NX+1:7),'Enable','off','String','')
                end
                if ~isnan(str2double(choice)) &&  strcmp(choice(1),num2str(n))
                    choice = [num2str(n),get(NB_In{n}(1,str2double(choice(2:end))),'String')];
                end
                %(7 control points for arbitrary number of stations)
                N = get(NB_In{n}(1,1:7),'String'); P = ones(1,min([BD.NX,7]));
                for i=1:length(P)
                    if handle==NB_In{n}(1,i) || handle==NB_In{n}(2,i) %correct inputs
                        N0 = get(NB_In{n}(1,i),'String'); %station
                        if strfind(N0,'.') %prevent decimal inputs
                            set(NB_In{n}(1,i),'String',N0(1:strfind(N0,'.')-1))
                        end
                        if str2double(N0)<1
                            set(NB_In{n}(1,i),'String','1')
                        elseif str2double(N0)>NB{n}.NX
                            set(NB_In{n}(1,i),'String',num2str(NB{n}.NX))
                        end
                        for j=1:min([NB{n}.NX,7]) %prevent overlap (identical values)
                            Nmatch = i~=j && strcmp(N0,N{j});
                            Nhigh = j>i && eval(N0)>=eval(N{j});
                            Nlow = j<i && eval(N0)<eval(N{j});
                            if Nmatch || Nhigh || Nlow
                                set(NB_In{n}(1,1:11),'BackgroundColor',gray)
                                set(NB_In{n}(1,i),'String',sprintf('%d',NB{n}.N(i)))
                                set(gcf,'CurrentObject',NB_In{n}(1,j))
                                set(NB_In{n}(1,j),'BackgroundColor',blue)
                            end
                        end
                    end
                    if handle==NB_In{n}(1,i)
                        N = eval(get(NB_In{n}(1,i),'String'));
                        choice = [num2str(n),num2str(N)];
                        set(NB_In{n}(2,i),'String',num2str(round(NB{n}.X(N),1)))
                    end
                    P0 = get(NB_In{n}(3,i),'String');
                    if ~isempty(P0)
                        P(i) = eval(P0);
                        NB{n}.N(i) = eval(get(NB_In{n}(1,i),'String'));
                        NB{n}.X(NB{n}.N(i)) = eval(get(NB_In{n}(2,i),'String'));
                    else
                        P(i) = NaN;
                    end
                    if P(i)<0
                        P(i)=0; set(NB_In{n}(3,i),'String','0')
                    elseif P(i)>10
                        P(i)=10; set(NB_In{n}(3,i),'String','10')
                    end
                end
                if length(unique(NB{n}.X))<length(NB{n}.X)
                    [~,i1] = unique(NB{n}.X,'stable');
                    for i=2:NB{n}.NX
                        if isempty(find(i==i1,1)), NB{n}.X(i) = NB{n}.X(i-1)+1e-6; end
                    end
                end
                if length(P)<7, set(NB_In{n}(:,7),'Enable','off'), end
                set(NB_In{n}(1:2,isnan(P)),'Enable','off')
                Nin = NB{n}.N(~isnan(P)); Pin = P(~isnan(P));
                NB{n}.P = interp1(NB{n}.X(Nin),Pin,NB{n}.X,'linear','extrap');
            end
        end
        
        %Second Update (for Adjusted Geometry)
        %%%% 2.6% increase in update time %%%%
        for i=1:length(RP), WG.(RP{i})=eval(get(WG_In(i),'String')); end
        for i=1:length(RP), HT.(RP{i})=eval(get(HT_In(i),'String')); end
        for i=1:length(RP), VT.(RP{i})=eval(get(VT_In(i),'String')); end
        for n=1:length(NP)
            if ~isempty(NP_In{n})
                for i=1:length(RP)
                    NP{n}.(RP{i})=eval(get(NP_In{n}(i),'String'));
                end
                NP{n}.SSPNE=NP{n}.SSPN;
            end
        end
        
        %Calculate Wing-Body Interference Parameters
        LE_pts = [WG.X,HT.X,VT.X];
        TE_pts = LE_pts + [WG.CHRDR,HT.CHRDR,VT.CHRDR];
        R_LE = interp1(BD.X,BD.R,LE_pts,'spline','extrap');
        R_TE = interp1(BD.X,BD.R,TE_pts,'spline','extrap');
        WG.SSPNE = WG.SSPN-(R_LE(1)+R_TE(1))/2;
        HT.SSPNE = HT.SSPN-(R_LE(2)+R_TE(2))/2;
        VT.SSPNE = VT.SSPN-(R_LE(3)+R_TE(3))/2;
        S_LE = interp1(BD.X,BD.S,WG.X,'spline','extrap');
        S_TE = interp1(BD.X,BD.S,WG.X+WG.CHRDR,'spline','extrap');
        BD.d_eq = 2*sqrt((S_LE+S_TE)/2/pi); %averaged at root chord
        
        %Update Aerodynamic Parameters
        alphas=get(AERO_In(1),'String');   AERO.ALSCHD=str2double(alphas);
        if ~isempty(strfind(alphas,':')),  AERO.ALSCHD=eval(alphas); end
        if isnan(AERO.ALSCHD), AERO.ALSCHD=eval(['[',alphas,']']);   end
        alts=get(AERO_In(2),'String');   AERO.ALT=str2double(alts);
        if ~isempty(strfind(alts,':')),  AERO.ALT=eval(alts); end
        if isnan(AERO.ALT), AERO.ALT=eval(['[',alts,']']);   end
        machs=get(AERO_In(3),'String');   AERO.MACH=str2double(machs);
        if ~isempty(strfind(machs,':')),  AERO.MACH=eval(machs); end
        if isnan(AERO.MACH), AERO.MACH=eval(['[',machs,']']);   end
        if AERO.MACH(1)>1 %correct ft/s or kts input to Mach
            if kts, AERO.MACH=AERO.MACH*1.68781; end
            AERO.MACH=AERO.MACH/ATM.a;
            set(AERO_In(3),'String',sprintf('%.3f',AERO.MACH));
            if length(AERO.MACH)>1
                set(AERO_In(3),'String',sprintf(',%.2f',AERO.MACH(2:end)));
            end
        end
        checks = {'ALT','MACH','WT'};
        for i=1:length(checks) %error check aero
            if length(AERO.(checks{i}))==1 && AERO.(checks{i})<0
                AERO.(checks{i}) = 1e-6; set(AERO_In(i+1),'String','0')
            end
        end
        
        %Inertia (convert from oz*in^2 to slug*ft^2)
        if inch
            AERO.XI = AERO.XI/74129.0079;
            AERO.YI = AERO.YI/74129.0079;
        end
        
        %CG Select/Airfoil Data
        for i=4:length(RA), AERO.(RA{i})=eval(get(AERO_In(i),'String'));end
        if ispc, path_brk='\'; else, path_brk = '/'; end %PC path uses \
        switch handle
            case {AERO_In(5),AERO_In(6)} %CG
                choice='cg';
                set(AERO_In(end),'Value',AERO.XCG)
            case AERO_In(9) %Wing Airfoil
                NACA=get(AERO_In(9),'String');
                if isempty(strfind(WG.NACA{1},NACA))||strcmp(NACA,'0')
                    WG.NACA{1}=NACA; end %do not update if no airfoil change
                if isempty(WG.NACA{1}), WG.NACA{1}='0'; end  	%non-NACA
                WG = Lift_Curve_Slope(WG,1);                    %aero
                set(WG_In(11),'String',sprintf('%.2f',WG.TC))   %thickness
                i1=strfind(WG.NACA{1},path_brk); i2=strfind(WG.NACA{1},'.');
                if ~isempty(i1) && ~isempty(i2)                 %airfoil
                    set(AERO_In(9),'String',WG.NACA{1}(i1(end)+1:i2(end)-1));
                elseif ~isempty(i2)
                    set(AERO_In(9),'String',WG.NACA{1}(1:i2(end)-1));
                end
                if length(WG.DATA)<2 %if only prescribing 1 airfoil
                    set(AERO_In(10),'String',get(AERO_In(9),'String'))
                end
            case AERO_In(10) %Wing Airfoil
                NACA=get(AERO_In(10),'String');
                if isempty(strfind(WG.NACA{2},NACA))||strcmp(NACA,'0')
                    WG.NACA{2}=NACA; end %do not update if no airfoil change
                if isempty(WG.NACA{2}), WG.NACA{2}='0'; end     %non-NACA
                WG = Lift_Curve_Slope(WG,2);                    %aero
                set(WG_In(11),'String',sprintf('%.2f',WG.TC))   %thickness
                i1=strfind(WG.NACA{2},path_brk); i2=strfind(WG.NACA{2},'.');
                if ~isempty(i1) && ~isempty(i2)                 %airfoil
                    set(AERO_In(10),'String',WG.NACA{2}(i1(end)+1:i2(end)-1));
                elseif ~isempty(i2)
                    set(AERO_In(10),'String',WG.NACA{2}(1:i2(end)-1));
                end
            case AERO_In(11) %Tail Airfoil
                NACA=get(AERO_In(11),'String');
                if isempty(strfind(HT.NACA{1},NACA))||strcmp(NACA,'0')
                    HT.NACA{1}=NACA; end
                if isempty(HT.NACA{1}), HT.NACA={'0'}; end      %non-NACA
                HT = Lift_Curve_Slope(HT,1);                    %aero
                set(HT_In(11),'String',sprintf('%.2f',HT.TC))   %thickness
                i1 = strfind(HT.NACA{1},path_brk); i2 = strfind(HT.NACA{1},'.');
                if ~isempty(i1) && ~isempty(i2)                 %airfoil
                    set(AERO_In(11),'String',HT.NACA{1}(i1(end)+1:i2(end)-1));
                elseif ~isempty(i2)
                    set(AERO_In(11),'String',HT.NACA{1}(1:i2(end)-1));
                end
        end
        
        %Update CG
        if cg_calc
            cg_data = get(opt(1),'UserData'); x=zeros(1,10); z=x; w=x;
            for i=1:10
                x(i)=eval(cg_data{1,i});
                z(i)=eval(cg_data{2,i});
                w(i)=eval(cg_data{3,i});
            end
            x0 = zeros(1,length(cg_data)); z0 = x0;
            x0(1:4) = [WG.X,HT.X,VT.X,BD.X(1)];
            z0(1:4) = [WG.Z,HT.Z,VT.Z,0];
            if ~get(cmp(1),'Value'), w(1)=0; end
            if ~get(cmp(1),'Value'), w(2)=0; end
            if ~get(cmp(1),'Value'), w(3)=0; end
            if ~get(cmp(1),'Value'), w(4)=0; end
            for n=1:4
                if ~isempty(NP_In{n}) && get(cmp(4+n),'Value')
                    x0(4+n)=NP{n}.X;
                    z0(4+n)=NP{n}.Z;
                else
                    w(4+n)=0;
                end
            end
            for n=1:2
                if ~isempty(NB_In{n}) && get(cmp(8+n),'Value')
                    x0(8+n)=NB{n}.X0(1);
                    z0(8+n)=NB{n}.Z0(1);
                else
                    w(8+n)=0;
                end
            end
            x = x+x0; z=z+z0; if strcmp(unit,'in'), w=w/16; end
            if sum(w)==0
                msg=msgbox('Right click components for Weight/Balance');
                waitfor(msg);
            else
                choice='cg';
                AERO.WT = sum(w);
                AERO.XCG = sum(x.*w)/sum(w);
                AERO.ZCG = sum(z.*w)/sum(w);
                set(AERO_In(4),'String',num2str(AERO.WT))
                set(AERO_In(5),'String',num2str(AERO.XCG))
                set(AERO_In(6),'String',num2str(AERO.ZCG))
            end
            
        end
        
        %%%%%%%%%%%%%%%%%% BEGIN STABILITY ANALYSIS %%%%%%%%%%%%%%%%%%%%%%%
        
        %Gather/Assume 2-D Aerodynamic Parameters
        if ~isfield(WG,'a0')||~WG.a0(1)
            WG.a0=0.116; WG.alpha0=-2.11; WG.Cm_ac=-0.06;
        end
        if ~isfield(HT,'a0')||~HT.a0(1)
            HT.a0=0.117; HT.alpha0=0.00; HT.Cm_ac=-0.0055; %panel method
        end
        
        %Determine Geometric Parameters
        WG=Geometry(WG,angl);HT=Geometry(HT,angl);VT=Geometry(VT,angl,'v');
        
        %Free-Stream Conditions
        ATM=Atmosphere(AERO.ALT);
        ATM.Q=1/2*ATM.D*(AERO.MACH(1)*ATM.a)^2; %Dynamic Pressure (psf)
        if strcmp(unit,'in'), ATM.Q=ATM.Q/144; end %or convert to psi
        ATM.Re=ATM.D*AERO.MACH(1)*ATM.a/ATM.V;  %Reynolds Number no Ref Dim
        
        %Estimate Parasite Drag Buildup
        AC.CD0=0;
        if get(cmp(1),'Value'), WG=Drag(WG,unit); AC.CD0=AC.CD0+WG.CD0; end
        if get(cmp(2),'Value'), HT=Drag(HT,unit); AC.CD0=AC.CD0+HT.CD0; end
        if get(cmp(3),'Value'), VT=Drag(VT,unit); AC.CD0=AC.CD0+VT.CD0; end
        if get(cmp(4),'Value'), BD=Drag(BD,unit); AC.CD0=AC.CD0+BD.CD0; end
        for n=1:4
            if ~isempty(NP_In{n}) && get(cmp(4+n),'Value')
                NP{n}=Geometry(NP{n},angl);  NP{n}=Drag(NP{n},unit);
                if NP{n}.Y, NP{n}.CD0=NP{n}.CD0*2; end
                AC.CD0=AC.CD0+NP{n}.CD0;
            end
        end
        for n=1:2
            if ~isempty(NB_In{n}) && get(cmp(8+n),'Value')
                NB{n}=Drag(NB{n},unit);
                if NB{n}.Y0, NB{n}.CD0=NB{n}.CD0*2; end
                AC.CD0=AC.CD0+NB{n}.CD0;
            end
        end
        AC.CD0=1.25*AC.CD0; %estimated interference drag
        
        %Determine Aerodynamic Parameters
        WG=Aero(WG,AERO.MACH(1),angl); HT=Aero(HT,AERO.MACH(1),angl);
        
        %Estimate Downwash at Tail
        if downwash, Downwash; else, HT.dwash=dw(1); HT.eta=dw(2); end
        
        %Calculate Fuselage Stability
        if body_method
            Body_Stability('Multhopp');
        else
            Body_Stability('Gilruth_White');
        end
        
        %Aircraft Lift Coefficient and CG Location
        if isnan(str2double(get(AERO_In(5),'String')))
            AERO.XCG = eval(get(AERO_In(5),'String'));
        end
        AC.CL = AERO.WT/(ATM.Q*WG.S(end));
        AC.x_cg = (AERO.XCG-WG.X-WG.xmac)/WG.cbar(end);
        
        %Tail Volume Coefficients
        HT.l = HT.X+HT.x_ac*HT.cbar(end)+HT.xmac-AERO.XCG; 	%cg -> x_ac
        VT.l = VT.X+VT.cbar(end)/4+VT.xmac-AERO.XCG;      	%cg -> 25%cbar
        HT.V = HT.S(end)*HT.l/(WG.S(end)*WG.cbar(end));  	%HT Volume Term
        VT.V = VT.S(end)*VT.l/(WG.S(end)*WG.b);            	%VT Volume Term
        
        %Lateral/Directional Stability Corrections
        Lat_Dir_Corrections(AERO.MACH(1))
        
        %Perform Lateral Stability Analysis
        Lateral_Static_Stability(angl,cmp)
        Lateral_Dynamic_Stability
        
        %Estimate Control Surface Parameters
        F = Controls(F); A = Controls(A); E = Controls(E);
        
        %Prepare Variables for Trim
        if trim_mode == 2
            switch handle
                case WG_In(13),  HT.i=[];
                case HT_In(13),  WG.i=[];
                otherwise
                    if length(AERO.ALSCHD)==1
                        HT.i=[]; WG.i=[];
                    else
                        HT.i=[]; %default to HT trim
                    end
            end
        end
        
        %Perform Longitudinal Static Stability Calculation
        htail = get(cmp(2),'Value'); body = get(cmp(4),'Value');
        Longitudinal_Static_Stability(trim_mode,htail,body,angl)
        
        %Update Trim Solution
        set(WG_In(13),'String',sprintf('%.1f',WG.i))
        set(HT_In(13),'String',sprintf('%.1f',HT.i))
        if length(AERO.ALSCHD)==1
            set(AERO_In(1),'String',sprintf('%.1f',AC.alpha))
        end
        
        %Perform Longitudinal Dynamic Stability Analysis
        Longitudinal_Dynamic_Stability
        
        %%%%%%%%%%%%%%%%%%% END STABILITY ANALYSIS %%%%%%%%%%%%%%%%%%%%%%%%
        
    else %continuous CG adjust
        
        %Update Control Surface Parameters
        F = Controls(F); E = Controls(E);
        
        %Perform Longitudinal Static Stability Calculation
        AC.x_cg = (AERO.XCG-WG.X-WG.xmac)/WG.cbar(end);
        HT.l = HT.X+HT.x_ac*HT.cbar(end)+HT.xmac-AERO.XCG;   	%cg -> x_ac
        htail = get(cmp(4),'Value'); body = get(cmp(4),'Value');
        Longitudinal_Static_Stability(trim_mode,htail,body,angl)
        
    end
    
    %Trim Elevator
    if trim_mode == 1
        set(E_In(5),'String',num2str(E.DELTA))
        if strcmp(get(E_In(5),'Enable'),'on')
            set(E_In(5),'Enable','off')
        end
    elseif get(cmp(2),'Value')
        if strcmp(get(E_In(5),'Enable'),'off')
            set(E_In(5),'Enable','on')
        end
    end
    
    %Print Report(s)
    reports = get(gcf,'UserData');
    for i=1:size(reports,1)
        if ~isempty(reports{i,1})
            plot_val = [];
            variable = get(reports{i,1}(3),'String');
            if ~isempty(strtrim(variable))
                if ~isempty(strfind(variable,'='))
                    eval(variable)
                    value = 'Evaluated Expression';
                elseif isnumeric(eval(variable))&&length(eval(variable))==1
                    plot_val = eval(variable);
                    value = sprintf('=%.6f',plot_val);
                else
                    eval(variable)
                    value = 'In Command Window';
                end
                if ~isempty(strfind(variable,'N0')), choice='np'; end
            else
                value = 'Define output variable';
            end
            set(reports{i,1}(4),'String',num2str(value))
            
            %Plot Cost Analysis
            if ~isempty(ax{6}) && ~isempty(plot_val) && strcmp(ax{6}{i}.Visible,'on') && ...
                    strcmp(get(handle,'Type'),'uicontrol') && ...
                    strcmp(get(handle,'Style'),'edit') && ...
                    isprop(handle,'String')
                if isempty(reports{i,2}) || ...
                        ~strcmp(get(ax{6}{i}.XLabel,'String'),get(handle,'Tag'))
                    x0 = eval(get(handle,'String')); 	y0 = plot_val;
                    x = x0;                             y = y0;
                else
                    x = reports{i,2}(:,1);           y = reports{i,2}(:,2);
                    x0 = eval(get(handle,'String')); y0 = plot_val;
                    x(end+1,1) = x0;                 y(end+1,1) = y0;
                    [x,index] = unique(x);           y = y(index);
                end
                delete(findall(ax{6}{i},'Type','line'))
                plot(ax{6}{i},x,y,'b-',x0,y0,'b.','MarkerSize',10)
                xlabel(ax{6}{i},get(handle,'Tag')), grid(ax{6}{i},'on')
                ylabel(ax{6}{i},variable)
                reports{i,2} = [x,y];
                set(gcf,'UserData',reports)
            end
        end
    end
    
    %Estimate Stability
    AC.Cm_CL=AC.x_cg-AC.N0;
    
    %Print Stability Results
    if get(cmp(1),'Value')
        out{1}=sprintf('CG at %.0f%% MAC:\n',AC.x_cg*100);
        if abs(E.DELTA)>delta_max
            out{2}='Exceeded max elevator deflection';
        elseif AC.Cm_CL>0
            out{2}='Aircraft is unstable';
        else
            out{2}=sprintf('Aircraft is %.0f%% stable',-AC.Cm_CL*100);
        end
    else
        out = '';
    end
    set(AERO_Out,'String',out)
    
    %Plot
    [AZ,EL]=view(ax{1});
    if ~exist('choice','var'), choice=''; end
    AID([AZ,EL],0,'plot',choice)
    
elseif strcmp(action,'plot')%%%%%%%%%%%%%%%%%%% PLOT %%%%%%%%%%%%%%%%%%%%%%
    
    %Check Inputs
    if nargin<4, choice=''; end
    
    %Plot Type
    if strcmp(ax{1}.Tag,'Geometry')
        
        %Refresh Plot
        if ~isempty(ax{2}{11}), delete(ax{2}{11}), ax{2}{11} = []; end
        
        %Update Design
        hold(ax{1},'on')
        if get(cmp(1),'Value') %wing
            [ax{2}{1},g] = Plot_Planform(WG,...
                'wing',ax{1},res(2),res(2),angl,choice,ax{2}{1});
            if ~isempty(g), ax{2}{11} = g; end %disposable plot handle
        end
        if get(cmp(2),'Value') %horizontal tail
            [ax{2}{2},g] = Plot_Planform(HT,...
                'ht',ax{1},res(3),res(3),angl,choice,ax{2}{2});
            if ~isempty(g), ax{2}{11} = g; end
        end
        if get(cmp(3),'Value') %vertical tail
            [ax{2}{3},g] = Plot_Planform(VT,...
                'vt',ax{1},res(3),res(3),angl,choice,ax{2}{3});
            if ~isempty(g), ax{2}{11} = g; end
        end
        if get(cmp(4),'Value') %fuselage
            [ax{2}{4},g] = Plot_Body(BD,...
                ax{1},res(1),choice,0,ax{2}{4});
            if ~isempty(g), ax{2}{11} = g; end
        end
        part = {'wing 2','ht 2','vt 2','prop'};
        for n=1:length(NP) %plot additional planforms
            if ~isempty(NP_In{n}) && get(cmp(4+n),'Value')
                p = min([3,n+1]); %p=2,3,3,3
                [ax{2}{4+n},g] = Plot_Planform(NP{n},part{n},...
                    ax{1},res(p),res(p),angl,choice,ax{2}{4+n});
                if ~isempty(g), ax{2}{11} = g; end
            end
        end
        for n=1:length(NB) %plot additional bodies
            if ~isempty(NB_In{n}) && get(cmp(8+n),'Value')
                [ax{2}{8+n},g] = Plot_Body(NB{n},ax{1},...
                    res(1),choice,n,ax{2}{8+n});
                if ~isempty(g), ax{2}{11} = g; end
            end
        end
        
        %Figure Properties
        if ~isempty(ax{6}), axes(ax{1}), end
        colormap(ax{1},ac_color)
        if shade
            shading(ax{1},'interp')     %interpolated shading
            lighting(ax{1},'gouraud')   %smooth airplane mesh
            material(ax{1},'metal')     %apply material
        else
            shading(ax{1},'faceted')    %faceted shading
            lighting(ax{1},'flat')      %visible airplane mesh
            material(ax{1},'default')   %remove material
        end
        if isempty(findall(ax{1},'Type','light'))
            camlight(-15,30), camlight(15,30)
        end
        
        %Image Loaded
        if transparent && ~isempty(ax{4}), transparent = 2; end
        
        %Plot CG if Adjusted
        legend_labels = {}; legend_plt = [];
        if strcmp(choice,'cg') || (transparent && isempty(ax{4}))
            transparent=2; legend_labels{end+1} = 'Center of Gravity';
            if AC.Cm_CL>0, marker='r.'; %unstable
            elseif abs(E.DELTA)>delta_max, marker='y.'; %uncontrollable
            else, marker='g.'; %stable
            end
            ax{2}{11}(end+1) = plot3(ax{1},AERO.XCG,0,AERO.ZCG,marker,'MarkerSize',50);
            legend_plt(end+1) = ax{2}{11}(end);
            ax{2}{11}(end+1) = text(AERO.XCG,0,AERO.ZCG,sprintf('   %.0f%% MAC',AC.x_cg*100));
            
        end
        
        %Plot Neutral Point
        if strcmp(choice,'np') || (transparent && isempty(ax{4}))
            transparent=2; legend_labels{end+1} = 'Neutral Point';
            ax{2}{11}(end+1) = plot3(ax{1},WG.X+WG.xmac+AC.N0*WG.cbar(end),0,AERO.ZCG,'b.','MarkerSize',50);
            legend_plt(end+1) = ax{2}{11}(end);
            ax{2}{11}(end+1) = text(WG.X+WG.xmac+AC.N0*WG.cbar(end),0,AERO.ZCG,sprintf('   %.0f%% MAC',AC.N0*100));
        end
        
        %Legend
        %delete(findall(ax{1},'Type','legend'))
        if ~isempty(legend_labels)
            ax{2}{11}(end+1) = legend(legend_plt,legend_labels,'Location','North');
        end
        
        %Transparency
        if transparent == 2
            set(opt(2),'Tag','cg')
            set(findall(ax{1},'FaceAlpha',1),'FaceAlpha',0.3)
        elseif strcmp(get(opt(2),'Tag'),'cg')
            set(opt(2),'Tag','')
            set(findall(ax{1},'FaceAlpha',0.3),'FaceAlpha',1)
        end
        
    elseif strcmp(ax{1}.Tag, 'Aerodynamics')
        
        %Plot Drag
        view(ax{3},2), delete(findall(ax{3},'Type','line'))
        v_stall = sqrt(AERO.WT(1)/(ATM.D*WG.S(end))); %assume CL_max = 2
        if strcmp(unit,'in'), v_stall=v_stall*12; end
        v_tr = AERO.MACH*ATM.a;
        if 1.2*max(v_tr)/ATM.a>1
            v_max=0.9*ATM.a;
        elseif 1.2*max(v_tr)>v_stall
            v_max=1.2*max(v_tr);
        else
            v_max=2*v_stall;
        end
        v_array = v_stall:v_max;
        Q = 1/2*ATM.D*v_array.^2;
        if strcmp(unit,'in'), Q=Q/144; end %convert from inches
        CL_array = AERO.WT(1)./(Q*WG.S(end));
        if strcmp(unit,'in'), CL_array = CL_array*144;  end
        CDi = WG.K*CL_array.^2;
        D_0 = AC.CD0*Q*WG.S(end);
        D_i = CDi.*Q*WG.S(end);
        D = D_0+D_i; D_tr=interp1(v_array,D,v_tr);
        if kts
            v_array = v_array/1.68781;  v_tr = v_tr/1.68781;
            v_stall = v_stall/1.68781;  v_max = v_max/1.68781;
        end
        plot(ax{3},v_array,D_i,v_array,D_0,v_array,D,v_tr,D_tr,'g*')
        legend(ax{3},'Induced','Profile','Total')
        xlim(ax{3},[v_stall,v_max]), ylim(ax{3},[0,AERO.WT/3])
        drag=sprintf('%.3f + %.3f',AC.CD0,WG.K);
        title(ax{3},['Drag: (C_{D} = ',drag,'C_{L}^{2})'])
        if kts
            xlabel(ax{3},'Velocity (knots)')
        else
            xlabel(ax{3},'Velocity (ft/s)')
        end
        ylabel(ax{3},'Drag (lb)')
        grid(ax{3},'on')
        
        %Plot Aircraft
        axes(ax{1}), hold(ax{1},'on') 	%refresh plot
        if ~isempty(ax{2}{11}), delete(ax{2}{11}), ax{2}{11} = []; end
        
        %Plot Aircraft or Pressure Distribution
        if get(cmp(1),'Value'), ax{2}{1} = Plot_Planform(WG,...
                'wing',ax{1},res(2),res(2),angl,choice,ax{2}{1}); end
        if get(cmp(2),'Value'), ax{2}{2} = Plot_Planform(HT,...
                'ht',ax{1},res(3),res(3),angl,choice,ax{2}{2}); end
        if get(cmp(3),'Value'), ax{2}{3} = Plot_Planform(VT,...
                'vt',ax{1},res(3),res(3),angl,choice,ax{2}{3}); end
        if get(cmp(4),'Value'), ax{2}{4} = Plot_Body(BD,...
                ax{1},res(1),choice,0,ax{2}{4}); end
        part = {'wing 2','ht 2','vt 2','prop'};
        for n=1:length(NP) %plot additional planforms
            if ~isempty(NP_In{n}) && get(cmp(4+n),'Value')
                p = min([3,n+1]); %p=2,3,3,3
                ax{2}{4+n} = Plot_Planform(NP{n},part{n},...
                    ax{1},res(p),res(p),angl,choice,ax{2}{4+n});
            end
        end
        for n=1:length(NB) %plot additional bodies
            if ~isempty(NB_In{n}) && get(cmp(8+n),'Value')
                ax{2}{8+n} = Plot_Body(NB{n},ax{1},...
                    res(1),choice,n,ax{2}{8+n});
            end
        end
        
        %Clear Plots
        delete(findall(ax{1},'Type','line'))
        delete(findall(ax{1},'Type','text'))
        delete(findall(ax{1},'Type','quiver'))
        if ~isempty(Results{3})
            delete(findall(ax{1},'Type','patch'))
        end
        
        %Plot Downwash
        if downwash
            [h,Zw] = Downwash;
            [ax{2}{11},~,WG] = Plot_Planform(WG,'downwash',ax{1},res(2),res(2),[h,Zw]);
        end
        
        %Plot Lift Distribution
        nj = round(res(2)/4);
        if get(cmp(1),'Value') %wing
            [~,~,WG] = Plot_Planform(WG,'lift',ax{1},res(2),nj);
        end
        %             if get(cmp(2),'Value') %horizontal tail
        %                 [~,~,HT] = Plot_Planform(HT,'lift',ax{1},res(2),nj);
        %             end
        
        %Tornado Lift Distribution
        if ~isempty(Results{3}) && get(cmp(1),'Value')
            
            %Plot Distribution
            Y = Results{3}.spanwise{1}.y;
            Cl = Results{3}.spanwise{1}.Cl;
            Cl = Cl*max(WG.spanwise.Cl)/max(Cl); %scale for comparison
            Cl = Cl/WG.spanwise.scale*WG.CHRDR;
            X = ones(length(Y),1)*WG.X+WG.xmac+WG.cbar(end)/4;
            plot3(ax{1},X,Y,WG.Z+Cl,'-r')
            
            %Plot Arrows
            %             ds = 1; color = [0.7,0.3,0];
            %             X = X(1:ds:length(X));
            %             Y = Y(1:ds:length(Y));
            %             Z = WG.Z*ones(length(Y),1);
            %             zero = zeros(length(Y),1);
            %             Cl = Cl(1:ds:length(Cl));
            %             quiver3(ax{1},X,Y,Z,zero,zero,Cl,'color',color,'AutoScale','off')
            
            %Legend
            legend_plt = plot3(ax{1},0,0,0,'--k',0,0,0,'-b',0,0,0,'-r');
            legend(legend_plt,'Ideal Lift Distribution','Prandtl''s Lifting Line','Tornado VLM','Location','North');
            
        else
            
            %Legend
            legend_plt = plot3(ax{1},0,0,0,'--k',0,0,0,'-b');
            legend(legend_plt,'Ideal Lift Distribution','Prandtl''s Lifting Line','Location','North');
            
        end
        
        %Figure Properties
        colormap(ax{1},ac_color)
        if shade
            shading(ax{1},'interp')     %Interpolated shading
            lighting(ax{1},'gouraud')   %Smooth airplane mesh
            material(ax{1},'metal')     %Apply material
        end
        if isempty(findall(ax{1},'Type','light'))
            camlight(-15,30), camlight(15,30)
        end
        
        %         %Plot CG if Adjusted
        %         if strcmp(choice,'cg') || (isempty(Results{3}) && transparent)
        %             transparent=2;
        %             if AC.Cm_CL>0, marker='r.'; %unstable
        %             elseif abs(E.DELTA)>delta_max, marker='y.'; %uncontrollable
        %             else, marker='g.'; %stable
        %             end
        %             plot3(ax{1},AERO.XCG,0,AERO.ZCG,marker,'MarkerSize',50);
        %             text(AERO.XCG,0,AERO.ZCG,...
        %                 sprintf('   %.0f%% MAC',AC.x_cg*100))
        %         end
        %
        %         %Plot Neutral Point
        %         if strcmp(choice,'np') || (isempty(Results{3}) && transparent)
        %             transparent=2;
        %             plot3(ax{1},WG.X+WG.xmac(end)+AC.N0*WG.cbar(end),0,AERO.ZCG,'b.','MarkerSize',50);
        %             text(WG.X+WG.xmac(end)+AC.N0*WG.cbar(end),0,AERO.ZCG,sprintf('   %.0f%% MAC',AC.N0*100));
        %         end
        
        %Transparency
        if transparent
            if ~isempty(Results{3})
                
                %Plot Cp Distribution
                alpha(ax{1},0.1) %make surface plots practically invisible
                colormap(ax{1},parula);
                XYZ = Results{3}.lattice.XYZ; cp = Results{3}.cp;
                fill3(ax{1},XYZ(:,:,1)',XYZ(:,:,2)',XYZ(:,:,3)',cp');
                b = colorbar(ax{1},'West');
                b.Label.String = 'Cp'; b.Label.Rotation = 0;
                set(ax{1},'CLim',[min(cp),max(cp)]) %[min(cp),max(cp)]
                
            else
                set(opt(2),'Tag','cg')
                set(findall(ax{1},'FaceAlpha',1),'FaceAlpha',0.3)
            end
        elseif strcmp(get(opt(2),'Tag'),'cg')
            set(opt(2),'Tag','')
            set(findall(ax{1},'FaceAlpha',0.3),'FaceAlpha',1)
        end
        
    else %Plot stability and lift curve slopes
        
        %Calculate Range of Alphas
        alim=[min([-10,AC.alpha]),max([20,AC.alpha])];
        alphas=linspace(alim(1),alim(2));
        CL=AC.CL0+AC.CLa*alphas;  CL_trim=interp1(alphas,CL,AC.alpha);
        Cma=AC.Cm_CL*AC.CLa;
        Cm=AC.Cm0+Cma*alphas;   Cm_trim=interp1(alphas,Cm,AC.alpha);
        
        %Plot Lift Curve Slope
        CLlim = [-0.5,max([2,1.1*AC.CL])];
        lgnd = {'Cruise','Approximated'};
        if AC.Cm_CL>0, marker='r.'; %unstable
        elseif abs(E.DELTA)>delta_max, marker='y.'; %uncontrollable
        else, marker='g.'; %stable
        end
        if isempty(ax{2}{1})
            ax{2}{1}(1)=plot(ax{1},AC.alpha,CL_trim,marker,'MarkerSize',25);
            ax{2}{1}(2)=plot(ax{1},alphas,CL,'b');
        else
            set(ax{2}{1}(1),'XData',AC.alpha,'YData',CL_trim)
            set(ax{2}{1}(2),'XData',alphas,'YData',CL)
            delete(ax{2}{1}(3:end))
        end
        if ~isempty(Results{1})
            ax{2}{1}(end+1)=plot(ax{1},Results{1}.alpha,Results{1}.cl,'g.-');
            lgnd{end+1} = 'DATCOM';
        end
        if ~isempty(Results{2})
            ax{2}{1}(end+1)=plot(ax{1},Results{2}.alpha,Results{2}.CL,'r.-');
            lgnd{end+1} = 'ASCDM';
        end
        if ~isempty(Results{3})
            ax{2}{1}(end+1)=plot(ax{1},alphas,Results{3}.CL0+Results{3}.CL_a*alphas*pi/180,'c-');
            lgnd{end+1} = 'Tornado';
        end
        if ~isempty(Results{4})
            ax{2}{1}(end+1)=plot(ax{1},alphas,AC.CL0+Results{4}.CLa*alphas*pi/180,'m-');
            lgnd{end+1} = 'AVL';
        end
        ax{2}{1}(end+1)=plot(ax{1},[-100,100],[0,0],'k');
        ax{2}{1}(end+1)=plot(ax{1},[0,0],[-100,100],'k');
        if length(lgnd)>1, legend(ax{1},lgnd), end
        xlim(ax{1},alim), ylim(ax{1},CLlim),
        title(ax{1},'C_L vs. \alpha')
        xlabel(ax{1},'Angle of Attack, \alpha (deg)')
        ylabel(ax{1},'Lift Coefficient, C_L')
        
        %Plot Stability Slope
        Cmval = 1.1*(AC.Cm0+AC.Cma*AC.alpha);
        Cmlim = [min([-.2,Cmval]),max([.4,Cmval])];
        if isempty(ax{2}{2})
            ax{2}{2}(1)=plot(ax{3},AC.alpha,Cm_trim,marker,'MarkerSize',25);
            ax{2}{2}(2)=plot(ax{3},alphas,Cm,'b');
        else
            set(ax{2}{2}(1),'XData',AC.alpha,'YData',Cm_trim)
            set(ax{2}{2}(2),'XData',alphas,'YData',Cm)
            delete(ax{2}{2}(3:end))
        end
        if ~isempty(Results{1})
            ax{2}{2}(end+1)=plot(ax{3},Results{1}.alpha,Results{1}.cm,'g.-');
        end
        if ~isempty(Results{2})
            ax{2}{1}(end+1)=plot(ax{3},Results{2}.alpha,Results{2}.CM,'r.-');
        end
        if ~isempty(Results{3})
            ax{2}{2}(end+1)=plot(ax{3},alphas,Results{3}.Cm0+Results{3}.Cm_a*alphas*pi/180,'c-');
        end
        if ~isempty(Results{4})
            ax{2}{2}(end+1)=plot(ax{3},alphas,AC.Cm0+Results{4}.Cma*alphas*pi/180,'m-');
        end
        ax{2}{2}(end+1)=plot(ax{3},[-100,100],[0,0],'k');
        ax{2}{2}(end+1)=plot(ax{3},[0,0],[-100,100],'k');
        if length(lgnd)>1, legend(ax{3},lgnd), end
        xlim(ax{3},alim), ylim(ax{3},Cmlim)
        title(ax{3},'C_m vs. \alpha')
        xlabel(ax{3},'Angle of Attack, \alpha (deg)')
        ylabel(ax{3},'Moment Coefficient, C_m')
        
    end
    
    %Highlight Unknown Component Weights
    if cg_calc
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
    end
    
elseif strcmp(action,'change_ax')%%%%%%%%%%%%% CHANGE AX %%%%%%%%%%%%%%%%%%
    
    %Adjust Plotting Options
    [Az,El] = view(ax{1});
    if Az==0 && El==90
        vw = 3;
    else
        vw = [Az,El];
    end
    
    %Manual Function Call
    if ischar(handle)
        mode = handle;
    else
        mode = handle.String;
    end
    
    %Reset Axes Handles
    delete([ax{1},ax{3}]), ax{1} = []; ax{3} = [];
    
    %Reset Plot Handles
    ax{2} = cell(1,11);
    
    %Change Plot Type
    if strcmp('Geometry',mode)
        
        %Axis Properties
        ax{1}=axes('Position',[0.3,0.2,0.7,0.6]);
        ax{1}.Tag = 'Geometry';         %Plot type
        camproj(ax{1},'perspective')    %Perspective viewing
        axis(ax{1},'off')               %Set axis visibility off
        view(ax{1},vw)                  %Apply view rotation
        axis(ax{1},'equal')             %Correct aspect ratio
        camva(ax{1},5)              	%Zoom/Turn off stretch-to-fit
        
    elseif strcmp('Stability',mode)
        
        %Stability
        ax{1} = axes('Position',[0.41,0.6,0.5,0.3]);
        grid(ax{1},'on'), hold(ax{1},'on'), ax{1}.Tag = 'Stability';
        ax{3} = axes('Position',[0.41,0.15,0.5,0.3]);
        grid(ax{3},'on'), hold(ax{3},'on')
        
    else
        
        %Axis Properties
        ax{1} = axes('Position',[0.41,0.55,0.5,0.45]);
        ax{1}.Tag = 'Aerodynamics';   	%Plot type
        camproj(ax{1},'perspective')    %Perspective viewing
        axis(ax{1},'off')               %Set axis visibility off
        view(ax{1},vw)                  %Apply view rotations
        axis(ax{1},'equal')             %Correct aspect ratio
        camva(ax{1},5)              	%Zoom/Turn off stretch-to-fit
        ax{3} = axes('Position',[0.41,0.15,0.5,0.3]);
        
    end
    
    %Plot
    if Az==0 && El==90
        AID(3,0,'plot')
    else
        AID([Az,El],0,'plot')
    end
    
elseif strcmp(action,'save')%%%%%%%%%%%%%%%%%% SAVE %%%%%%%%%%%%%%%%%%%%%%%
    
    %Loading Pointer
    set(gcf,'Pointer','watch')
    
    %Retrieve Case ID
    if strcmp(choice,'Save')
        CaseID = get(gcf,'Tag');
        if isempty(CaseID), CaseID='My First Plane'; end
        [fname,pathname] = uiputfile({'*.mat','MATLAB Save File';...
            '*.dat;','DATCOM Input File'},'Choose Save Directory',CaseID);
        if ~fname, set(gcf,'Pointer','arrow'), return; end
        suffix = fname(end-2:end);          fname = fname(1:end-4);
        CaseID = fullfile(pathname,fname);  set(gcf,'Tag',CaseID)
        
        %Write MATLAB Save File
        if strcmp(suffix,'mat')
            plot_cmp = zeros(1,4); cg_data = get(opt(1),'UserData');
            for i=1:length(cmp) %only write selected components
                if cmp(i)
                    if ~get(cmp(i),'Value')
                        if i>8,  NB{i-8} = []; elseif i>4, NP{i-4} = []; end
                    elseif i<=4
                        plot_cmp(i) = 1;
                    end
                end
            end
            %if exist('Models','dir'), end
            %CaseID = fullfile(lib_path,'Models',CaseID);
            save([CaseID,'.mat'],'WG','HT','VT','F','A','E','R','BD','NP',...
                'NB','AERO','plot_cmp','unit','cg_data')
            
        elseif strcmp(suffix,'dat') %Export DATCOM Input File
            
            DATCOM_IO(CaseID,'case',choice,cg_calc,unit);
            comp = 0;   %check if any components have been added
            for n=1:length(NB_In), comp = comp+~isempty(NB_In{n}); end
            for n=1:length(NP_In), comp = comp+~isempty(NP_In{n}); end
            if comp, DATCOM_IO(CaseID,'parts',choice,cg_calc,unit); end
            
        end
        
    end
    
    %Process File in Datcom
    if strcmp(choice,'DATCOM')
        
        %Check for datcomimport (Aerospace Toolbox)
        loadvar = 1;
        if ~exist('datcomimport')
            warndlg({'Aerospace Toolbox function "datcomimport"',...
                'is required to read DATCOM output file.'},...
                'Unable to Load Results')
            loadvar = 0; %set(opt(13),'Checked','off');
        end
        current_path = pwd;
        cd(fullfile(lib_path,'DATCOM')); delete('*.dat') %clean up
        DATCOM_IO('for005.dat','case',choice,cg_calc,unit);
        if ispc %windows
            if check_io
                !Notepad for005.dat
            end
            system('datcom.exe');
            if check_io
                !Notepad for006.dat
            end
            if loadvar
                Results(1)=datcomimport('for006.dat',true);
            end
            cd(current_path)
            if ~isfield(Results{1},'cl')
                waitfor(warndlg('Error running DATCOM, check output'))
            end
            %copyfile('DATCOM/for005.dat',[CaseID,'.dat'])
            
        else    %OSX/Linux
            
            if check_io
                type 'for005.dat'
            end
            setenv('DYLD_LIBRARY_PATH', '/usr/local/bin:/opt/local/lib:')
            system('./datcom.osx');
            if check_io
                type 'for006.dat'
            end
            if loadvar
                Results(1)=datcomimport('for006.dat',true);
            end
            cd(current_path)
            if ~isfield(Results{1},'cl')
                waitfor(warndlg('Error running DATCOM, check output'))
            end
            %copyfile('DATCOM/for005.dat',[CaseID,'.dat'])
        end
        fprintf('\nDATCOM input file written to %s\n',...
            fullfile(lib_path,'DATCOM','for005.dat'))
        
%     elseif strcmp(choice,'ASCDM')
%         
%         global WGPLNF HTPLNF CRPLNF VTPLNF VFPLNF BODY
%         global FLTCON FLAG OPTINS SYNTHS SYMFLP
%         
%         %Re-assign Global Variables
%         WGPLNF = WG; WGPLNF.TYPE=1; WGPLNF.SSPNDD=WG.SSPN;
%         HTPLNF = HT; HTPLNF.TYPE=1; HTPLNF.SSPNDD=WG.SSPN;
%         VTPLNF = VT; VTPLNF.TYPE=1; VTPLNF.SSPNDD=WG.SSPN;
%         
%         %Aero
%         FLTCON = AERO;
%         FLTCON.NALT = length(FLTCON.ALT);
%         FLTCON.NMACH = length(FLTCON.MACH);
%         FLTCON.NALPHA = length(FLTCON.ALSCHD);
%         FLTCON.VINF = FLTCON.MACH;
%         FLTCON.RNNUB = ATM.Re;
%         FLTCON.PINF = ATM.P;
%         FLTCON.TINF = ATM.T;
%         AC = {'DERIV','RAD';'BUILD',0;'DAMP',0;...
%             'NACA',{{'W'},num2str(length(WG.NACA{1})),WG.NACA{1},...
%             num2str(length(WG.NACA{1})),WG.NACA{1};...
%             {'H'},num2str(length(HT.NACA{1})),HT.NACA{1},...
%             num2str(length(HT.NACA{1})),HT.NACA{1};...
%             {'V'},num2str(length(VT.NACA{1})),VT.NACA{1},...
%             num2str(length(VT.NACA{1})),VT.NACA{1}};...
%             'WGSCHR',{};'HTSCHR',{};'VTSCHR',{}};
%         
%         %FLAG and OPTINS
%         FLAG = struct('BD',1,'WG',1,'HT',1,'VT',1,'WB',1,'HB','WBH',...
%             'CR',0,'CB',0,'WBC',0,'VB',1,'WBH',1,'WBV',1,'WBHV',1,...
%             'WBCV',0,'VF',0,'TVT',0,'PROP',0','JET',0,'GRNDEF',0,...
%             'FLAP',0,...
%             'SYMFLP',[0,0,0],'ASYFLP',[0,0,0,0,0],'TAB',[0,0,0,0,0]);
%         OPTINS = struct('ROUGFC',0,'SREF',WG.S(end),...
%             'CBARR',WG.cbar(end),'BLREF',WG.b);
%         
%         %Body
%         BODY = BD; BODY.ELLIP = 1; BODY.BLN = 0; BD.phi = 0;
%         
%         %Synthesis Parameters
%         SYNTHS = AERO;
%         SYNTHS.XW = WG.X; SYNTHS.ZW = WG.Z;
%         SYNTHS.XH = HT.X; SYNTHS.ZH = HT.Z;
%         SYNTHS.XV = VT.X; SYNTHS.ZV = VT.Z;
%         SYNTHS.ALIW = WG.i; SYNTHS.ALIH = HT.i;
%         
%         %SYMFLP
%         SYMFLP = [struct('DELTA',0),struct('DELTA',0)];
%         
%         %Save Planform/Body Data
%         wg = WG; ht = HT; vt = VT; NX = BD.NX;
%         
%         %Run ASCDM Code
%         addpath('ASCDM')
%         cd ASCDM
%         ASCDM
%         cd ..
%         
%         %Repair Global Variables
%         WG = wg; HT = ht; VT = vt;
%         BD.NX = NX; BD.X = BD.X(1:NX)'; BD.R = BD.R(1:NX)';
%         BD.ZU = BD.ZU(1:NX)'; BD.ZL = BD.ZL(1:NX)'; BD.S = BD.S(1:NX)';
%         AC = []; AC.alpha = 0;
%         
%         %Write Stability Coefficients
%         comps = {'W','B','H','V'}; config = [];
%         for i=1:length(comps)
%             if get(cmp(i),'Value'), config(end+1) = comps{i}; end
%         end
%         Results{2}.alpha  = cell2mat(ACOUT(3,2:end));
%         for i=1:size(ACOUT,1)
%             if ~isempty(strfind(ACOUT{i,1},config))
%                 var = ACOUT{i,1}(strfind(ACOUT{i,1},'_')+1:end);
%                 Results{2}.(var) = cell2mat(ACOUT(i,2:end));
%             end
%         end
        
    elseif strcmp(choice,'Tornado')
        
        %Allows for Cursor Change
        pause(0.1)
        
        %Generate Mesh
        prompt = {'Spanwise Nodes','Chordwise Nodes'};
        default = {'10','5'};
        if WG.TWISTA
            prompt{end+1} = 'Twist Linearity';
            default{end+1} = '2';
        end
        if length(WG.DATA)>1
            prompt{end+1} = 'Airfoil Interpolation Linearity';
            default{end+1} = '3';
        end
        mesh = inputdlg(prompt,'Wing Mesh Parameters',1,default);
        if isempty(mesh), set(gcf,'Pointer','arrow'), return; end
        [geo,state] =  Tornado_IO(mesh); 
        
        %0 = Freestream following wake, Tornado method
        %1 = Fixed wake, standard VLM method
        mode = 0;
        
        if check_io
            fieldnames = fields(state);
            if length(fieldnames)==11
                prompt = {'Airspeed (m/s)','Angle of Attack, Alpha (rad), ',...
                    'Sideslip Angle, Beta (rad)','Roll Rate, P (rad/s)',...
                    'Pitch Rate, Q (rad/s)','Yaw Rate, R (rad/s)',...
                    'Alpha_dot, (rad/s)','Beta_dot (rad/s)',...
                    'Altitude (m)','Density (kg/m^3)','Compressibility Correction [0,1]'};
            else
                prompt = fieldnames;
            end
            for i = 1:length(fieldnames)
                state_in{i} = num2str(state.(fieldnames{i}));
            end
            state_out = inputdlg(prompt,'Tornado Inputs',1,state_in);
            if ~isempty(state_out)
                for i = 1:length(fieldnames)
                    state.(fieldnames{i}) = eval(state_out{i});
                end
            end
            state
            method = questdlg('Analysis Method for 3-D Vortex Wake Calculations','VLM Calculation Method',...
                'Freestream Following Wake','Fixed Wake','Freestream Following Wake');
            if strcmp(method,'Fixed Wake')
                mode = 1;
            end
        end
            
        %Generate Lattice
        %addpath('Tornado')
        [lattice,ref]=fLattice_setup2(geo,state,mode);
        if ~strcmp(ax{1}.Tag,'Stability')
            if ~isempty(ax{2}{11}), delete(ax{2}{11}), ax{2}{11} = []; end
            alpha(ax{1},get(opt(2),'UserData'))
            l = plot3(ax{1},lattice.XYZ(:,:,1)',lattice.XYZ(:,:,2)',lattice.XYZ(:,:,3)','k');
            drawnow %plot lattice
        end
        
        %Moments about 25% MAC
        geo.ref_point(1) = ref.mac_pos(1)+ref.C_mac/4;
        
        %Run Inviscid Vortex Lattice Solution
        results = solver(state,geo,lattice);
        if isempty(results) %deleted early
            if ~strcmp(ax{1}.Tag,'Stability')
                delete(l), alpha(ax{1},1), set(opt(2),'Checked','off')
            end
            set(gcf,'Pointer','arrow'), return
        end
        results = coeff_create3(results,lattice,state,ref,geo);
        Results{3} = results;
        Results{3}.CL0 = results.CL-results.CL_a*state.alpha;
        Results{3}.Cm0 = results.Cm-results.Cm_a*state.alpha;
        Results{3}.lattice = lattice;
        
        %Lift Distribution
        for k=1:geo.nwing
            
            y0 = -abs(sum(geo.b(k,:))); %start from negative semi-span
            index = Results{3}.ystation(:,k)~=0;
            y1 = Results{3}.ystation(index,k);
            L = Results{3}.ForcePerMeter(index,k)/4.44822/3.28084^2; %lb/ft
            Cl = L/(WG.S(end)*ATM.Q);
            dy = zeros(length(y1),1);
            for i=1:length(y1)
                dy(i) = y1(i)-y0(i);
                y0(i+1) = y1(i)+dy(i);
            end
            dy = 2*dy;
            Results{3}.spanwise{k}.y = y1;
            Results{3}.spanwise{k}.dy = dy;
            Results{3}.spanwise{k}.Cl = Cl;
            
        end
        
        %Plot Cp Distribution
        if ~strcmp(ax{1}.Tag,'Stability')
            alpha(ax{1},1e-3) %make surface plots practically invisible
            colormap(ax{1},parula);
            h = fill3(ax{1},lattice.XYZ(:,:,1)',lattice.XYZ(:,:,2)',lattice.XYZ(:,:,3)',results.cp');
            b = colorbar(ax{1},'West');
            b.Label.String = 'Cp'; b.Label.Rotation = 0;
            set(ax{1},'CLim',[min(results.cp),max(results.cp)])
        end
        
        %Static Margin
        np = questdlg('Estimate Neutral Point?','Iterate to Find NP');
        if strcmp(np,'Yes')
            [output,~]=fFindstaticmargin(geo,state);
            Results{3}.N0 = output.ac;
            fprintf('Neutral Point at X = %.4f %s\n',output.ac(1),unit)
            fprintf('(written to Results{3}.N0)\n')
            %             if ~strcmp(ax{1}.Tag,'Stability')
            %                 plot3(ax{1},output.ac(1),output.ac(2),output.ac(3),'c.','MarkerSize',50)
            %                 text(output.ac(1),output.ac(2),output.ac(3),...
            %                     sprintf('   %.0f%% MAC',(output.ac(1)-ref.mac_pos(1))/ref.C_mac*100))
            %                 alpha(ax{1},0.3)
            %             end
        end
        
        %analysis set
        %         global control
        %         if ~isempty(Results) && ~isempty(Results{3})
        %             control(1,end+1) = A.DELTAR;
        %             control(2,end) = Results{3}.CL;
        %             control(3,end) = Results{3}.Cl;
        %             control(4,end) = Results{3}.Cm;
        %             control(5,end) = Results{3}.Cn;
        %         end
        
        if check_io
            out = Results{3};
            assignin('base','out',out)
            out
        end
        
        %Transparency
        if strcmp(get(opt(2),'Checked'),'off')
            alpha(ax{1},1)
        else
            alpha(ax{1},get(opt(2),'UserData'))
        end
        
        %Clear Plots
        if ~strcmp(ax{1}.Tag,'Stability')
            delete(l) %delete lattice plot
            delete(h) %delete fill plot
            delete(b) %delete colormap
        end
        
    elseif strcmp(choice,'AVL')
        
        %Generate Mesh
        prompt = {'Spanwise Nodes','Chordwise Nodes'};
        default = {'10','10'};
        if WG.TWISTA
            prompt{end+1} = 'Twist Linearity';
            default{end+1} = '1';
        end
        if length(WG.DATA)>1
            prompt{end+1} = 'Airfoil Interpolation Linearity';
            default{end+1} = '1';
        end
        mesh = inputdlg(prompt,'Wing Mesh Parameters',1,default);
        if isempty(mesh), set(gcf,'Pointer','arrow'), return; end
        [geo,state] =  Tornado_IO(mesh); assignin('base','geo',geo)
        AVL_path = AVL_IO(mesh,geo,state,check_io);
        
        %addpath('AVL')
        Results{4} = parseST(fullfile(AVL_path,'geometry.st'));
        
        %         sb = parseSB(fullfile(path,'geometry.sb'));
        %         f = fieldnames(sb);
        %         for i=1:length(f), Results{4}.(f{i}) = sb.(f{i}); end
        
    end
    
    %Reset Pointer
    set(gcf,'Pointer','arrow')
    
    %Update
    AID(0,0,'update')
    
    elseif strcmp(action,'sim')%%%%%%%%%%%%%%%%%% SIMULINK %%%%%%%%%%%%%%%%%%%%
    
        %Write stability/control derivatives to workspace
        sim = questdlg('Send to Flight Simulator?');
        if strcmp(sim,'Yes')
    
            if ~isempty(Results)
                Input_Sim(Results{1},AERO,ATM,AC,WG,A,E,R)
                system('/Applications/FlightGear.app/Contents/MacOS/fgfs')
            end
    
        else
    
            %Back to Main Window
            AID(0,0,'update')
    
        end
    
end
end

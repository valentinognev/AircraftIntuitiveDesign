function Viz(handle,~,i)%%%%%%%%%%%%%%%%% TOGGLE VISIBILITY %%%%%%%%%%%%%%%
global ax opt cmp WG_In HT_In VT_In BD_In F_In A_In E_In R_In ...
    NP_In NB_In AERO_In
if ~isprop(handle,'Value')
    toggle=handle; set(cmp(i),'Value',toggle)
else
    toggle=handle.Value; 
end
if toggle
    enable = 'on';
else
    enable = 'off';
end

%Enable/Disble Component
set(nonzeros(ax{2}{i}),'Visible',enable)
switch i
    case 1
        set(WG_In,'Enable',enable)
        set(F_In,'Enable',enable)
        set(A_In,'Enable',enable)
       	if strcmp(get(opt(8),'Checked'),'on') %turn off trim mode
            set(opt(8),'Checked','off')
        end
        set(AERO_In(9:10),'Enable',enable)
    case 2 %htail
        set(HT_In,'Enable',enable)
        set(E_In,'Enable',enable)
       	if strcmp(get(opt(8),'Checked'),'on') %turn off trim mode
            set(opt(8),'Checked','off')
        end
        set(AERO_In(11),'Enable',enable)
    case 3 %vtail
        set(VT_In,'Enable',enable)
        set(R_In,'Enable',enable)
   	case 4, set(BD_In,'Enable',enable) %fuselage
    case {5,6,7,8}, set(NP_In{i-4},'Enable',enable) %added planform
    case {9,10}
        set(NB_In{i-8}(:,1:7),'Enable',enable)    	%added body
        set(NB_In{i-8}(1,8:end),'Enable',enable)    %added body
end

%Update
AID(0,0,'update')

end

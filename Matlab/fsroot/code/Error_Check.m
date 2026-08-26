%Error Check Input Values (planforms and control surfaces)
function Error_Check(PT,PT_In,mn,mx)
global WG_In WG HT_In HT VT_In VT BD_In BD AERO_In AERO ... %needed by eval
    AC F_In F A_In A E_In E R_In R NP_In NP NB_In NB

%Check for Input Errors
n = length(mn); m = length(PT_In);
error = zeros(length(PT),n);
for i=1:length(PT)
    for j=1:m
        if ~isnumeric(mn{j}), mn{j} = PT.(mn{j}); end
        if ~isnumeric(mx{j}), mx{j} = PT.(mx{j}); end 
     	val = eval(get(PT_In(j),'String'));
        if length(val)==1 
            error(i,j) = val<mn{j};
            if ~error(i,j), error(i,j) = (val>mx{j})*2; end
        end
    end
end

[i,j] = find(error); 
if length(i)>1, i = i(1); end
if length(j)>1, j = j(1); end
if error(i,j)==1      %min (1)
	set(PT_In(j),'String',mn{j})
elseif error(i,j)==2  %max (2)
    set(PT_In(j),'String',mx{j})
end

end
function PT=Geometry(PT,angl,type)
if nargin<3, type = ''; end

%Account for Span-wise Break
if PT.CHRDBP && PT.SSPNOP 

    %Given Dimensions
    PT.b=PT.SSPN*2;                                 %Span
    cr = PT.CHRDR; cb = PT.CHRDBP; ct = PT.CHRDTP;  %Chord Lengths
    
    %Inboard Section
    TR_i = cb/cr; 
    cbar_i = 2/3*cr*(1+TR_i+TR_i^2)/(1+TR_i);  
    b_i = 2*PT.SSPNOP;
    S_i = (cr+cb)/2*b_i;     
    AR_i = b_i^2/S_i;
    swp_i = atand(tand(PT.SAVSI)-4*(-PT.CHSTAT)*(1-TR_i)/(AR_i*(1+TR_i)));
    
    %Outboard Section
    TR_o = ct/cb;
    cbar_o = 2/3*cb*(1+TR_o+TR_o^2)/(1+TR_o);   
    b_o = 2*(PT.SSPN-PT.SSPNOP);
    S_o = (cb+ct)/2*b_o;
    AR_o = b_o^2/S_o;
    swp_o = atand(tand(PT.SAVSO)-4*(-PT.CHSTAT)*(1-TR_o)/(AR_o*(1+TR_o)));
    
    %Weighted Average of Aerodynamic Chords
    PT.S = [S_i, S_o, S_i+S_o];                     %Total Planform Area
    PT.AR = [AR_i, AR_o, PT.b^2/PT.S(end)];         %Aspect Ratio
    PT.cbar = [cbar_i, cbar_o, ...
        (cbar_i*S_i+cbar_o*S_o)/PT.S(end)];       	%Mean Aerodynamic Chord

    %Calculate Equivalent Single Taper Ratio
    k = 3*PT.b*PT.cbar(end)/(4*PT.S(end)); 
    a = 1-k; b = 1-2*k; c = 1-k;
    if cbar_o>cbar_i                   
        PT.TR = [TR_i, TR_o, (-b+sqrt(b^2-4*a*c))/(2*a)];         
    else
        PT.TR = [TR_i, TR_o, (-b-sqrt(b^2-4*a*c))/(2*a)];    
    end

    %Sweep and Dihedral
    swp = [swp_i, swp_o, (swp_i*b_i+swp_o*b_o)/PT.b];
    PT.gamma = (PT.DHDADI*b_i+PT.DHDADO*b_o)/PT.b;
    
    %Location of Tip
    PT.Xbrk=PT.X+b_i/2*tand(swp_i);
    PT.Xtip=PT.Xbrk+b_o/2*tand(swp_o);
    if angl
        if strcmp(type,'v')
            PT.Ybrk=PT.Z+b_i/2*cosd(PT.DHDADI);
            PT.Zbrk=PT.Y+b_i/2*sind(PT.DHDADI);
        else
            PT.Ybrk=PT.Y+b_i/2*cosd(PT.DHDADI);
            PT.Zbrk=PT.Z+b_i/2*sind(PT.DHDADI);
        end
        PT.Ytip=PT.Ybrk+b_o/2*cosd(PT.DHDADO);
        PT.Ztip=PT.Zbrk+b_o/2*sind(PT.DHDADO);
    else
        if strcmp(type,'v')
            PT.Zbrk=PT.Y+b_i/2*tand(PT.DHDADI);
        else
            PT.Zbrk=PT.Z+b_i/2*tand(PT.DHDADI);
        end
        PT.Ybrk=PT.SSPNOP; PT.Ytip=PT.SSPN;
        PT.Ztip=PT.Zbrk+b_o/2*tand(PT.DHDADO);
    end
    
else %Given Single, Linear Taper
    
    %MAC, Taper Ratio, and Aspect Ratio
    PT.b=PT.SSPN*2;
    PT.cbar=(PT.CHRDR+PT.CHRDTP)/2;                 %Mean Aerodynamic Chord
    PT.TR=PT.CHRDTP/PT.CHRDR;                       %Taper Ratio
    PT.S=PT.b/2*PT.CHRDR*(1+PT.TR);                 %Span
    PT.AR=PT.b^2/PT.S;                              %Aspect Ratio

    %Sweep and Dihedral
    swp=atand(tand(PT.SAVSI)-4*(0-PT.CHSTAT)*(1-PT.TR)/(PT.AR*(1+PT.TR)));
    PT.gamma=PT.DHDADI;
    
    %Location of Tip
    PT.Xtip=PT.X+PT.SSPN*tand(swp);
    if angl
        if strcmp(type,'v') %vertical
            PT.Xbrk=PT.X; PT.Ybrk=PT.Z; PT.Zbrk=PT.Y;
            PT.Ytip=PT.Z+PT.SSPN*cosd(PT.DHDADI);
            PT.Ztip=PT.Y+PT.SSPN*sind(PT.DHDADI);
        else %horizontal
            PT.Xbrk=PT.X; PT.Ybrk=PT.Y; PT.Zbrk=PT.Z;
            PT.Ytip=PT.Y+PT.SSPN*cosd(PT.DHDADI);
            PT.Ztip=PT.Z+PT.SSPN*sind(PT.DHDADI);
        end
    else
        if strcmp(type,'v') %vertical
            PT.Xbrk=PT.X; PT.Zbrk=PT.Y;
            PT.Ztip=PT.Y+PT.SSPN*tand(PT.DHDADI);
        else %horizontal
            PT.Xbrk=PT.X; PT.Zbrk=PT.Z;
            PT.Ztip=PT.Z+PT.SSPN*tand(PT.DHDADI);
        end
    end
end

%Sweep Calculations 
%atand(tand(swp)-4*(station-PT.CHSTAT)*(1-PT.TR)/(PT.AR*(1+PT.TR)))
PT.swp = zeros(4,length(swp));
PT.swp(1,:)=real(swp); %1.) LE  2.) 0.25c  3.) 0.5c  4.) TE
PT.swp(2,:)=real(atand(tand(swp)-4*(0.25)*(1-PT.TR)./(PT.AR.*(1+PT.TR))));
PT.swp(3,:)=real(atand(tand(swp)-4*(0.5)*(1-PT.TR)./(PT.AR.*(1+PT.TR))));
PT.swp(4,:)=real(atand(tand(swp)-4*(1)*(1-PT.TR)./(PT.AR.*(1+PT.TR))));
    
%Location of Mean Aerodynamic Chord (MAC)                       
PT.ymac=PT.b/6*(1+2*PT.TR(end))/(1+PT.TR(end));     %Y-Position of MAC
if strcmp(type,'v'), PT.S = PT.S/2; PT.b=PT.b/2; PT.ymac=PT.ymac*2; end %VT
PT.xmac=PT.ymac*tand(PT.swp(1,end));            	%X-Position of MAC LE

end
function Body_Stability(choice)
global AERO BD WG HT AC

if strcmp(choice,'Gilruth_White')
    
    %Rename Variables
    L=BD.X(end);	    %Fuselage Length (ft)
    l=WG.X+WG.CHRDR/4;  %Nose -> 25%cr of wing (ft)
    w=max(BD.R)*2;      %Max Fuselage Width (ft)
    
    %Gilruth & White's Correction Factor
    K=0.002322*exp(5.037*l/L);
    
    %Stability Slope
    BD.Cm0=0;
    BD.Cma=K*w^2*L/(WG.S(end)*WG.cbar(end));
    
else %Multhopp
    
    %Break into Sections
    le=find((BD.X-WG.X)>0,1,'first');
    te=find((BD.X-(WG.X+WG.CHRDR))<0,1,'last');
    if te<le, te = le; end
    cr_exp=BD.X(te)-BD.X(le);
    fwd=1:le-1; aft=te:BD.NX-1;
    
    %Error Check
   	if isempty(fwd)||isempty(aft), Body_Stability('Gilruth_White'), return, end
    
    %Determine Segment Lengths and Widths
    dx=BD.X(2:end)-BD.X(1:end-1);
    x1=BD.X(le)-BD.X(fwd)-dx(fwd)/2;
    x2=BD.X(aft)-dx(aft-1)/2-BD.X(te);
    wf=BD.R(2:end)+BD.R(1:end-1);
    la=BD.X(end)-BD.X(te);
    
    %Estimate Upwash
    de_da(fwd(1:end-1))=0.175*(x1(1:end-1)/cr_exp).^(-1.341);
    de_da(fwd(end))=0.754*(dx(fwd(end))/cr_exp).^(-0.793);
    if isfield(AC,'a'), de_da=de_da*AC.a/0.0785; end
    db_da1=1+de_da;
    
    %Estimate Downwash
    de_da=HT.dwash;
    db_da2=x2/la*(1-de_da);
    
    %Determine Stability Slope
    db_da=[db_da1,db_da2];
    wf=[wf(fwd),wf(aft)];
    dx=[dx(fwd),dx(aft)];
    BD.Cma=pi^2/(180*2*WG.S(end)*WG.cbar(end))*sum(wf.^2.*db_da.*dx);
    
    %Monk's Apparent Mass Factor (Figure 5.4)
    fineness=4:2:20;
    delta_K=[0.78,0.86,0.91,0.94,0.955,0.965,0.97,0.973,0.975];
    am_poly=polyfit(fineness,delta_K,4);
    BD.dk=polyval(am_poly,BD.X(end)/(2*max(BD.R)));
    
    %Compressibility Effects (Figure 4.1.4.1-6)
    mach=0.2:0.1:0.9;
    delta_CM=[1,1.01,1.03,1.07,1.12,1.2,1.29,1.44];
    cm_poly=polyfit(mach,delta_CM,2);
    dm=polyval(cm_poly,AERO.MACH(1));

    %Determine Moment
    ZC=(BD.ZU+BD.ZL)/2; dZC=ZC(2:end)-ZC(1:end-1);
    dZC=[dZC(fwd),dZC(aft)];
    aw=(WG.alpha0L(1)+WG.alpha0L(1))/2-WG.i;
    ib=-atand(dZC./dx);
    Cm0=BD.dk/(36.5*WG.S(end)*WG.cbar(end))*sum(wf.^2.*(aw+ib).*dx)*dm;
    BD.Cm0 = Cm0 - BD.Cma*aw; %Cm0 fix (5.29 in Greiner's notes)
    
end
end


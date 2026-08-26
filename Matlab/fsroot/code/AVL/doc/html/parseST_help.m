%% parseST
% Parse the data from a file containing the output of AVL's ST command
%
%% Syntax
% parseST(filename)
%
%% Description
% parseST and the other functions detailed here get a filename as an
% argument.  The file should contain the data dumped by AVL using the
% ST menu.
%
%% Example

myST = parseST('../sampleData/plane1690.st');

%Access any data field like this:
myST.CLa

%% See also 
% <parseSB_help.html |parseSB|>, <parseSF_help.html |parseSF|>,
% <parseConfig_help.html |parseConfig|>,
% <parseRunCaseHeader_help.html |parseRunCaseHeader|>, 
% <parseRunCaseFile_help.html |parseRunCaseFile|>. 
%
% _Copyright 2012 Joseph Moster_
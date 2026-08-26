%% parseSB
% Parse the data from a file containing the output of AVL's SB command
%
%% Syntax
% parseSB(filename)
%
%% Description
% desc...

%% Example
%parseSB similar to parseST but for SB files
mySB = parseSB('../sampleData/plane2243.sb');

%Access any data field like this:
mySB.CXu

%% See also 
% <parseST_help.html |parseST|>, <parseSF_help.html |parseSF|>,
% <parseConfig_help.html |parseConfig|>,
% <parseRunCaseHeader_help.html |parseRunCaseHeader|>, 
% <parseRunCaseFile_help.html |parseRunCaseFile|>
%
% _Copyright 2012 Joseph Moster_
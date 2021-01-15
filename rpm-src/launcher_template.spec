Name: <<PROJECT>>
Version: <<MAJOR>>.<<MINOR>>.<<PATCH>>
Release: 1%{?dist}
Summary: EPI2ME-Labs Server Manager
License: Mozilla Public License Version 2.0
AutoReqProv: no

%global _localbindir %{_exec_prefix}/local/bin

%description
EPI2ME-Labs Server Manager

%install
echo "##########"%{_localbindir}
echo "##########"%{_bindir}
<<INSTALL_LIST>>

%files
<<FILES_LIST>>

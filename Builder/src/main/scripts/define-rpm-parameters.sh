#!/bin/bash

if [ "$#" -ne 4 ] ; then
   echo "Script requires 4 arguments to execute:"
   echo -e "\t-path to additional ruby lib"
   echo -e "\t-path to puppet spec file"
   echo -e "\t-rpm version for POM"
   echo -e "\t-R state for rpm"
   exit 1
else
   ruby_path=$1
   spec_path=$2
   rpm_version=$3
   r_state=$4
fi

# Update path to ruby libraries which are required to build puppet
perl -pi.bak -e "s#\<ruby.path\>#${ruby_path}#" SPEC/${spec_path}
# Set package version taken from integration pom into puppet.spec file
perl -pi.bak -e "s#\<rpm.version\>#${rpm_version}#" SPEC/${spec_path}
# Set package version taken from integration pom into puppet.spec file
perl -pi.bak -e "s#\<ericsson.rstate\>#${r_state}#" SPEC/${spec_path}

#Build puppet and puppet-server RPMs based on spec file
#rpmbuild --define "_topdir %(pwd)/" --define "_builddir %{_topdir}" --define "_rpmdir %{_topdir}/RPM" \
#--define "_specdir %{_topdir}/SPEC" --define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
#--define "_sourcedir %{_topdir}/SOURCES" --define "_localstatedir /var" -bb SPEC/${spec_path}

rpmbuild --define "_topdir %(pwd)/" --define "_builddir %{_topdir}" --define "_rpmdir %{_topdir}/RPM" \
--define "_specdir %{_topdir}/SPEC" --define '_rpmfilename %%{NAME}-%%{VERSION}.%%{ARCH}.rpm' \
--define "_sourcedir %{_topdir}/SOURCES" --define "_localstatedir /var" --define "dist .el7" --define "rhel 7" -bb SPEC/${spec_path}

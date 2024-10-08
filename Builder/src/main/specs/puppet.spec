# Augeas and SELinux requirements may be disabled at build time by passing
# --without augeas and/or --without selinux to rpmbuild or mock

# Fedora 17 ships with ruby 1.9, RHEL 7 with ruby 2.0, which use vendorlibdir instead
# of sitelibdir. Adjust our target if installing on f17 or rhel7.
%if 0%{?fedora} >= 17 || 0%{?rhel} >= 7 || 0%{?amzn} >= 1
%global puppet_libdir   %(ruby -rrbconfig -e 'puts RbConfig::CONFIG["vendorlibdir"]')
%else
%global puppet_libdir   %(ruby -rrbconfig -e 'puts RbConfig::CONFIG["sitelibdir"]')
%endif

%if 0%{?fedora} >= 17 || 0%{?rhel} >= 7
%global _with_systemd 1
%else
%global _with_systemd 0
%endif

# VERSION is subbed out during rake srpm process
%global realversion 3.8.7
%global rpmversion 3.8.7

%global confdir ext/redhat
%global pending_upgrade_path %{_localstatedir}/lib/rpm-state/puppet
%global pending_upgrade_file %{pending_upgrade_path}/upgrade_pending

Name:           puppet
Version:        %{rpmversion}
Release:        1%{?dist}
Vendor:         %{?_host_vendor}
Summary:        A network tool for managing many disparate systems
License:        ASL 2.0
URL:            http://puppetlabs.com
Source0:        http://puppetlabs.com/downloads/%{name}/%{name}-%{realversion}.tar.gz

Group:          System Environment/Base

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  facter >= 1:1.7.0
# Puppet 3.x drops ruby 1.8.5 support and adds ruby 1.9 support
BuildRequires:  ruby >= 1.8.7
BuildRequires:  hiera >= 1.0.0
BuildArch:      noarch
Requires:       ruby >= 1.8
Requires:       ruby-shadow
Requires:       rubygem-json

# Pull in ruby selinux bindings where available
%if 0%{?fedora} || 0%{?rhel} >= 6
%{!?_without_selinux:Requires: ruby(selinux), libselinux-utils}
%else
%if ( 0%{?rhel} && 0%{?rhel} == 5 ) || 0%{?amzn} >= 1
%{!?_without_selinux:Requires: libselinux-ruby, libselinux-utils}
%endif
%endif

Requires:       facter >= 1:1.7.0
# Puppet 3.x drops ruby 1.8.5 support and adds ruby 1.9 support
# Ruby 1.8.7 available for el5 at: yum.puppetlabs.com/el/5/devel/$ARCH
Requires:       ruby >= 1.8.7
Requires:       hiera >= 1.0.0
Obsoletes:      hiera-puppet < 1.0.0
Provides:       hiera-puppet >= 1.0.0
%{!?_without_augeas:Requires: ruby-augeas}

# Required for %%pre
Requires:       shadow-utils

%if 0%{?_with_systemd}
# Required for %%post, %%preun, %%postun
Requires:       systemd
%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
BuildRequires:  systemd
%else
BuildRequires:  systemd-units
%endif
%else
# Required for %%post and %%preun
Requires:       chkconfig
# Required for %%preun and %%postun
Requires:       initscripts
%endif

%description
Puppet lets you centrally manage every important aspect of your system using a
cross-platform specification language that manages all the separate elements
normally aggregated in different files, like users, cron jobs, and hosts,
along with obviously discrete elements like packages, services, and files.

%package server
Group:          System Environment/Base
Summary:        Server for the puppet system management tool
Requires:       puppet = %{version}-%{release}
# chkconfig (%%post, %%preun) and initscripts (%%preun %%postun) are required for non systemd
# and systemd (%%post, %%preun, and %%postun) are required for systems with systemd as default
# They come along transitively with puppet-%{version}-%{release}.

%description server
Provides the central puppet server daemon which provides manifests to clients.
The server can also function as a certificate authority and file server.

%prep
%setup -q -n %{name}-%{realversion}


%build
for f in external/nagios.rb relationship.rb; do
  sed -i -e '1d' lib/puppet/$f
done

find examples/ -type f | xargs --no-run-if-empty chmod a-x

%install
rm -rf %{buildroot}
ruby install.rb --destdir=%{buildroot} --quick --no-rdoc --sitelibdir=%{puppet_libdir}

install -d -m0755 %{buildroot}%{_sysconfdir}/puppet/environments/example_env/manifests
install -d -m0755 %{buildroot}%{_sysconfdir}/puppet/environments/example_env/modules
install -d -m0755 %{buildroot}%{_sysconfdir}/puppet/manifests
install -d -m0755 %{buildroot}%{_datadir}/%{name}/modules
install -d -m0755 %{buildroot}%{_localstatedir}/lib/puppet
install -d -m0755 %{buildroot}%{_localstatedir}/lib/puppet/state
install -d -m0755 %{buildroot}%{_localstatedir}/lib/puppet/reports
install -d -m0755 %{buildroot}%{_localstatedir}/run/puppet

# As per redhat bz #495096
install -d -m0750 %{buildroot}%{_localstatedir}/log/puppet

%if 0%{?_with_systemd}
# Systemd for fedora >= 17 or el 7
%{__install} -d -m0755  %{buildroot}%{_unitdir}
install -Dp -m0644 ext/systemd/puppet.service %{buildroot}%{_unitdir}/puppet.service
ln -s %{_unitdir}/puppet.service %{buildroot}%{_unitdir}/puppetagent.service
install -Dp -m0644 ext/systemd/puppetmaster.service %{buildroot}%{_unitdir}/puppetmaster.service
%else
# Otherwise init.d for fedora < 17 or el 5, 6
install -Dp -m0644 %{confdir}/client.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/puppet
install -Dp -m0755 %{confdir}/client.init %{buildroot}%{_initrddir}/puppet
install -Dp -m0644 %{confdir}/server.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/puppetmaster
install -Dp -m0755 %{confdir}/server.init %{buildroot}%{_initrddir}/puppetmaster
install -Dp -m0755 %{confdir}/queue.init %{buildroot}%{_initrddir}/puppetqueue
%endif

install -Dp -m0644 %{confdir}/fileserver.conf %{buildroot}%{_sysconfdir}/puppet/fileserver.conf
install -Dp -m0644 %{confdir}/puppet.conf %{buildroot}%{_sysconfdir}/puppet/puppet.conf
install -Dp -m0644 %{confdir}/logrotate %{buildroot}%{_sysconfdir}/logrotate.d/puppet
install -Dp -m0644 ext/README.environment %{buildroot}%{_sysconfdir}/puppet/environments/example_env/README.environment

# Install the ext/ directory to %%{_datadir}/%%{name}
install -d %{buildroot}%{_datadir}/%{name}
cp -a ext/ %{buildroot}%{_datadir}/%{name}
# emacs and vim bits are installed elsewhere
rm -rf %{buildroot}%{_datadir}/%{name}/ext/{emacs,vim}
# remove misc packaging artifacts not applicable to rpms
rm -rf %{buildroot}%{_datadir}/%{name}/ext/{gentoo,freebsd,solaris,suse,windows,osx,ips,debian}
rm -f %{buildroot}%{_datadir}/%{name}/ext/redhat/*.init
rm -f %{buildroot}%{_datadir}/%{name}/ext/{build_defaults.yaml,project_data.yaml}

# Rpmlint fixup
chmod 755 %{buildroot}%{_datadir}/%{name}/ext/regexp_nodes/regexp_nodes.rb
chmod 755 %{buildroot}%{_datadir}/%{name}/ext/puppet-load.rb

# Install emacs mode files
emacsdir=%{buildroot}%{_datadir}/emacs/site-lisp
install -Dp -m0644 ext/emacs/puppet-mode.el $emacsdir/puppet-mode.el
install -Dp -m0644 ext/emacs/puppet-mode-init.el \
    $emacsdir/site-start.d/puppet-mode-init.el

# Install vim syntax files
vimdir=%{buildroot}%{_datadir}/vim/vimfiles
install -Dp -m0644 ext/vim/ftdetect/puppet.vim $vimdir/ftdetect/puppet.vim
install -Dp -m0644 ext/vim/syntax/puppet.vim $vimdir/syntax/puppet.vim

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
# Setup tmpfiles.d config
mkdir -p %{buildroot}%{_sysconfdir}/tmpfiles.d
echo "D /var/run/%{name} 0755 %{name} %{name} -" > \
    %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf
%endif

# Create puppet modules directory for puppet module tool
mkdir -p %{buildroot}%{_sysconfdir}/%{name}/modules

%files
%defattr(-, root, root, 0755)
%doc LICENSE README.md examples
%{_bindir}/puppet
%{_bindir}/extlookup2hiera
%{puppet_libdir}/*
%if 0%{?_with_systemd}
%{_unitdir}/puppet.service
%{_unitdir}/puppetagent.service
%else
%{_initrddir}/puppet
%config(noreplace) %{_sysconfdir}/sysconfig/puppet
%endif
%dir %{_sysconfdir}/puppet
%dir %{_sysconfdir}/%{name}/modules
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%endif
%config(noreplace) %{_sysconfdir}/puppet/puppet.conf
%config(noreplace) %{_sysconfdir}/puppet/auth.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/puppet
# We don't want to require emacs or vim, so we need to own these dirs
%{_datadir}/emacs
%{_datadir}/vim
%{_datadir}/%{name}
# man pages
%{_mandir}/man5/puppet.conf.5.gz
%{_mandir}/man8/puppet.8.gz
%{_mandir}/man8/puppet-agent.8.gz
%{_mandir}/man8/puppet-apply.8.gz
%{_mandir}/man8/puppet-catalog.8.gz
%{_mandir}/man8/puppet-describe.8.gz
%{_mandir}/man8/puppet-ca.8.gz
%{_mandir}/man8/puppet-cert.8.gz
%{_mandir}/man8/puppet-certificate.8.gz
%{_mandir}/man8/puppet-certificate_request.8.gz
%{_mandir}/man8/puppet-certificate_revocation_list.8.gz
%{_mandir}/man8/puppet-config.8.gz
%{_mandir}/man8/puppet-device.8.gz
%{_mandir}/man8/puppet-doc.8.gz
%{_mandir}/man8/puppet-facts.8.gz
%{_mandir}/man8/puppet-file.8.gz
%{_mandir}/man8/puppet-filebucket.8.gz
%{_mandir}/man8/puppet-help.8.gz
%{_mandir}/man8/puppet-inspect.8.gz
%{_mandir}/man8/puppet-instrumentation_data.8.gz
%{_mandir}/man8/puppet-instrumentation_listener.8.gz
%{_mandir}/man8/puppet-instrumentation_probe.8.gz
%{_mandir}/man8/puppet-key.8.gz
%{_mandir}/man8/puppet-kick.8.gz
%{_mandir}/man8/puppet-man.8.gz
%{_mandir}/man8/puppet-module.8.gz
%{_mandir}/man8/puppet-node.8.gz
%{_mandir}/man8/puppet-parser.8.gz
%{_mandir}/man8/puppet-plugin.8.gz
%{_mandir}/man8/puppet-queue.8.gz
%{_mandir}/man8/puppet-report.8.gz
%{_mandir}/man8/puppet-resource.8.gz
%{_mandir}/man8/puppet-resource_type.8.gz
%{_mandir}/man8/puppet-secret_agent.8.gz
%{_mandir}/man8/puppet-status.8.gz
%{_mandir}/man8/extlookup2hiera.8.gz
# These need to be owned by puppet so the server can
# write to them. The separate %defattr's are required
# to work around RH Bugzilla 681540
%defattr(-, puppet, puppet, 0755)
%{_localstatedir}/run/puppet
%defattr(-, puppet, puppet, 0750)
%{_localstatedir}/log/puppet
%{_localstatedir}/lib/puppet
%{_localstatedir}/lib/puppet/state
%{_localstatedir}/lib/puppet/reports
# Return the default attributes to 0755 to
# prevent incorrect permission assignment on EL6
%defattr(-, root, root, 0755)


%files server
%defattr(-, root, root, 0755)
%if 0%{?_with_systemd}
%{_unitdir}/puppetmaster.service
%else
%{_initrddir}/puppetmaster
%{_initrddir}/puppetqueue
%config(noreplace) %{_sysconfdir}/sysconfig/puppetmaster
%endif
%config(noreplace) %{_sysconfdir}/puppet/fileserver.conf
%dir %{_sysconfdir}/puppet/manifests
%dir %{_sysconfdir}/puppet/environments
%dir %{_sysconfdir}/puppet/environments/example_env
%dir %{_sysconfdir}/puppet/environments/example_env/manifests
%dir %{_sysconfdir}/puppet/environments/example_env/modules
%{_sysconfdir}/puppet/environments/example_env/README.environment
%{_mandir}/man8/puppet-ca.8.gz
%{_mandir}/man8/puppet-master.8.gz

# Fixed uid/gid were assigned in bz 472073 (Fedora), 471918 (RHEL-5),
# and 471919 (RHEL-4)
%pre
getent group puppet &>/dev/null || groupadd -r puppet -g 52 &>/dev/null
getent passwd puppet &>/dev/null || \
useradd -r -u 52 -g puppet -d %{_localstatedir}/lib/puppet -s /sbin/nologin \
    -c "Puppet" puppet &>/dev/null
# ensure that old setups have the right puppet home dir
if [ $1 -gt 1 ] ; then
  usermod -d %{_localstatedir}/lib/puppet puppet &>/dev/null
fi
exit 0

%post
%if 0%{?_with_systemd}
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ "$1" -ge 1 ]; then
  # The pidfile changed from 0.25.x to 2.6.x, handle upgrades without leaving
  # the old process running.
  oldpid="%{_localstatedir}/run/puppet/puppetd.pid"
  newpid="%{_localstatedir}/run/puppet/agent.pid"
  if [ -s "$oldpid" -a ! -s "$newpid" ]; then
    (kill $(< "$oldpid") && rm -f "$oldpid" && \
      /bin/systemctl start puppet.service) >/dev/null 2>&1 || :
  fi
fi

# TORF-574690 - Ensure that puppet CRL certs are recreated
if [ -f /var/lib/puppet/ssl/ca/ca_crl.pem ]
then
  if [ $(/usr/bin/expr $(/usr/bin/openssl crl -noout -nextupdate -in /var/lib/puppet/ssl/ca/ca_crl.pem | /usr/bin/awk '{ print $4 }') - $(/usr/bin/date +%Y)) -lt 6 ]
  then
      echo "Removing CRL certs from lms..."
      /usr/bin/puppet certificate_revocation_list destroy arg &> /dev/null
      /usr/bin/puppet certificate_revocation_list destroy arg --terminus ca &> /dev/null

      echo "Recreating CRL certs..."
      /usr/bin/puppet cert clean no-host &> /dev/null
  fi

elif [ -f /var/lib/puppet/ssl/crl.pem ]
then
  if [ $(/usr/bin/expr $(/usr/bin/openssl crl -noout -nextupdate -in /var/lib/puppet/ssl/crl.pem | /usr/bin/awk '{ print $4 }') - $(/usr/bin/date +%Y)) -lt 6 ]
  then
      echo "Removing puppet CRL cert..."
      /usr/bin/find /var/lib/puppet/ssl/ -name crl.pem -delete &> /dev/null
  fi
fi

%else
/sbin/chkconfig --add puppet || :
if [ "$1" -ge 1 ]; then
  # The pidfile changed from 0.25.x to 2.6.x, handle upgrades without leaving
  # the old process running.
  oldpid="%{_localstatedir}/run/puppet/puppetd.pid"
  newpid="%{_localstatedir}/run/puppet/agent.pid"
  if [ -s "$oldpid" -a ! -s "$newpid" ]; then
    (kill $(< "$oldpid") && rm -f "$oldpid" && \
      /sbin/service puppet start) >/dev/null 2>&1 || :
  fi

  # If an old puppet process (one whose binary is located in /sbin) is running,
  # kill it and then start up a fresh with the new binary.
  if [ -e "$newpid" ]; then
    if ps aux | grep `cat "$newpid"` | grep -v grep | awk '{ print $12 }' | grep -q sbin; then
      (kill $(< "$newpid") && rm -f "$newpid" && \
        /sbin/service puppet start) >/dev/null 2>&1 || :
    fi
  fi
fi
%endif

%post server
%if 0%{?_with_systemd}
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ "$1" -ge 1 ]; then
  # The pidfile changed from 0.25.x to 2.6.x, handle upgrades without leaving
  # the old process running.
  oldpid="%{_localstatedir}/run/puppet/puppetmasterd.pid"
  newpid="%{_localstatedir}/run/puppet/master.pid"
  if [ -s "$oldpid" -a ! -s "$newpid" ]; then
    (kill $(< "$oldpid") && rm -f "$oldpid" && \
      /bin/systemctl start puppetmaster.service) > /dev/null 2>&1 || :
  fi
fi
%else
/sbin/chkconfig --add puppetmaster || :
if [ "$1" -ge 1 ]; then
  # The pidfile changed from 0.25.x to 2.6.x, handle upgrades without leaving
  # the old process running.
  oldpid="%{_localstatedir}/run/puppet/puppetmasterd.pid"
  newpid="%{_localstatedir}/run/puppet/master.pid"
  if [ -s "$oldpid" -a ! -s "$newpid" ]; then
    (kill $(< "$oldpid") && rm -f "$oldpid" && \
      /sbin/service puppetmaster start) >/dev/null 2>&1 || :
  fi
fi
%endif

%preun
%if 0%{?_with_systemd}
if [ "$1" -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable puppetagent.service > /dev/null 2>&1 || :
    /bin/systemctl --no-reload disable puppet.service > /dev/null 2>&1 || :
    /bin/systemctl stop puppetagent.service > /dev/null 2>&1 || :
    /bin/systemctl stop puppet.service > /dev/null 2>&1 || :
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

if [ "$1" == "1" ]; then
    /bin/systemctl is-enabled puppetagent.service > /dev/null 2>&1
    if [ "$?" == "0" ]; then
        /bin/systemctl --no-reload disable puppetagent.service > /dev/null 2>&1 ||:
        /bin/systemctl stop puppetagent.service > /dev/null 2>&1 ||:
        /bin/systemctl daemon-reload >/dev/null 2>&1 ||:
        if [ ! -d %{pending_upgrade_path} ]; then
            mkdir -p %{pending_upgrade_path}
        fi

        if [ ! -e %{pending_upgrade_file} ]; then
            touch %{pending_upgrade_file}
        fi
    fi
fi

%else
if [ "$1" = 0 ] ; then
    /sbin/service puppet stop > /dev/null 2>&1
    /sbin/chkconfig --del puppet || :
fi
%endif

%preun server
%if 0%{?_with_systemd}
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable puppetmaster.service > /dev/null 2>&1 || :
    /bin/systemctl stop puppetmaster.service > /dev/null 2>&1 || :
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
%else
if [ "$1" = 0 ] ; then
    /sbin/service puppetmaster stop > /dev/null 2>&1
    /sbin/chkconfig --del puppetmaster || :
fi
%endif

%postun
%if 0%{?_with_systemd}
if [ $1 -ge 1 ] ; then
    if [ -e %{pending_upgrade_file} ]; then
        /bin/systemctl --no-reload enable puppet.service > /dev/null 2>&1 ||:
        /bin/systemctl start puppet.service > /dev/null 2>&1 ||:
        /bin/systemctl daemon-reload >/dev/null 2>&1 ||:
        rm %{pending_upgrade_file}
    fi
    # Package upgrade, not uninstall
    /bin/systemctl try-restart puppetagent.service >/dev/null 2>&1 || :
fi
%else
if [ "$1" -ge 1 ]; then
    /sbin/service puppet condrestart >/dev/null 2>&1 || :
fi
%endif

%postun server
%if 0%{?_with_systemd}
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart puppetmaster.service >/dev/null 2>&1 || :
fi
%else
if [ "$1" -ge 1 ]; then
    /sbin/service puppetmaster condrestart >/dev/null 2>&1 || :
fi
%endif

%clean
rm -rf %{buildroot}

%changelog
* Mon Apr 25 2016 Puppet Labs Release <info@puppetlabs.com> -  3.8.7-1
- Build for 3.8.7

* Wed Oct 2 2013 Jason Antman <jason@jasonantman.com>
- Move systemd service and unit file names back to "puppet" from erroneous "puppetagent"
- Add symlink to puppetagent unit file for compatibility with current bug
- Alter package removal actions to deactivate and stop both service names

* Thu Jun 27 2013 Matthaus Owens <matthaus@puppetlabs.com> - 3.2.3-0.1rc0
- Bump requires on ruby-rgen to 0.6.5

* Fri Apr 12 2013 Matthaus Owens <matthaus@puppetlabs.com> - 3.2.0-0.1rc0
- Add requires on ruby-rgen for new parser in Puppet 3.2

* Fri Jan 25 2013 Matthaus Owens <matthaus@puppetlabs.com> - 3.1.0-0.1rc1
- Add extlookup2hiera.8.gz to the files list

* Wed Jan 9  2013 Ryan Uber <ru@ryanuber.com> - 3.1.0-0.1rc1
- Work-around for RH Bugzilla 681540

* Fri Dec 28 2012 Michael Stahnke <stahnma@puppetlabs.com> -  3.0.2-2
- Added a script for Network Manager for bug https://bugzilla.redhat.com/532085

* Tue Dec 18 2012 Matthaus Owens <matthaus@puppetlabs.com>
- Remove for loop on examples/ code which no longer exists. Add --no-run-if-empty to xargs invocations.

* Sat Dec 1 2012 Ryan Uber <ryuber@cisco.com>
- Fix for logdir perms regression (#17866)

* Wed Aug 29 2012 Moses Mendoza <moses@puppetlabs.com> - 3.0.0-0.1rc5
- Update for 3.0.0 rc5

* Fri Aug 24 2012 Eric Sorenson <eric0@puppetlabs.com> - 3.0.0-0.1rc4
- Facter requirement is 1.6.11, not 2.0
- Update for 3.0.0 rc4

* Tue Aug 21 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.19-1
- Update for 2.7.19

* Tue Aug 14 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.19-0.1rc3
- Update for 2.7.19rc3

* Tue Aug 7 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.19-0.1rc2
- Update for 2.7.19rc2

* Wed Aug 1 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.19-0.1rc1
- Update for 2.7.19rc1

* Wed Jul 11 2012 William Hopper <whopper@puppetlabs.com> - 2.7.18-2
- (#15221) Create /etc/puppet/modules for puppet module tool

* Mon Jul 9 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.18-1
- Update for 2.7.18

* Tue Jun 19 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 2.7.17-1
- Update for 2.7.17

* Wed Jun 13 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 2.7.16-1
- Update for 2.7.16

* Fri Jun 08 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.16-0.1rc1.2
- Updated facter 2.0 dep to include epoch 1

* Wed Jun 06 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 2.7.16-0.1rc1
- Update for 2.7.16rc1, added generated manpages

* Fri Jun 01 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 3.0.0-0.1rc3
- Puppet 3.0.0rc3 Release

* Fri Jun 01 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 2.7.15-0.1rc4
- Update for 2.7.15rc4

* Tue May 29 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.15-0.1rc3
- Update for 2.7.15rc3

* Tue May 22 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 3.0.0-0.1rc2
- Puppet 3.0.0rc2 Release

* Thu May 17 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 3.0.0-0.1rc1
- Puppet 3.0.0rc1 Release

* Wed May 16 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.15-0.1rc2
- Update for 2.7.15rc2

* Tue May 15 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.15-0.1rc1
- Update for 2.7.15rc1

* Wed May 02 2012 Moses Mendoza <moses@puppetlabs.com> - 2.7.14-1
- Update for 2.7.14

* Tue Apr 10 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 2.7.13-1
- Update for 2.7.13

* Mon Mar 12 2012 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.12-1
- Update for 2.7.12

* Fri Feb 24 2012 Matthaus Litteken <matthaus@puppetlabs.com> - 2.7.11-2
- Update 2.7.11 from proper tag, including #12572

* Wed Feb 22 2012 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.11-1
- Update for 2.7.11

* Wed Jan 25 2012 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.10-1
- Update for 2.7.10

* Fri Dec 9 2011 Matthaus Litteken <matthaus@puppetlabs.com> - 2.7.9-1
- Update for 2.7.9

* Thu Dec 8 2011 Matthaus Litteken <matthaus@puppetlabs.com> - 2.7.8-1
- Update for 2.7.8

* Wed Nov 30 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.8-0.1rc1
- Update for 2.7.8rc1

* Mon Nov 21 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.7-1
- Relaese 2.7.7

* Tue Nov 01 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.7-0.1rc1
- Update for 2.7.7rc1

* Fri Oct 21 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.6-1
- 2.7.6 final

* Thu Oct 13 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.6-.1rc3
- New RC

* Fri Oct 07 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.6-0.1rc2
- New RC

* Mon Oct 03 2011 Michael Stahnke <stahnma@puppetlabs.com> -  2.7.6-0.1rc1
- New RC

* Fri Sep 30 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.5-1
- Fixes for CVE-2011-3869, 3870, 3871

* Wed Sep 28 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.4-1
- Fix for CVE-2011-3484

* Wed Jul 06 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.2-0.2.rc1
- Clean up rpmlint errors
- Put man pages in correct package

* Wed Jul 06 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.7.2-0.1.rc1
- Update to 2.7.2rc1

* Wed Jun 15 2011 Todd Zullinger <tmz@pobox.com> - 2.6.9-0.1.rc1
- Update rc versioning to ensure 2.6.9 final is newer to rpm
- sync changes with Fedora/EPEL

* Tue Jun 14 2011 Michael Stahnke <stahnma@puppetlabs.com> - 2.6.9rc1-1
- Update to 2.6.9rc1

* Thu Apr 14 2011 Todd Zullinger <tmz@pobox.com> - 2.6.8-1
- Update to 2.6.8

* Thu Mar 24 2011 Todd Zullinger <tmz@pobox.com> - 2.6.7-1
- Update to 2.6.7

* Wed Mar 16 2011 Todd Zullinger <tmz@pobox.com> - 2.6.6-1
- Update to 2.6.6
- Ensure %%pre exits cleanly
- Fix License tag, puppet is now GPLv2 only
- Create and own /usr/share/puppet/modules (#615432)
- Properly restart puppet agent/master daemons on upgrades from 0.25.x
- Require libselinux-utils when selinux support is enabled
- Support tmpfiles.d for Fedora >= 15 (#656677)

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.25.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon May 17 2010 Todd Zullinger <tmz@pobox.com> - 0.25.5-1
- Update to 0.25.5
- Adjust selinux conditional for EL-6
- Apply rundir-perms patch from tarball rather than including it separately
- Update URL's to reflect the new puppetlabs.com domain

* Fri Jan 29 2010 Todd Zullinger <tmz@pobox.com> - 0.25.4-1
- Update to 0.25.4

* Tue Jan 19 2010 Todd Zullinger <tmz@pobox.com> - 0.25.3-2
- Apply upstream patch to fix cron resources (upstream #2845)

* Mon Jan 11 2010 Todd Zullinger <tmz@pobox.com> - 0.25.3-1
- Update to 0.25.3

* Tue Jan 05 2010 Todd Zullinger <tmz@pobox.com> - 0.25.2-1.1
- Replace %%define with %%global for macros

* Tue Jan 05 2010 Todd Zullinger <tmz@pobox.com> - 0.25.2-1
- Update to 0.25.2
- Fixes CVE-2010-0156, tmpfile security issue (#502881)
- Install auth.conf, puppetqd manpage, and queuing examples/docs

* Wed Nov 25 2009 Jeroen van Meeuwen <j.van.meeuwen@ogd.nl> - 0.25.1-1
- New upstream version

* Tue Oct 27 2009 Todd Zullinger <tmz@pobox.com> - 0.25.1-0.3
- Update to 0.25.1
- Include the pi program and man page (R.I.Pienaar)

* Sat Oct 17 2009 Todd Zullinger <tmz@pobox.com> - 0.25.1-0.2.rc2
- Update to 0.25.1rc2

* Tue Sep 22 2009 Todd Zullinger <tmz@pobox.com> - 0.25.1-0.1.rc1
- Update to 0.25.1rc1
- Move puppetca to puppet package, it has uses on client systems
- Drop redundant %%doc from manpage %%file listings

* Fri Sep 04 2009 Todd Zullinger <tmz@pobox.com> - 0.25.0-1
- Update to 0.25.0
- Fix permissions on /var/log/puppet (#495096)
- Install emacs mode and vim syntax files (#491437)
- Install ext/ directory in %%{_datadir}/%%{name} (/usr/share/puppet)

* Mon May 04 2009 Todd Zullinger <tmz@pobox.com> - 0.25.0-0.1.beta1
- Update to 0.25.0beta1
- Make Augeas and SELinux requirements build time options

* Mon Mar 23 2009 Todd Zullinger <tmz@pobox.com> - 0.24.8-1
- Update to 0.24.8
- Quiet output from %%pre
- Use upstream install script
- Increase required facter version to >= 1.5

* Tue Dec 16 2008 Todd Zullinger <tmz@pobox.com> - 0.24.7-4
- Remove redundant useradd from %%pre

* Tue Dec 16 2008 Jeroen van Meeuwen <kanarip@kanarip.com> - 0.24.7-3
- New upstream version
- Set a static uid and gid (#472073, #471918, #471919)
- Add a conditional requirement on libselinux-ruby for Fedora >= 9
- Add a dependency on ruby-augeas

* Wed Oct 22 2008 Todd Zullinger <tmz@pobox.com> - 0.24.6-1
- Update to 0.24.6
- Require ruby-shadow on Fedora and RHEL >= 5
- Simplify Fedora/RHEL version checks for ruby(abi) and BuildArch
- Require chkconfig and initstripts for preun, post, and postun scripts
- Conditionally restart puppet in %%postun
- Ensure %%preun, %%post, and %%postun scripts exit cleanly
- Create puppet user/group according to Fedora packaging guidelines
- Quiet a few rpmlint complaints
- Remove useless %%pbuild macro
- Make specfile more like the Fedora/EPEL template

* Mon Jul 28 2008 David Lutterkort <dlutter@redhat.com> - 0.24.5-1
- Add /usr/bin/puppetdoc

* Thu Jul 24 2008 Brenton Leanhardt <bleanhar@redhat.com>
- New version
- man pages now ship with tarball
- examples/code moved to root examples dir in upstream tarball

* Tue Mar 25 2008 David Lutterkort <dlutter@redhat.com> - 0.24.4-1
- Add man pages (from separate tarball, upstream will fix to
  include in main tarball)

* Mon Mar 24 2008 David Lutterkort <dlutter@redhat.com> - 0.24.3-1
- New version

* Wed Mar  5 2008 David Lutterkort <dlutter@redhat.com> - 0.24.2-1
- New version

* Sat Dec 22 2007 David Lutterkort <dlutter@redhat.com> - 0.24.1-1
- New version

* Mon Dec 17 2007 David Lutterkort <dlutter@redhat.com> - 0.24.0-2
- Use updated upstream tarball that contains yumhelper.py

* Fri Dec 14 2007 David Lutterkort <dlutter@redhat.com> - 0.24.0-1
- Fixed license
- Munge examples/ to make rpmlint happier

* Wed Aug 22 2007 David Lutterkort <dlutter@redhat.com> - 0.23.2-1
- New version

* Thu Jul 26 2007 David Lutterkort <dlutter@redhat.com> - 0.23.1-1
- Remove old config files

* Wed Jun 20 2007 David Lutterkort <dlutter@redhat.com> - 0.23.0-1
- Install one puppet.conf instead of old config files, keep old configs
  around to ease update
- Use plain shell commands in install instead of macros

* Wed May  2 2007 David Lutterkort <dlutter@redhat.com> - 0.22.4-1
- New version

* Thu Mar 29 2007 David Lutterkort <dlutter@redhat.com> - 0.22.3-1
- Claim ownership of _sysconfdir/puppet (bz 233908)

* Mon Mar 19 2007 David Lutterkort <dlutter@redhat.com> - 0.22.2-1
- Set puppet's homedir to /var/lib/puppet, not /var/puppet
- Remove no-lockdir patch, not needed anymore

* Mon Feb 12 2007 David Lutterkort <dlutter@redhat.com> - 0.22.1-2
- Fix bogus config parameter in puppetd.conf

* Sat Feb  3 2007 David Lutterkort <dlutter@redhat.com> - 0.22.1-1
- New version

* Fri Jan  5 2007 David Lutterkort <dlutter@redhat.com> - 0.22.0-1
- New version

* Mon Nov 20 2006 David Lutterkort <dlutter@redhat.com> - 0.20.1-2
- Make require ruby(abi) and buildarch: noarch conditional for fedora 5 or
  later to allow building on older fedora releases

* Mon Nov 13 2006 David Lutterkort <dlutter@redhat.com> - 0.20.1-1
- New version

* Mon Oct 23 2006 David Lutterkort <dlutter@redhat.com> - 0.20.0-1
- New version

* Tue Sep 26 2006 David Lutterkort <dlutter@redhat.com> - 0.19.3-1
- New version

* Mon Sep 18 2006 David Lutterkort <dlutter@redhat.com> - 0.19.1-1
- New version

* Thu Sep  7 2006 David Lutterkort <dlutter@redhat.com> - 0.19.0-1
- New version

* Tue Aug  1 2006 David Lutterkort <dlutter@redhat.com> - 0.18.4-2
- Use /usr/bin/ruby directly instead of /usr/bin/env ruby in
  executables. Otherwise, initscripts break since pidof can't find the
  right process

* Tue Aug  1 2006 David Lutterkort <dlutter@redhat.com> - 0.18.4-1
- New version

* Fri Jul 14 2006 David Lutterkort <dlutter@redhat.com> - 0.18.3-1
- New version

* Wed Jul  5 2006 David Lutterkort <dlutter@redhat.com> - 0.18.2-1
- New version

* Wed Jun 28 2006 David Lutterkort <dlutter@redhat.com> - 0.18.1-1
- Removed lsb-config.patch and yumrepo.patch since they are upstream now

* Mon Jun 19 2006 David Lutterkort <dlutter@redhat.com> - 0.18.0-1
- Patch config for LSB compliance (lsb-config.patch)
- Changed config moves /var/puppet to /var/lib/puppet, /etc/puppet/ssl
  to /var/lib/puppet, /etc/puppet/clases.txt to /var/lib/puppet/classes.txt,
  /etc/puppet/localconfig.yaml to /var/lib/puppet/localconfig.yaml

* Fri May 19 2006 David Lutterkort <dlutter@redhat.com> - 0.17.2-1
- Added /usr/bin/puppetrun to server subpackage
- Backported patch for yumrepo type (yumrepo.patch)

* Wed May  3 2006 David Lutterkort <dlutter@redhat.com> - 0.16.4-1
- Rebuilt

* Fri Apr 21 2006 David Lutterkort <dlutter@redhat.com> - 0.16.0-1
- Fix default file permissions in server subpackage
- Run puppetmaster as user puppet
- rebuilt for 0.16.0

* Mon Apr 17 2006 David Lutterkort <dlutter@redhat.com> - 0.15.3-2
- Don't create empty log files in post-install scriptlet

* Fri Apr  7 2006 David Lutterkort <dlutter@redhat.com> - 0.15.3-1
- Rebuilt for new version

* Wed Mar 22 2006 David Lutterkort <dlutter@redhat.com> - 0.15.1-1
- Patch0: Run puppetmaster as root; running as puppet is not ready
  for primetime

* Mon Mar 13 2006 David Lutterkort <dlutter@redhat.com> - 0.15.0-1
- Commented out noarch; requires fix for bz184199

* Mon Mar  6 2006 David Lutterkort <dlutter@redhat.com> - 0.14.0-1
- Added BuildRequires for ruby

* Wed Mar  1 2006 David Lutterkort <dlutter@redhat.com> - 0.13.5-1
- Removed use of fedora-usermgmt. It is not required for Fedora Extras and
  makes it unnecessarily hard to use this rpm outside of Fedora. Just
  allocate the puppet uid/gid dynamically

* Sun Feb 19 2006 David Lutterkort <dlutter@redhat.com> - 0.13.0-4
- Use fedora-usermgmt to create puppet user/group. Use uid/gid 24. Fixed
problem with listing fileserver.conf and puppetmaster.conf twice

* Wed Feb  8 2006 David Lutterkort <dlutter@redhat.com> - 0.13.0-3
- Fix puppetd.conf

* Wed Feb  8 2006 David Lutterkort <dlutter@redhat.com> - 0.13.0-2
- Changes to run puppetmaster as user puppet

* Mon Feb  6 2006 David Lutterkort <dlutter@redhat.com> - 0.13.0-1
- Don't mark initscripts as config files

* Mon Feb  6 2006 David Lutterkort <dlutter@redhat.com> - 0.12.0-2
- Fix BuildRoot. Add dist to release

* Tue Jan 17 2006 David Lutterkort <dlutter@redhat.com> - 0.11.0-1
- Rebuild

* Thu Jan 12 2006 David Lutterkort <dlutter@redhat.com> - 0.10.2-1
- Updated for 0.10.2 Fixed minor kink in how Source is given

* Wed Jan 11 2006 David Lutterkort <dlutter@redhat.com> - 0.10.1-3
- Added basic fileserver.conf

* Wed Jan 11 2006 David Lutterkort <dlutter@redhat.com> - 0.10.1-1
- Updated. Moved installation of library files to sitelibdir. Pulled
initscripts into separate files. Folded tools rpm into server

* Thu Nov 24 2005 Duane Griffin <d.griffin@psenterprise.com>
- Added init scripts for the client

* Wed Nov 23 2005 Duane Griffin <d.griffin@psenterprise.com>
- First packaging

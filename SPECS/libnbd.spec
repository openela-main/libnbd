# If we should verify tarball signature with GPGv2.
%global verify_tarball_signature 1

# If there are patches which touch autotools files, set this to 1.
%global patches_touch_autotools 1

# The source directory.
%global source_directory 1.6-stable

Name:           libnbd
Version:        1.6.0
Release:        5%{?dist}
Summary:        NBD client library in userspace

License:        LGPLv2+
URL:            https://github.com/libguestfs/libnbd

Source0:        http://libguestfs.org/download/libnbd/%{source_directory}/%{name}-%{version}.tar.gz
Source1:        http://libguestfs.org/download/libnbd/%{source_directory}/%{name}-%{version}.tar.gz.sig
# Keyring used to verify tarball signature.  This contains the single
# key from here:
# https://pgp.key-server.io/pks/lookup?search=rjones%40redhat.com&fingerprint=on&op=vindex
Source2:       libguestfs.keyring

# Maintainer script which helps with handling patches.
Source3:        copy-patches.sh

# Patches come from this upstream branch:
# https://github.com/libguestfs/libnbd/tree/rhel-8.6

# Patches.
Patch0001:     0001-copy-copy-nbd-to-sparse-file.sh-Skip-test-unless-nbd.patch
Patch0002:     0002-generator-Refactor-CONNECT.START-state.patch
Patch0003:     0003-generator-Print-a-better-error-message-if-connect-2-.patch
Patch0004:     0004-opt_go-Tolerate-unplanned-server-death.patch
Patch0005:     0005-security-Document-assignment-of-CVE-2021-20286.patch
Patch0006:     0006-copy-Pass-in-dummy-variable-rather-than-errno-to-cal.patch
Patch0007:     0007-copy-CVE-2022-0485-Fail-nbdcopy-if-NBD-read-or-write.patch

%if 0%{patches_touch_autotools}
BuildRequires: autoconf, automake, libtool
%endif

%if 0%{verify_tarball_signature}
BuildRequires:  gnupg2
%endif

# For the core library.
BuildRequires:  gcc
BuildRequires:  /usr/bin/pod2man
BuildRequires:  gnutls-devel
BuildRequires:  libxml2-devel

# For nbdfuse.
BuildRequires:  fuse, fuse-devel

# For the Python 3 bindings.
BuildRequires:  python3-devel

# For the OCaml bindings.
BuildRequires:  ocaml
BuildRequires:  ocaml-findlib-devel
BuildRequires:  ocaml-ocamldoc

# Only for building the examples.
BuildRequires:  glib2-devel

# For bash-completion.
BuildRequires:  bash-completion

# Only for running the test suite.
BuildRequires:  coreutils
BuildRequires:  gcc-c++
BuildRequires:  gnutls-utils
#BuildRequires:  jq
%ifnarch %{ix86}
BuildRequires:  nbdkit
BuildRequires:  nbdkit-data-plugin
#BuildRequires:  nbdkit-eval-plugin
BuildRequires:  nbdkit-memory-plugin
BuildRequires:  nbdkit-null-plugin
BuildRequires:  nbdkit-pattern-plugin
BuildRequires:  nbdkit-sh-plugin
#BuildRequires:  nbdkit-sparse-random-plugin
#BuildRequires:  nbd
BuildRequires:  qemu-img
%endif
BuildRequires:  util-linux


%description
NBD — Network Block Device — is a protocol for accessing Block Devices
(hard disks and disk-like things) over a Network.

This is the NBD client library in userspace, a simple library for
writing NBD clients.

The key features are:

 * Synchronous and asynchronous APIs, both for ease of use and for
   writing non-blocking, multithreaded clients.

 * High performance.

 * Minimal dependencies for the basic library.

 * Well-documented, stable API.

 * Bindings in several programming languages.


%package devel
Summary:        Development headers for %{name}
License:        LGPLv2+ and BSD
Requires:       %{name}%{?_isa} = %{version}-%{release}


%description devel
This package contains development headers for %{name}.


%package -n ocaml-%{name}
Summary:        OCaml language bindings for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}


%description -n ocaml-%{name}
This package contains OCaml language bindings for %{name}.


%package -n ocaml-%{name}-devel
Summary:        OCaml language development package for %{name}
Requires:       ocaml-%{name}%{?_isa} = %{version}-%{release}


%description -n ocaml-%{name}-devel
This package contains OCaml language development package for
%{name}.  Install this if you want to compile OCaml software which
uses %{name}.


%package -n python3-%{name}
Summary:        Python 3 bindings for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
%{?python_provide:%python_provide python3-%{name}}

# The Python module happens to be called lib*.so.  Don't scan it and
# have a bogus "Provides: libnbdmod.*".
%global __provides_exclude_from ^%{python3_sitearch}/lib.*\\.so


%description -n python3-%{name}
python3-%{name} contains Python 3 bindings for %{name}.


%package -n nbdfuse
Summary:        FUSE support for %{name}
License:        LGPLv2+ and BSD
Requires:       %{name}%{?_isa} = %{version}-%{release}


%description -n nbdfuse
This package contains FUSE support for %{name}.


%package bash-completion
Summary:       Bash tab-completion for %{name}
BuildArch:     noarch
Requires:      bash-completion >= 2.0
# Don't use _isa here because it's a noarch package.  This dependency
# is just to ensure that the subpackage is updated along with libnbd.
Requires:      %{name} = %{version}-%{release}


%description bash-completion
Install this package if you want intelligent bash tab-completion
for %{name}.


%prep
%if 0%{verify_tarball_signature}
tmphome="$(mktemp -d)"
gpgv2 --homedir "$tmphome" --keyring %{SOURCE2} %{SOURCE1} %{SOURCE0}
%endif
%autosetup -p1
%if 0%{patches_touch_autotools}
autoreconf -i
%endif


%build
%configure \
    --disable-static \
    --with-tls-priority=@LIBNBD,SYSTEM \
    PYTHON=%{__python3} \
    --enable-python \
    --enable-ocaml \
    --enable-fuse \
    --disable-golang

make %{?_smp_mflags}


%install
%make_install

# Delete libtool crap.
find $RPM_BUILD_ROOT -name '*.la' -delete

# Delete the golang man page since we're not distributing the bindings.
rm $RPM_BUILD_ROOT%{_mandir}/man3/libnbd-golang.3*


%check
# interop/structured-read.sh fails with the old qemu-nbd in Fedora 29,
# so disable it there.
%if 0%{?fedora} <= 29
rm interop/structured-read.sh
touch interop/structured-read.sh
chmod +x interop/structured-read.sh
%endif

# All fuse tests fail in Koji with:
# fusermount: entry for fuse/test-*.d not found in /etc/mtab
# for unknown reasons but probably related to the Koji environment.
for f in fuse/test-*.sh; do
    rm $f
    touch $f
    chmod +x $f
done

# info/info-map-base-allocation-json.sh fails because of a bug in
# jq 1.5 in RHEL 8 (fixed in later versions).
rm info/info-map-base-allocation-json.sh
touch info/info-map-base-allocation-json.sh
chmod +x info/info-map-base-allocation-json.sh

make %{?_smp_mflags} check || {
    for f in $(find -name test-suite.log); do
        echo
        echo "==== $f ===="
        cat $f
    done
    exit 1
  }


%files
%doc README
%license COPYING.LIB
%{_bindir}/nbdcopy
%{_bindir}/nbdinfo
%{_libdir}/libnbd.so.*
%{_mandir}/man1/nbdcopy.1*
%{_mandir}/man1/nbdinfo.1*


%files devel
%doc TODO examples/*.c
%license examples/LICENSE-FOR-EXAMPLES
%{_includedir}/libnbd.h
%{_libdir}/libnbd.so
%{_libdir}/pkgconfig/libnbd.pc
%{_mandir}/man3/libnbd.3*
%{_mandir}/man1/libnbd-release-notes-1.*.1*
%{_mandir}/man3/libnbd-security.3*
%{_mandir}/man3/nbd_*.3*


%files -n ocaml-%{name}
%{_libdir}/ocaml/nbd
%exclude %{_libdir}/ocaml/nbd/*.a
%exclude %{_libdir}/ocaml/nbd/*.cmxa
%exclude %{_libdir}/ocaml/nbd/*.cmx
%exclude %{_libdir}/ocaml/nbd/*.mli
%{_libdir}/ocaml/stublibs/dllmlnbd.so
%{_libdir}/ocaml/stublibs/dllmlnbd.so.owner


%files -n ocaml-%{name}-devel
%doc ocaml/examples/*.ml
%license ocaml/examples/LICENSE-FOR-EXAMPLES
%{_libdir}/ocaml/nbd/*.a
%{_libdir}/ocaml/nbd/*.cmxa
%{_libdir}/ocaml/nbd/*.cmx
%{_libdir}/ocaml/nbd/*.mli
%{_mandir}/man3/libnbd-ocaml.3*
%{_mandir}/man3/NBD.3*
%{_mandir}/man3/NBD.*.3*


%files -n python3-%{name}
%{python3_sitearch}/libnbdmod*.so
%{python3_sitearch}/nbd.py
%{python3_sitearch}/nbdsh.py
%{python3_sitearch}/__pycache__/nbd*.py*
%{_bindir}/nbdsh
%{_mandir}/man1/nbdsh.1*


%files -n nbdfuse
%{_bindir}/nbdfuse
%{_mandir}/man1/nbdfuse.1*


%files bash-completion
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/nbdcopy
%{_datadir}/bash-completion/completions/nbdfuse
%{_datadir}/bash-completion/completions/nbdinfo
%{_datadir}/bash-completion/completions/nbdsh


%changelog
* Mon Feb  7 2022 Richard W.M. Jones <rjones@redhat.com> - 1.6.0-5.el8
- Fix CVE-2022-0485: Fail nbdcopy if NBD read or write fails
  resolves: rhbz#2045718

* Thu Sep 2 2021 Danilo C. L. de Paula <ddepaula@redhat.com> - 1.6.0-4.el8
- Resolves: bz#2000225
  (Rebase virt:rhel module:stream based on AV-8.6)

* Mon Jul 13 2020 Danilo C. L. de Paula <ddepaula@redhat.com> - 1.2.2
- Resolves: bz#1844296
(Upgrade components in virt:rhel module:stream for RHEL-8.3 release)

* Wed Feb  5 2020 Richard W.M. Jones <rjones@redhat.com> - 1.2.2-1
- New stable release 1.2.2.

* Tue Dec  3 2019 Richard W.M. Jones <rjones@redhat.com> - 1.2.1-1
- New stable release 1.2.1.

* Thu Nov 14 2019 Richard W.M. Jones <rjones@redhat.com> - 1.2.0-1
- New stable release 1.2.0.

* Wed Oct  9 2019 Richard W.M. Jones <rjones@redhat.com> - 1.0.3-1
- New upstream version 1.0.3.
- Contains fix for remote code execution vulnerability.
- Add new libnbd-security(3) man page.

* Tue Sep 17 2019 Richard W.M. Jones <rjones@redhat.com> - 1.0.2-1
- New upstream version 1.0.2.
- Remove patches which are upstream.
- Contains fix for NBD Protocol Downgrade Attack (CVE-2019-14842).
- Fix previous commit message.

* Thu Sep 12 2019 Richard W.M. Jones <rjones@redhat.com> - 1.0.1-2
- Add upstream patch to fix nbdsh (for nbdkit tests).
- Fix interop tests on slow machines.

* Sun Sep 08 2019 Richard W.M. Jones <rjones@redhat.com> - 1.0.1-1
- New stable version 1.0.1.

* Wed Aug 28 2019 Richard W.M. Jones <rjones@redhat.com> - 1.0.0-1
- New upstream version 1.0.0.

* Wed Aug 21 2019 Miro Hrončok <mhroncok@redhat.com> - 0.9.9-2
- Rebuilt for Python 3.8

* Wed Aug 21 2019 Richard W.M. Jones <rjones@redhat.com> - 0.9.9-1
- New upstream version 0.9.9.

* Wed Aug 21 2019 Richard W.M. Jones <rjones@redhat.com> - 0.9.8-4
- Fix nbdkit dependencies so we're actually running the tests.
- Add glib2-devel BR so we build the glib main loop example.
- Add upstream patch to fix test error:
  nbd_connect_unix: getlogin: No such device or address
- Fix test failure on 32 bit.

* Tue Aug 20 2019 Richard W.M. Jones <rjones@redhat.com> - 0.9.8-3
- Bump and rebuild to fix releng brokenness.
  https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/message/2LIDI33G3IEIPYSCCIP6WWKNHY7XZJGQ/

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 0.9.8-2
- Rebuilt for Python 3.8

* Thu Aug 15 2019 Richard W.M. Jones <rjones@redhat.com> - 0.9.8-1
- New upstream version 0.9.8.
- Package the new nbd_*(3) man pages.

* Mon Aug  5 2019 Richard W.M. Jones <rjones@redhat.com> - 0.9.7-1
- New upstream version 0.9.7.
- Add libnbd-ocaml(3) man page.

* Sat Aug  3 2019 Richard W.M. Jones <rjones@redhat.com> - 0.9.6-2
- Add all upstream patches since 0.9.6 was released.
- Package the ocaml bindings into a subpackage.

* Tue Jul 30 2019 Richard W.M. Jones <rjones@redhat.com> - 0.9.6-1
- New upstream verison 0.9.6.

* Fri Jul 26 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.9-1
- New upstream version 0.1.9.

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Wed Jul 17 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.8-1
- New upstream version 0.1.8.

* Tue Jul 16 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.7-1
- New upstream version 0.1.7.

* Wed Jul  3 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.6-1
- New upstream version 0.1.6.

* Thu Jun 27 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.5-1
- New upstream version 0.1.5.

* Sun Jun 09 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.4-1
- New upstream version 0.1.4.

* Sun Jun  2 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.2-2
- Enable libxml2 for NBD URI support.

* Thu May 30 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.2-1
- New upstream version 0.1.2.

* Tue May 28 2019 Richard W.M. Jones <rjones@redhat.com> - 0.1.1-1
- Fix license in man pages and examples.
- Add nbdsh(1) man page.
- Include the signature and keyring even if validation is disabled.
- Update devel subpackage license.
- Fix old FSF address in Python tests.
- Filter Python provides.
- Remove executable permission on the tar.gz.sig file.
- Initial release.

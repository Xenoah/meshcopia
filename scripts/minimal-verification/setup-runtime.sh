#!/bin/sh
# Inside the pinned disposable official Debian container only. No Blender needed.
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update
mkdir /tmp/minimal-official-packages
cd /tmp/minimal-official-packages
apt-get download 'python3.13=3.13.5-2+deb13u5'
apt-get download 'zlib1g=1:1.3.dfsg+really1.3.1-1+b1'
set -- python3.13_*.deb
[ "$#" -eq 1 ]
printf '%s  %s\n' 460c1fd72845516ac3ce9d1686916f3ab2e4c86f8a9746e14d26243a47e2b98d "$1" | sha256sum -c -
set -- zlib1g_*.deb
[ "$#" -eq 1 ]
printf '%s  %s\n' 015be740d6236ad114582dea500c1d907f29e16d6db00566ca32fb68d71ac90d "$1" | sha256sum -c -
apt-get install -y ./*.deb git ca-certificates
printf '%s  %s\n' 889c603f0d17cb54060951bcf4c4f9b8c9ebd9e52b392c70209bbb9755d797d9 /usr/bin/python3.13 | sha256sum -c -
printf '%s  %s\n' 85590dd58edf5445e18bc7193e5ebc01ac5841f1ae187e97705a662e90c6421e /usr/lib/x86_64-linux-gnu/libz.so.1.3.1 | sha256sum -c -
/usr/bin/python3.13 -c 'import platform,zlib; assert platform.python_version()=="3.13.5"; assert zlib.ZLIB_VERSION==zlib.ZLIB_RUNTIME_VERSION=="1.3.1"'

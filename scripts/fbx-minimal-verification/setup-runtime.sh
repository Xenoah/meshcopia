#!/bin/sh
set -eu
# Official signed Debian package installation; no signature bypass or substitution.
export DEBIAN_FRONTEND=noninteractive
apt-get update
mkdir /tmp/fbx-official-packages
cd /tmp/fbx-official-packages
apt-get download 'blender=4.3.2+dfsg-2'
apt-get download 'blender-data=4.3.2+dfsg-2'
apt-get download 'libc6=2.41-12+deb13u4'
apt-get download 'python3-numpy=1:2.2.4+ds-1'
apt-get download 'python3.13=3.13.5-2+deb13u5'
apt-get download 'zlib1g=1:1.3.dfsg+really1.3.1-1+b1'
set -- blender_*.deb
[ "$#" -eq 1 ]
printf '%s  %s\n' '72059c2362953cedf7cce468cfc48b87338358731400cd71fd3d688be119daab' "$1" | sha256sum -c -
set -- blender-data_*.deb
[ "$#" -eq 1 ]
printf '%s  %s\n' 'ab95b1d6f75a7e9e38d251e8720c13a5d45be264ca90d0dfb4658374f6a5d137' "$1" | sha256sum -c -
set -- libc6_*.deb
[ "$#" -eq 1 ]
printf '%s  %s\n' '967aa62605721081c3eb2a17650611a792aa802d76a6511d1840242623d204c9' "$1" | sha256sum -c -
set -- python3-numpy_*.deb
[ "$#" -eq 1 ]
printf '%s  %s\n' 'eacb51b412e4621e4b6d631a479f6f0589522416e494d8da0e680f1863b5cb44' "$1" | sha256sum -c -
set -- python3.13_*.deb
[ "$#" -eq 1 ]
printf '%s  %s\n' '460c1fd72845516ac3ce9d1686916f3ab2e4c86f8a9746e14d26243a47e2b98d' "$1" | sha256sum -c -
set -- zlib1g_*.deb
[ "$#" -eq 1 ]
printf '%s  %s\n' '015be740d6236ad114582dea500c1d907f29e16d6db00566ca32fb68d71ac90d' "$1" | sha256sum -c -
apt-get install -y ./*.deb git ca-certificates
mkdir /tmp/fbx-official-data
dpkg-deb -x ./blender-data_*.deb /tmp/fbx-official-data
echo '8af335ff0daba71b9301e076f8c72836f013c012736d59d9e2b6700885d1eb1f  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/__init__.py' | sha256sum -c -
echo '8af335ff0daba71b9301e076f8c72836f013c012736d59d9e2b6700885d1eb1f  /usr/share/blender/scripts/addons_core/io_scene_fbx/__init__.py' | sha256sum -c -
echo '1697b26e84cdabdebf8cf8c1dbb6e3b303705917aaf84eab835f0cdad6b26e20  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/data_types.py' | sha256sum -c -
echo '1697b26e84cdabdebf8cf8c1dbb6e3b303705917aaf84eab835f0cdad6b26e20  /usr/share/blender/scripts/addons_core/io_scene_fbx/data_types.py' | sha256sum -c -
echo '3322a809e0073947e107de8f7e5839dff0956578271e88506eab7a7627f3323f  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/encode_bin.py' | sha256sum -c -
echo '3322a809e0073947e107de8f7e5839dff0956578271e88506eab7a7627f3323f  /usr/share/blender/scripts/addons_core/io_scene_fbx/encode_bin.py' | sha256sum -c -
echo 'fd494ffc3d8d01e21b028fa05b8bb7739afecfc09e0c8f2e09ef451b5b0e9e05  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/export_fbx_bin.py' | sha256sum -c -
echo 'fd494ffc3d8d01e21b028fa05b8bb7739afecfc09e0c8f2e09ef451b5b0e9e05  /usr/share/blender/scripts/addons_core/io_scene_fbx/export_fbx_bin.py' | sha256sum -c -
echo '4fc62f848f7834e2f376838251db2f64ec1a7856578acb6f152ac78ac5e60616  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/fbx2json.py' | sha256sum -c -
echo '4fc62f848f7834e2f376838251db2f64ec1a7856578acb6f152ac78ac5e60616  /usr/share/blender/scripts/addons_core/io_scene_fbx/fbx2json.py' | sha256sum -c -
echo 'ffabd204b2cce48670b47de6bb77e8dba06daa77b7efab037c4f157f1ffa80b6  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/fbx_utils.py' | sha256sum -c -
echo 'ffabd204b2cce48670b47de6bb77e8dba06daa77b7efab037c4f157f1ffa80b6  /usr/share/blender/scripts/addons_core/io_scene_fbx/fbx_utils.py' | sha256sum -c -
echo 'ddf8d90b87b51e057212c9b5f3c73caea49fddf2915140eb2e3206f7dad757a3  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/fbx_utils_threading.py' | sha256sum -c -
echo 'ddf8d90b87b51e057212c9b5f3c73caea49fddf2915140eb2e3206f7dad757a3  /usr/share/blender/scripts/addons_core/io_scene_fbx/fbx_utils_threading.py' | sha256sum -c -
echo 'd3a4232dc9bc7599df4058a4f786fa9c2c9c971809185b811439b64986a7ceac  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/import_fbx.py' | sha256sum -c -
echo 'd3a4232dc9bc7599df4058a4f786fa9c2c9c971809185b811439b64986a7ceac  /usr/share/blender/scripts/addons_core/io_scene_fbx/import_fbx.py' | sha256sum -c -
echo 'd7676c3116e0b16752a6530e42f1b1126ca1e37a61595d0ea84c21d46a97f8c5  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/json2fbx.py' | sha256sum -c -
echo 'd7676c3116e0b16752a6530e42f1b1126ca1e37a61595d0ea84c21d46a97f8c5  /usr/share/blender/scripts/addons_core/io_scene_fbx/json2fbx.py' | sha256sum -c -
echo '982c7b5071c293184f974dfb362b7c5f950c91a535d5283d656a8934aacfe5ad  /tmp/fbx-official-data/usr/share/blender/scripts/addons_core/io_scene_fbx/parse_fbx.py' | sha256sum -c -
echo '982c7b5071c293184f974dfb362b7c5f950c91a535d5283d656a8934aacfe5ad  /usr/share/blender/scripts/addons_core/io_scene_fbx/parse_fbx.py' | sha256sum -c -
echo '0dfe9af0f3e67643ecf15327fa5e14e7315f61d1a81afdcafe76a71b1918e2b4  /usr/bin/blender' | sha256sum -c -

apt-get update
apt-get upgrade
apt-get install -y gcc
apt-get install -y make
apt-get install -y curl
curl -o tmp.gz.tar https://ftp.gnu.org/pub/gnu/gettext/gettext-0.21.1.tar.gz
tar -xf tmp.gz.tar
cd gettext-0.21.1 && ./configure && make && make install
ldconfig

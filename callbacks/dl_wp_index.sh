#!/usr/bin/env bash

path=~/storage/shared/Download/WP/Files/"$1"/
extensions='jpg,jpeg,png,gif,bmp,sql,txt,csv,pdf,pcap'

if [ "$2" == "443" ]; then
    uri="https://$1"
else
    uri="http://$1:$2"
fi

echo "[*] $1"

wg(){
    wget -q --tries=1 --no-netrc --no-check-certificate \
        --connect-timeout=1 --read-timeout=5 \
        -e robots=off --user-agent Mozilla/5.0 "$@"
}

has_index() {
    wg "$1" -O- | grep -Fq 'Index of'
}

has_index "$uri" && echo "[~>=>] $uri" && wg --timestamping \
    -r -X '/bin' -np -nd -Q 100M \
    -A "$extensions" -P "$path" "$uri" \
    && echo "[+] $1" \
    || echo "[-] $1"

find "$path" -size 0 -delete 2> /dev/null
rmdir "$path" 2> /dev/null


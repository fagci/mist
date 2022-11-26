#!/usr/bin/env bash

path=~/storage/shared/Download/FTP/Files/"$1"/
extensions='jpg,jpeg,png,gif,bmp,sql,txt,csv,pdf,pcap'
uri="ftp://$1:$2"

echo "[*] $1"

wget --tries=1 --connect-timeout=1 --read-timeout=5 \
    --timestamping --no-netrc \
    -r -X '/bin' -np -nd -Q 100M \
    -A "$extensions" -P "$path" "$uri" \
    && echo "[+] $1" \
    || echo "[-] $1"

find "$path" -size 0 -delete 2> /dev/null
rm "${path}.listing" 2> /dev/null
rmdir "$path" 2> /dev/null

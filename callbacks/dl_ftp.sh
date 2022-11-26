#!/usr/bin/env bash

path=~/storage/shared/Download/FTP/Files/"$1"/

wg(){
    wget -e robots=off --tries=1 --connect-timeout=1 --read-timeout=5 "$@"
}

download_recursive() {
    local uri="$1"
    local extensions="$2"
    local destination="$3"

    wg --timestamping --no-netrc -r -X '/bin' -np -nd -Q 100M -A "$extensions" -P "$destination" "$uri"
}

echo "[*] + $1"

download_recursive \
    "ftp://$1:$2" \
    'jpg,jpeg,png,gif,bmp,sql,txt,csv,pdf,pcap' \
    "$path"

find "$path" -size 0 -delete 2> /dev/null
rm "${path}.listing" 2> /dev/null
rmdir "$path" 2> /dev/null

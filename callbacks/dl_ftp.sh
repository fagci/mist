#!/usr/bin/env bash

wg(){
    wget -e robots=off --tries=1 --connect-timeout=1 --read-timeout=5 "$@"
}

download_recursive() {
    local uri="$1"
    local extensions="$2"
    local destination="$3"

    wg --timestamping -r -X '/bin' -np -nd -Q 100M -A "$extensions" -P "$destination" "$uri"
}

echo "[*] + $1"
download_recursive "ftp://$1:$2" 'jpg,jpeg,png,gif,bmp,sql,txt,csv,pdf' ~/storage/shared/Download/FTP/Files/"$1"/
echo "[*] - $1"

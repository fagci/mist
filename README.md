# MInimalistic netSTalker tool

## Example loot

See [@netrandom_loot](https://t.me/netrandom_loot)

## Usage

```
mist.py [-h] [-t T] [-w W] [-p P] [-cb CB] [-cbc CBC]

Minimalistic netstalker

options:
  -h, --help  show this help message and exit
  -t T        timeout (s)
  -w W        workers count
  -p P        port
  -cb CB      callback handler
  -cbc CBC    max parallel callbacs
```

## Example

```sh
./mist.py -p 21 -cb ./callbacks/dl_ftp.sh
```

# MInimalistic netSTalker tool

## Example loot

See [@netrandom_loot](https://t.me/netrandom_loot)

## Usage

```

mist.py [-h] [-t T] [-w W] [-p P] [-cb CB] [-i I] [-cbc CBC] [-si SI]

Minimalistic netstalker

options:
  -h, --help  show this help message and exit
  -t T        timeout (s)
  -w W        workers count
  -p P        port
  -cb CB      callback handler
  -i I        interface to use
  -cbc CBC    max parallel callbacs
  -si SI      stats interval
```

## Example

```sh
./mist.py -p 21 -cb ./callbacks/dl_ftp.sh
```

## Stats

```
./mist.py -p 80 -cb /dev/null -si 60 -w 1024

# after 60 s:

Total: 112464
Found: 1956 (1.7%)
  100 ms: 490 (25.1%)
  200 ms: 552 (28.2%)
  300 ms: 561 (28.7%)
  400 ms: 337 (17.2%)
  500 ms: 15 (0.8%)
  600 ms: 1 (0.1%)
Errors: 110508 (98.3%)
  [Errno 101] Network is unreachable: 126 (0.1%)
  [Errno 111] Connection refused: 1727 (1.5%)
  [Errno 113] No route to host: 1323 (1.2%)
  timed out: 107332 (95.4%)
```

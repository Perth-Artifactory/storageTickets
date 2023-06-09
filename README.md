# storageTickets
QoL improvements to the way members leave projects in the space

## Setup

* `pip install -r requirements.txt`
* `cp config.json.example config.json`
* Set `config.json` parameters
  * `tidyauth_token` - Token for [tidyauth](https://github.com/Perth-Artifactory/tidyauth)
  * `tidyauth_address` - Address where tidyauth can be reached
  * `logo` - The logo for the top of the receipt inside `img/`
  * `events` - URL to a JSON containing upcoming events. Can be generated by [a utility script](https://github.com/Perth-Artifactory/util#unauthenticated-google-calendar-feed)
* Point to your printer
  * Find your vendor and device IDs using `lsusb`
  * `cp printer.py.example printer.py`
  * Add your IDs in place of `1234` in `printer.py`

## Running

Pretty much needs to be run as a service as root.

* `listen.py`
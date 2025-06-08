# DMR Contact CSV Generator
## Purpose

Many radios have a limited amount of space to process the global DMR database.
And some websites are charging money to customize the data set.
This script is a free way to shrink the data set.

Thanks to https://w1aex.com/dmrid/dmrid.html for dcumenting a similar manual process!
This script reduces toil in a similar way with some simple text manipulation.

For the input file, download one of the following:
https://radioid.net/static/users.json (Preferred)
https://radioid.net/static/user.csv (Standard)

### Usage Examples
#### Shrink the users.json file
python3 dmr-id-csv.py -f users.json -w smaller-users.csv -t json
#### Shrink the user.csv file
python3 dmr-id-csv.py -f user.csv -w smaller-users.csv -t csv


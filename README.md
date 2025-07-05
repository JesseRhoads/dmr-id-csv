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

#### Shrink the users.json file, merging name fields and shifting one column (for some radios like the RT-4D)
python3 dmr-id-csv.py -f users.json -w smaller-users.csv -t json -m -s

#### Shrink the user.csv file
python3 dmr-id-csv.py -f user.csv -w smaller-users.csv -t csv

### Country and State Mappings
The script will use ISO State and Country mappings to shrink the data to 2-letter state and 3-letter country.
However, the user input in the data is unsanitized. So some countries will likely not match.
To work around this, there is a manual mapping that we can add to correct any mappings where the first-three-letter assumption is incorrect.
See the country_map in the fix_country method.

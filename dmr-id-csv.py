#!/bin/env python3
# DMR Contact CSV Generator
# Maintainer: Jesse Rhoads
# Thanks to https://w1aex.com/dmrid/dmrid.html for dcumenting a similar manual process!
# Many radios have a limited amount of space to process the global DMR database.
# And some websites are charging money to customize the data set.
# This script is a free way to shrink the data set.
# This reduces toil with some simple text manipulation.

# For the input file, download one of the following:
# https://radioid.net/static/user.csv
# https://radioid.net/static/users.json

import argparse
import csv
import logging
import os
import signal
import pycountry
import json
import re
import sys
import us
from collections import defaultdict

# Simple 'what are we' to use for later
prog_name = "dmrids"
prog_description = "Shrinks the DMR ID DB CSV to fit in smaller memory."

# Set up Logging to stderr/stdout
log = logging.getLogger()


class DataRow:
    def __repr__(self):
        return str(
            f"{self.radio_id},{self.callsign},{self.fname},{self.lname},{self.city},{self.state},{self.country}"
        )

    def compress(self):
        # Combine name into one field and limit to 16 chars
        name = f"{self.fname} {self.lname}"[0:16]
        self.name = name.split(" ")
        self.fname = self.name[0]
        if len(self.name) < 2:
            self.name.append("")
        if len(self.name) > 2:
            self.lname = self.name.pop()
        else:
            self.lname = self.name[1]
        # Reduce Country name into 3 chars
        raw_country = self.country
        try:
            country = pycountry.countries.get(name=raw_country).alpha_3
            log.debug(f"Converted {raw_country} to {country}")
        except:
            country = self.fix_country(raw_country)
        self.country = country
        # Make State name 2-letter if USA
        if self.country == "USA":
            if self.state == "District Of Columbia":
                self.state = "DC"
            if self.state:
                try:
                    state = us.states.lookup(self.state).abbr
                    log.debug(f"Fixed state {self.state} to {state}")
                    self.state = state
                except:
                    state = self.state[0:3]
                    log.debug(f"Unable to find {self.state}, using {state}")
                    self.state = state
        else:
            # Limit state to 3 characters
            state = self.state[0:3]
            self.state = state
        # Limit city to 9 chars
        city = self.city[0:9].strip()
        self.city = city
        log.debug(f"Compressed row {self.radio_id}")

    def fix_country(self, raw_country):
        country_map = {
            "U.S. Virgin Islands": "UVI",
            "British Virgin Islands": "BVI",
            "Falkland Islands": "FLK",
            "México": "MEX",
            "St. Vincent and Grenada": "VCT",
            "Taiwan": "TWN",
            "Vietnam": "VNM",
        }
        found = country_map.get(raw_country, False)
        if found:
            log.debug(f"Country {raw_country} found in map, setting {found}")
            return found
        else:
            country = raw_country[0:3].upper()
            log.debug(f"Country {raw_country} not found, setting {country}")
            return country

    def to_dict(self):
        return {
            "RADIO_ID": self.radio_id,
            "CALLSIGN": self.callsign,
            "FIRST_NAME": self.fname,
            "LAST_NAME": self.lname,
            "CITY": self.city,
            "STATE": self.state,
            "COUNTRY": self.country,
        }

    def __init__(self, radio_id, call, fname, lname, city, state, country):
        # RT-4D expects RADIO_ID,CALLSIGN,FIRST_NAME,LAST_NAME,CITY,STATE,COUNTRY.
        self.radio_id = radio_id
        self.callsign = call
        self.fname = fname
        self.lname = lname
        self.city = city
        self.state = state
        self.country = country
        self.compress()


class DMR:
    # We use this function when the thing we want to process is only one line at a time.
    # For cases where the data spans multiple lines, we don't do this, we use a generator further down.
    def parse_json_input(self):
        # Open and read the JSON file
        with open(self.args.my_file, "r") as file:
            data = json.load(file)
        return data

    def parse_csv_input(self):
        # CSV Fields: RADIO_ID,CALLSIGN,FIRST_NAME,LAST_NAME,CITY,STATE,COUNTRY
        data = []
        users = []
        total = 0
        with open(self.args.my_file) as input:
            for unsanitized_line in input:
                line = unsanitized_line.strip().rstrip("\r").replace("^M", "")
                total += 1
                if line == "":
                    continue
                if total == 1:
                    continue
                if self.args.limit:
                    if total >= self.args.limit:
                        break
                else:
                    data.append(line)
        # CSV already has the fields, so we can start making DataRows
        #        row = DataRow(radio_id, callsign, fname, lname, city, state, countr
        for line in data:
            log.debug(f"line {line}")
            row = line.split(",")
            my_row = DataRow(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            log.debug(f"Made row {row}")
            self.seen_countries[my_row.country] += 1
            self.rows.append(my_row.to_dict())
        log.info(f"Total lines parsed: {total}")
        log.info(f"Entries by Country: {self.seen_countries}")

    def parse_json_data(self, data):
        total = 0
        for user in data["users"]:
            self.parse_user(user)
            total += 1
            if self.args.limit:
                if total >= self.args.limit:
                    break
        log.info(f"Total lines parsed: {total}")
        log.info(f"Countries: {self.seen_countries}")

    # Example user object in the JSON:
    #   "fname": "Jesse",
    #   "name": "Jesse",
    #   "country": "United States",
    #   "callsign": "KE4CQE",
    #   "city": "Orlando",
    #   "surname": "Rhoads",
    #   "radio_id": 3211024,
    #   "id": 3211024,
    #   "state": "Florida",

    def parse_user(self, user):
        fname = user.get("name").strip()
        lname = user.get("surname").strip()
        if lname not in fname:
            name = "f{fname} {lname}"
        else:
            name = fname
        country = user.get("country")
        state = user.get("state")
        city = user.get("city")
        callsign = user.get("callsign")
        radio_id = user.get("radio_id")
        row = DataRow(radio_id, callsign, fname, lname, city, state, country)
        log.debug(f"Made row {row}")
        self.seen_countries[row.country] += 1
        self.rows.append(row.to_dict())

    def write_csv(self):
        # log.debug(f"Rows: {self.rows}")
        with open(self.args.csv_out, "w", newline="") as csvfile:
            fieldnames = list(self.rows[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)

    def __init__(self, args):
        self.args = args
        self.rows = []
        self.seen_countries = defaultdict(int)


# Let's Get our command line parameters
def get_parameters():
    parser = argparse.ArgumentParser(description=prog_description)
    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        default=False,
        help="Enable Debug Logging",
        action="store_true",
    )

    parser.add_argument(
        "-f",
        "--file",
        dest="my_file",
        help="File to load",
        required=True,
    )
    parser.add_argument(
        "-w",
        "--write",
        dest="csv_out",
        help="File to write",
    )
    parser.add_argument(
        "-t",
        "--type",
        dest="file_type",
        choices=["csv", "json"],
        default="json",
        help="csv or json",
    )
    parser.add_argument(
        "-l",
        "--limit",
        dest="limit",
        type=int,
        help="Number of records to load",
    )

    return parser.parse_args()


def main():
    cli_args = get_parameters()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    log.addHandler(stdout_handler)

    if cli_args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    log.debug(f"{prog_name} Starting up. Arguments: {cli_args}")
    # Set up a managment object to handle scope more readily.
    dmr_csv = DMR(cli_args)

    # Initialize whatever else here.
    if cli_args.file_type == "json":
        data = dmr_csv.parse_json_input()
        csv = dmr_csv.parse_json_data(data)
    else:
        dmr_csv.parse_csv_input()

    if cli_args.csv_out:
        dmr_csv.write_csv()


if __name__ == "__main__":
    main()

#!/usr/bin/python
# abeebus.py 1.1 - A GeoIP lookup utility utilizing ipinfo.io services.
# Compatible with Python 2 and 3
# Copyright 2016 13Cubed. All rights reserved. Written by: Richard Davis

import sys
import json
import re
import csv
import argparse

# Handle Python 2 and 3 compatibility for urllib
try:
  from urllib.request import urlopen
except ImportError:
  from urllib2 import urlopen

def getData(filenames, sortByFirstOctet):
  """
  The given file is scraped for IPv4 addresses, and the addresses are used
  with the GeoIP location provider to obtain location data in JSON format.
  The JSON data is then parsed and appended to the 'results' list.
  """

  addresses = []
  filteredAddresses = []
  results = ['IP Address,Hostname,Country,Region,City,Postal Code,Latitude,Longitude,ASN']

  for filename in filenames:
    try:
      f = open(filename, 'rU')
    except IOError:
      print ('Could not find the specified file:', filename)
      sys.exit(1)

    # Parse file for valid IPv4 addresses via RegEx
    addresses += re.findall(r'(\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b)',f.read())
    f.close()

  # Remove duplicates from list
  addresses = set(addresses)

  # Filter list to eliminate bogon addresses, the loopback network, link local addresses, and RFC 1918 ranges; add results to new list
  for address in addresses:
    if not (re.match(r'^0.\d{1,3}.\d{1,3}.\d{1,3}$|^127.\d{1,3}.\d{1,3}.\d{1,3}$|^169.254.\d{1,3}.\d{1,3}$|^10.\d{1,3}.\d{1,3}.\d{1,3}$|^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$|^192.168.\d{1,3}.\d{1,3}$', address)):
      filteredAddresses.append(address)

  if (sortByFirstOctet == 1):
    # Sort filtered addresses ascending by first octet
    for i in range(len(filteredAddresses)):
      filteredAddresses[i] = '%3s.%3s.%3s.%3s' % tuple(filteredAddresses[i].split('.'))
      filteredAddresses.sort()
    for i in range(len(filteredAddresses)):
      filteredAddresses[i] = filteredAddresses[i].replace(' ', '')

  # Iterate through new list and obtain GeoIP information from ipinfo.io
  for filteredAddress in filteredAddresses:
    formattedData = ''
    # Build query URL from found addresses
    url = ('https://ipinfo.io/' + filteredAddress + '/json')

    try:
      rawData = urlopen(url).read()
    except URLError as err:
      print ('\nError contacting GeoIP provider: ' + str(err.reason) + '\n')
      sys.exit(1)

    rawData = json.loads(rawData.decode('utf-8'))

    keys = ['ip','hostname','country','region','city','postal','loc','org']

    for key in keys:
      try:
        if not (key == 'loc'):
          # Strip commas from raw data unless lat/long (loc) key; add a comma at the end of the value
          formattedData += rawData[key].replace(',','') + ','
        else:
          # Add a comma at the end of the value
          formattedData += rawData[key] + ','
      except:
        # If key is missing, add space and comma to move to next field in the CSV
        formattedData += ' ,'

    # Strip trailing comma
    formattedData = formattedData.strip(',')

    # Add final formatted data string to list
    results.append(formattedData)

  return results

def printData(results):
  rows = list(csv.reader(results))
  widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]

  for row in rows:
    print(' | '.join(cell.ljust(width) for cell, width in zip(row, widths)))

def writeData(results,outfile):
  try:
    f = open(outfile, 'w')
  except IOError:
    print ('Could not write the specified file:', outfile)
    sys.exit(1)

  for result in results:
    f.write(result + '\n')

  f.close()

def main():
  parser = argparse.ArgumentParser(description='Abeebus - A GeoIP lookup utility utilizing ipinfo.io services.', usage='abeebus.py filename(s) [-w outfile] [-s]', add_help=False)
  parser.add_argument('filenames', nargs="*")
  parser.add_argument('-w','--write', help='Write output to CSV file instead of stdout', required=False)
  parser.add_argument('-s','--sort', action='store_true', help='Sort addresses ascending by first octet', required=False)
  parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
  args = vars(parser.parse_args())

  # Make sure at least one filename was provided
  if not (args['filenames']):
    parser.print_usage()
    parser.exit()

  filenames = args['filenames']
  writeToFile = 0
  sortByFirstOctet = 0

  if (args['write']):
    writeToFile = 1
    outfile = args['write']

  if (args['sort']):
    sortByFirstOctet = 1

  output = getData(filenames,sortByFirstOctet)

  if (writeToFile == 1):
    writeData(output,outfile)

  else:
    printData(output)

  print ('\nCopyright (C) 2016 13Cubed. All rights reserved.')

if __name__ == '__main__':
  main()

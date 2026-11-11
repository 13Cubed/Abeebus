#!/usr/bin/python3
# Abeebus 2.2 - A GeoIP lookup utility utilizing ipinfo.io services.
# Copyright 2026 13Cubed. All rights reserved. Written by: Richard Davis
#
# Options, output and address filtering are unchanged from 2.0. The changes in
# 2.1 were internal: files are streamed rather than read whole, so arbitrarily
# large images can be processed, and lookups reuse a single connection with
# retry and backoff. In 2.2, stdout carries the results and nothing else, so
# that redirecting it yields just the table; the progress bar, diagnostics,
# errors and the copyright notice go to stderr. On screen nothing moves.

import sys
import json
import re
import csv
import os
import time
import socket
import http.client
import argparse

VERSION = '2.2'
USER_AGENT = 'Abeebus/' + VERSION

API_HOST = 'ipinfo.io'
HTTP_TIMEOUT = 30
HTTP_RETRIES = 3
HTTP_BACKOFF = 1.0
# A quota limit will not clear in a few seconds, so a 429 ends the retries
# early rather than spending more requests on an exhausted quota
RATE_LIMIT_ATTEMPTS = 2

# Valid IPv4 addresses. Compiled once because findAddresses needs to search
# from a given offset rather than from the start of a string.
ADDRESS_REGEX = re.compile(r'(\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b)')

READ_BUFFER = 65536
# The longest address the RegEx can match is 15 characters ("255.255.255.255"),
# so nothing spanning a read boundary can be longer than this
MAX_ADDRESS_LENGTH = 15

def findAddresses(filename, bufferSize=READ_BUFFER):
  """
  Yield each IPv4 address in the given file, in the order encountered. The file
  is streamed so that large images are not read into memory all at once, while
  producing exactly what a scan of the whole file would produce.

  This mirrors how a whole-file scan behaves: search from a position, emit the
  leftmost match, resume from the end of that match. Searching with an offset
  matters, because unlike slicing the buffer it still evaluates the leading
  word boundary against the preceding character. Slicing would let the RegEx
  group a run of digits and dots differently than a whole-file scan would,
  silently changing which addresses are reported. A match touching the end of a
  non-final read may be cut off mid address, so it is held back.

  ISO-8859-1 maps every byte to one character, so any file reads without error.
  """
  buffer = ''
  bufferStart = 0
  position = 0

  with open(filename, 'r', encoding='ISO-8859-1', newline='') as f:
    while True:
      chunk = f.read(bufferSize)
      final = not chunk
      buffer += chunk

      pendingStart = None
      while True:
        match = ADDRESS_REGEX.search(buffer, position - bufferStart)
        if match is None:
          break
        if not final and match.end() == len(buffer):
          pendingStart = bufferStart + match.start()
          break

        yield match.group(0)
        position = bufferStart + match.end()

      if final:
        return

      if pendingStart is not None:
        # Nothing matches before the pending match, so resume there
        position = max(position, pendingStart)
      else:
        # No complete match remains, so an address crossing the end of the
        # buffer must begin within the last MAX_ADDRESS_LENGTH characters
        position = max(position, bufferStart + len(buffer) - MAX_ADDRESS_LENGTH)

      # Keep one character before the resume point so that the next search can
      # still evaluate the leading word boundary correctly
      discard = max(0, position - bufferStart - 1)
      if discard:
        buffer = buffer[discard:]
        bufferStart += discard

class LookupFailed(Exception):
  """
  A lookup could not be completed. The reason is 'limit' for rate limiting,
  'auth' for a rejected token, or 'error' for anything else.
  """
  def __init__(self, reason):
    Exception.__init__(self, reason)
    self.reason = reason

class GeoIPLookup:
  """
  Holds one connection open across all lookups rather than building a new one
  per address, and backs off on rate limiting and server errors.
  """
  def __init__(self, apiToken):
    self.connection = None
    self.headers = {'Accept': 'application/json', 'User-Agent': USER_AGENT}

    if apiToken:
      # Sent as a header rather than in the URL so that the token stays out of
      # proxy logs and error messages
      self.headers['Authorization'] = 'Bearer ' + apiToken

  def close(self):
    if self.connection is not None:
      try:
        self.connection.close()
      except Exception:
        pass

      self.connection = None

  def get(self, address):
    rateLimited = False

    for attempt in range(HTTP_RETRIES):
      try:
        if self.connection is None:
          self.connection = http.client.HTTPSConnection(API_HOST, timeout=HTTP_TIMEOUT)

        self.connection.request('GET', '/' + address + '/json', headers=self.headers)
        response = self.connection.getresponse()
        status = response.status
        body = response.read()

        if (status == 200):
          try:
            rawData = json.loads(body.decode('utf-8', errors='replace'))
          except ValueError:
            raise LookupFailed('error')

          if not isinstance(rawData, dict):
            raise LookupFailed('error')

          return rawData

        # A rejected token cannot be retried, and neither can an unusable
        # request such as a token containing a newline
        if (status == 401 or status == 403):
          raise LookupFailed('auth')

        if (status == 429):
          rateLimited = True
        elif (status < 500):
          raise LookupFailed('error')

      except ValueError:
        # An unusable request, such as a token containing a newline
        raise LookupFailed('auth')

      except (http.client.HTTPException, socket.timeout, OSError):
        pass

      self.close()

      if (rateLimited and attempt >= RATE_LIMIT_ATTEMPTS - 1):
        break

      if (attempt < HTTP_RETRIES - 1):
        time.sleep(HTTP_BACKOFF * (2 ** attempt))

    raise LookupFailed('limit' if rateLimited else 'error')

def addressSortKey(address):
  # Numeric, so that 9.9.9.9 sorts before 45.33.32.156
  octets = [int(octet) for octet in address.split('.')]
  return (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]

def cleanValue(value):
  # The output is unquoted CSV, so a comma or a quote would shift the columns,
  # and a newline would split the row in two
  return re.sub(r'[\x00-\x1f\x7f-\x9f\u2028\u2029]', ' ', value.replace(',', '').replace('"', ''))

def getData(filenames, apiToken):
  """
  The given file is scraped for IPv4 addresses, and the addresses are used
  with the GeoIP location provider to obtain location data in JSON format.
  The JSON data is then parsed and appended to the 'results' list.
  """
  from collections import Counter

  addressCounts = Counter()
  filteredAddresses = []
  results = []
  seen = set()
  aborted = False

  for filename in filenames:
    # Skip a file named more than once so its addresses are not counted twice
    try:
      key = os.path.normcase(os.path.realpath(filename))
    except OSError:
      key = os.path.normcase(filename)

    if key in seen:
      continue

    seen.add(key)

    # Open each specified file for processing, and parse it for valid IPv4
    # addresses via RegEx
    try:
      addressCounts.update(findAddresses(filename))
    except IOError:
      print('Could not find the specified file:', filename, file=sys.stderr)
      sys.exit(1)

  # Filter list to eliminate the loopback network, link local addresses, RFC 1918 ranges, and the 0.0.0.0/8 range; add results to new list
  for address in addressCounts:
    if not (re.match(r'^0.\d{1,3}.\d{1,3}.\d{1,3}$|^127.\d{1,3}.\d{1,3}.\d{1,3}$|^169.254.\d{1,3}.\d{1,3}$|^10.\d{1,3}.\d{1,3}.\d{1,3}$|^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$|^192.168.\d{1,3}.\d{1,3}$', address)):
      filteredAddresses.append(address)

  # Sort by address so that equal counts always come out in the same order
  filteredAddresses.sort(key=addressSortKey)

  total = len(filteredAddresses)
  i = 0

  lookup = GeoIPLookup(apiToken)

  # Iterate through new list and obtain GeoIP information from ipinfo.io
  for filteredAddress in filteredAddresses:
    # Show progress bar
    progressBar(i, total, status='Getting Results')
    i += 1

    formattedData = ''

    try:
      rawData = lookup.get(filteredAddress)
    except LookupFailed as error:
      # Whatever was resolved before the failure is still worth reporting, so
      # that a long scan and the requests it already spent are not wasted. The
      # results speak for themselves, so only say when there are none.
      resolved = len(results)
      noResults = '' if resolved else ' No results to show.'

      if (error.reason == 'limit'):
        print('\n\nipinfo.io rate limit reached after', format(resolved, ','), 'of',
          format(total, ','), 'addresses.' + noResults, file=sys.stderr)

        if apiToken:
          print('This API token has no requests left for the current period.', file=sys.stderr)
        else:
          print('Unauthenticated requests allow 1,000 per day. Use -a to specify an API token.', file=sys.stderr)

      elif (error.reason == 'auth' and apiToken):
        print('\n\nipinfo.io rejected the API token.' + noResults, file=sys.stderr)

      else:
        # The address ends the line, so a period after it would read as part of
        # the address. Put the outcome on its own line instead.
        print('\nError parsing address:', filteredAddress, file=sys.stderr)

        if not resolved:
          print('No results to show.', file=sys.stderr)

      aborted = True
      break

    keys = ['ip','hostname','country','region','city','postal','loc','org']

    for key in keys:
      try:
        # If the key exists but is null, set its value to 'N/A'
        if (rawData[key] == ""):
          rawData[key] = 'N/A'

        # If the key is loc, split the value into the latitude and longitude columns
        if (key == 'loc'):
          latitude, separator, longitude = rawData[key].partition(',')
          formattedData += (cleanValue(latitude) or 'N/A') + ','
          formattedData += (cleanValue(longitude) or 'N/A') + ','
        # If the key is anything else, strip the commas from the value, then add a trailing comma to the end of the value
        else:
          formattedData += cleanValue(rawData[key]) + ','

      except Exception:
        # If the loc key is missing, add 'N/A,N/A' and a trailing comma
        if (key == 'loc'):
          formattedData += 'N/A,N/A,'
        # If any other key is missing, add 'N/A' and a trailing comma
        else:
          formattedData += 'N/A,'

    # Get number of occurrences for IP address and add to results
    addressCount = addressCounts[filteredAddress]
    formattedData += str(addressCount)

    # Add final formatted data string to list
    results.append(formattedData)

  # Finish the progress bar so that a completed run does not end short. The bar
  # leaves the cursor at the start of its line, so on a terminal the results
  # overwrite it; with -w it is the last thing on screen.
  if (total > 0 and not aborted):
    progressBar(total, total, status='Getting Results')

  lookup.close()

  # Sort results from highest count to lowest
  results = sorted(results, key=lambda x: int(x.split(',')[9]), reverse=True)

  # Add column headers
  results.insert(0,'IP Address,Hostname,Country,Region,City,Postal Code,Latitude,Longitude,ASN,Count')

  return results, aborted

def printData(results):
  rows = list(csv.reader(results))
  widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]

  for row in rows:
    print(' | '.join(cell.ljust(width) for cell, width in zip(row, widths)))

def writeData(results,outfile):
  try:
    # Written as UTF-8 with a BOM. Without it, Excel assumes the local codepage
    # and renders non-ASCII city and org names as mojibake.
    f = open(outfile, 'w', encoding='utf-8-sig')
  except IOError:
    print('Could not write the specified file:', outfile, file=sys.stderr)
    sys.exit(1)

  try:
    for result in results:
      # While Unicode characters will not be displayed via stdout, they will be written to the file
      f.write(result + '\n')
  except IOError:
    print('Could not write the specified file:', outfile, file=sys.stderr)
    sys.exit(1)
  finally:
    f.close()

def progressBar(count, total, status=''):
  # From https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
  bar_len = 60
  filled_len = int(round(bar_len * count / float(total)))

  percents = round(100.0 * count / float(total), 1)
  bar = '#' * filled_len + '.' * (bar_len - filled_len)

  # Pad to a constant width so that each redraw fully covers the frame before
  # it. Frames grow as the percentage does, so a shorter one drawn over a
  # longer one would otherwise leave its tail on screen.
  line = '[%s] %s%s ...%s' % (bar, percents, '%', status)

  # Drawn on stderr. The carriage return is meant for a terminal, and on stdout
  # it would be written into a redirected file along with the results.
  sys.stderr.write(line.ljust(bar_len + len(status) + 13) + '\r')
  sys.stderr.flush()

def main():
  # GeoIP results routinely contain non-ASCII city and org names, and so can a
  # filename in an error message. Some consoles cannot encode them, so
  # substitute rather than fail; -w still writes them intact as UTF-8.
  for stream in (sys.stdout, sys.stderr):
    try:
      stream.reconfigure(errors='replace')
    except (AttributeError, ValueError):
      pass

  parser = argparse.ArgumentParser(description='Abeebus ' + VERSION + ' - A GeoIP lookup utility utilizing ipinfo.io services.', usage='abeebus.py filename(s) [-w outfile] [-a token]', add_help=False)
  parser.add_argument('filenames', nargs="*")
  parser.add_argument('-w', '--write', help='Write output to CSV file instead of stdout', required=False)
  parser.add_argument('-a', '--api-token', help='Specify ipinfo.io API token', required=False)
  parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
  args = vars(parser.parse_args())

  # Make sure at least one filename was provided
  if not (args['filenames']):
    parser.print_usage()
    parser.exit()

  filenames = args['filenames']
  writeToFile = 0
  apiToken = ""

  if (args['write']):
    writeToFile = 1
    outfile = args['write']

  if (args['api_token']):
    apiToken = args['api_token'].strip()

  output, aborted = getData(filenames,apiToken)

  # A run that resolved nothing has no results worth showing, and writing a
  # header only file would destroy the output of an earlier successful run
  showResults = not (aborted and len(output) <= 1)

  if (showResults and writeToFile == 1):
    writeData(output,outfile)

    # Nothing was printed over the progress bar, so end its line. A run with
    # no addresses never drew one, and an aborted run already ended it.
    if (not aborted and len(output) > 1):
      print(file=sys.stderr)

  elif showResults:
    # The results normally overwrite the progress bar, but an abort message
    # will have broken that up, so separate them
    if aborted:
      print(file=sys.stderr)

    printData(output)

  print('\nCopyright (C) 2026 13Cubed. All rights reserved.', file=sys.stderr)

  if aborted:
    sys.exit(1)

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    sys.exit(130)
  except BrokenPipeError:
    try:
      sys.stdout.close()
    except Exception:
      pass
    sys.exit(0)

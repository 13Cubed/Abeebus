# Abeebus
Abeebus is a GeoIP lookup utility utilizing [ipinfo.io](https://ipinfo.io) services. This script is very useful for parsing email headers, small log files, and any other arbitrary data for IPv4 addresses. For any given file, Abeebus will:

- Extract valid IPv4 addresses (e.g., "CSI: Cyber" addresses like 951.27.9.840 will not match)
- Ignore duplicates
- Ignore RFC 1918 addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and the loopback network (127.0.0.0/8)

For each remaining address, Abeebus will sort the addresses numerically by the first octet and provide the following data as available from ipinfo.io:

- IP Address, Hostname, Country, Region, City, Postal Code, Latitude, Longitude, ASN

By default, Abeebus will display the data to stdout in the following format:

`IP Address   | Hostname    | Country | Region     | City      | Postal Code | Latitude | Longitude | ASN`
`17.178.96.59 | No Hostname | US      | California | Cupertino | 95014       | 37.3230  | -122.0322 | AS714 Apple Inc.`

Using the "-w" option, you can provide a filename to which Abeebus will output the data in CSV format:

`IP Address,Hostname,Country,Region,City,Postal Code,Latitude,Longitude,ASN`
`17.178.96.59,imoviegallery.com,US,California,Cupertino,95014,37.3230,-122.0322,AS714 Apple Inc.`

This is useful for working with large data sets in Microsoft Excel or LibreOffice Calc.

**Abeebus does not use any external libraries, and is compatible with Python 2 and 3.**

# Abeebus
Abeebus is a GeoIP lookup utility utilizing ipinfo.io services. This script is very useful for parsing email headers, small log files, and any other arbitrary data for IPv4 addresses. For any given file, Abeebus will:

- Extract valid IPv4 addresses (e.g., "CSI Cyber" IP addresses like 192.386.1.100 will not match)
- Remove duplicates
- Filter out RFC 1918 addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and the loopback network (127.0.0.0/8)

And for each remaining address, Abeebus will provide the following data as available from ipinfo.io:

- IP Address, Hostname, Country, Region, City, Postal Code, Latitude, Longitude, ASN

By default, Abeebus will display the data to stdout in the following format:

IP Address   | Hostname    | Country | Region     | City      | Postal Code | Latitude | Longitude | ASN             
17.178.96.59 | No Hostname | US      | California | Cupertino | 95014       | 37.3230  | -122.0322 | AS714 Apple Inc.

Using the "-w" option, you can provide a filename to which Abeebus will output the data in CSV format. This is useful for working with large data sets in Microsoft Excel or LibreOffice Calc.

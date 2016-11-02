# Abeebus
**Abeebus is a GeoIP lookup utility utilizing [ipinfo.io](https://ipinfo.io) services. This script is very useful for parsing email headers, small log files, and any other arbitrary data for IPv4 addresses.**

For any given file, Abeebus will:

- Extract valid IPv4 addresses (e.g., "CSI: Cyber" addresses like 951.27.9.840 will not match)
- Ignore duplicates
- Ignore RFC 1918 addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and the loopback network (127.0.0.0/8)

For each remaining address, Abeebus will provide the following data as available from ipinfo.io:

**- IP Address, Hostname, Country, Region, City, Postal Code, Latitude, Longitude, ASN**

By default, Abeebus will display the data to stdout in the following format:

```
IP Address    | Hostname                                  | Country | Region   | City    | Postal Code | Latitude | Longitude | ASN
52.73.116.225 | ec2-52-73-116-225.compute-1.amazonaws.com | US      | Virginia | Ashburn | 20149       | 39.0437  | -77.4875  | AS14618 Amazon.com Inc.
```
- Using the "**-w**" option, you can provide a filename to which Abeebus will output the data in CSV format (useful for working with large data sets in Microsoft Excel or LibreOffice Calc):

```
IP Address,Hostname,Country,Region,City,Postal Code,Latitude,Longitude,ASN
52.73.116.225,ec2-52-73-116-225.compute-1.amazonaws.com,US,Virginia,Ashburn,20149,39.0437,-77.4875,AS14618 Amazon.com Inc.
```

- Using the "**-s**" option, Abeebus will sort the addresses numerically by the first octet.

**Abeebus does not use any external libraries, and is compatible with Python 2 and 3.**

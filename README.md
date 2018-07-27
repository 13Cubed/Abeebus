# Abeebus
**Abeebus is a GeoIP lookup utility utilizing [ipinfo.io](https://ipinfo.io) services. This script is very useful for parsing email headers, log files, and any other arbitrary data for IPv4 addresses, and then GeoIP data for each of those addresses using ipinfo.io.**

**Video Demo:**

[![Parse Email Headers and Files for GeoIP Location Data](https://img.youtube.com/vi/ZjcASJCf2mA/0.jpg)](https://www.youtube.com/watch?v=ZjcASJCf2mA)

For any given file(s), Abeebus will:

- Extract valid IPv4 addresses (e.g., "CSI: Cyber" addresses like 951.27.9.840 will not match)
- Ignore duplicates
- Ignore bogon addresses, the loopback network, link local addresses, and RFC 1918 ranges

For each remaining address, Abeebus will provide the following data as available from ipinfo.io:

**- IP Address, Hostname, Country, Region, City, Postal Code, Latitude, Longitude, ASN, Count**

By default, Abeebus will display the data to stdout in the following format:

```
IP Address    | Hostname                                  | Country | Region   | City    | Postal Code | Latitude | Longitude | ASN                     | Count
52.73.116.225 | ec2-52-73-116-225.compute-1.amazonaws.com | US      | Virginia | Ashburn | 20149       | 39.0437  | -77.4875  | AS14618 Amazon.com Inc. | 5
```
- Using the "**-w**" option, you can provide a filename to which Abeebus will output the data in CSV format (useful for working with large data sets in Microsoft Excel or LibreOffice Calc):

```
IP Address,Hostname,Country,Region,City,Postal Code,Latitude,Longitude,ASN,Count
52.73.116.225,ec2-52-73-116-225.compute-1.amazonaws.com,US,Virginia,Ashburn,20149,39.0437,-77.4875,AS14618 Amazon.com Inc.,5
```

- Using the "**-s**" option, Abeebus will sort the addresses numerically by the first octet.

**Abeebus does not use any external libraries, and is compatible with Python 2 and 3.**

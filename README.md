# Abeebus
**Abeebus is a GeoIP lookup utility utilizing [ipinfo.io](https://ipinfo.io) services. This script is very useful for parsing email headers, log files, and any other arbitrary data for IPv4 addresses, and then obtaining GeoIP data for each of those addresses.**

**Video Demo:**

[![Parse Email Headers and Files for GeoIP Location Data](https://img.youtube.com/vi/egv63oso8Qc/0.jpg)](https://www.youtube.com/watch?v=egv63oso8Qc)

For any given file(s), Abeebus will:

- Extract valid IPv4 addresses (e.g., "CSI: Cyber" addresses like 951.27.9.840 will not match)
- Ignore duplicates
- Ignore bogon addresses, the loopback network, link local addresses, and RFC 1918 (private) addresses

For each remaining address, Abeebus will provide the following data as available from ipinfo.io:

**- IP Address, Hostname, Country, Region, City, Postal Code, Latitude, Longitude, ASN, Count**

By default, Abeebus will display the data to stdout in the following format:

```
IP Address    | Hostname                                  | Country | Region   | City    | Postal Code | Latitude | Longitude | ASN                     | Count
52.73.116.225 | ec2-52-73-116-225.compute-1.amazonaws.com | US      | Virginia | Ashburn | 20149       | 39.0437  | -77.4875  | AS14618 Amazon.com Inc. | 5
```
- Using the "**-w**" option, you can provide a filename to which Abeebus will output the data in CSV format (useful for working with large data sets in **Timeline Explorer**, **Microsoft Excel**, or **LibreOffice Calc**):

```
IP Address,Hostname,Country,Region,City,Postal Code,Latitude,Longitude,ASN,Count
52.73.116.225,ec2-52-73-116-225.compute-1.amazonaws.com,US,Virginia,Ashburn,20149,39.0437,-77.4875,AS14618 Amazon.com Inc.,5
```
- Using the "**-a**" option, you can provide an **ipinfo.io API** key if you have large datasets to process.

**Abeebus requires Python 3 (no external libraries needed).**

# zonequery
Query all DNS authoritative servers at a zone

Script to query all the authoritative servers for a zone, for a given
query name and type. The default output is a detailed machine parseable
JSON string. The --text option can be used to produce an abbreviated
text based output.

This program can also be invoked as an AWS lambda function via the
lambda_handler() function.

Author: Shumon Huque

## Pre-requisites

* Python3
* Additional modules:
  * dnspython
  * sortedcontainers

## Installation

To install from a local copy of this repository:

```
pip3 install .
```

To install from the git repo directly:

```
pip3 install git+https://github.com/shuque/zonequery.git@v0.3.3
```

## Usage

```
$ zonequery.py -h
usage: zonequery.py [-h] [-v] [-4 | -6] [--bufsize N] [--noedns] [--nsid]
                    [--subnet SUBNET] [--dnssec] [--text] [--timeout N]
                    [--retries N] [--notcpfallback] [--tcp] [--section name]
                    zone qname qtype

Version 0.3.3
Query all nameserver addresses for a given zone, qname, and qtype.

positional arguments:
  zone             DNS zone name
  qname            Query name
  qtype            Query type

optional arguments:
  -h, --help       show this help message and exit
  -v, --verbose    increase output verbosity
  -4               Use IPv4 transport only
  -6               Use IPv6 transport only
  --bufsize N      Set EDNS buffer size in octets (default: 1420)
  --noedns         Don't use EDNS
  --nsid           Send NSID EDNS option
  --subnet SUBNET  EDNS Client Subnet (e.g. 1.2.3.4/24)
  --dnssec         Set DNSSEC-OK bit in queries
  --text           Emit abbreviated text output (default is json)
  --timeout N      Query timeout in secs (default: 3)
  --retries N      Number of UDP retries (default: 2)
  --notcpfallback  Do not fall back to TCP on truncation
  --tcp            Use TCP only (default: UDP with TCP fallback)
  --section name   Specify response section to display (default: all)
```

## Example output

```
$ zonequery.py google.com www.google.com A

{
  "timestamp": 1653357383.3894224,
  "query": {
    "zone": "google.com",
    "qname": "www.google.com",
    "qtype": "A",
    "edns_buf_size": 1420
  },
  "nslist": {
    "ns1.google.com.": [
      "2001:4860:4802:32::a",
      "216.239.32.10"
    ],
    "ns2.google.com.": [
      "2001:4860:4802:34::a",
      "216.239.34.10"
    ],
    "ns3.google.com.": [
      "2001:4860:4802:36::a",
      "216.239.36.10"
    ],
    "ns4.google.com.": [
      "2001:4860:4802:38::a",
      "216.239.38.10"
    ]
  },
  "responses": [
    {
      "name": "ns1.google.com.",
      "ip": "2001:4860:4802:32::a",
      "size": 59,
      "rtt": 8.591,
      "rcode": "NOERROR",
      "flags": "QR AA",
      "id": 4625,
      "short_answers": "142.250.65.164",
      "sections": {
        "answer": [
          {
            "rrname": "www.google.com.",
            "rrtype": "A",
            "ttl": 300,
            "rdata": [
              "142.250.65.164"
            ]
          }
        ]
      }
    },
    {
      "name": "ns1.google.com.",
      "ip": "216.239.32.10",
      "size": 59,
      "rtt": 8.449,
      "rcode": "NOERROR",
      "flags": "QR AA",
      "id": 40003,
      "short_answers": "142.251.40.228",
      "sections": {
        "answer": [
          {
            "rrname": "www.google.com.",
            "rrtype": "A",
            "ttl": 300,
            "rdata": [
              "142.251.40.228"
            ]
          }
        ]
      }
    },
    {
      "name": "ns2.google.com.",
      "ip": "2001:4860:4802:34::a",
      "size": 59,
      "rtt": 15.182,
      "rcode": "NOERROR",
      "flags": "QR AA",
      "id": 32438,
      "short_answers": "142.250.65.164",
      "sections": {
        "answer": [
          {
            "rrname": "www.google.com.",
            "rrtype": "A",
            "ttl": 300,
            "rdata": [
              "142.250.65.164"
            ]
          }
        ]
      }
    },
    {
      "name": "ns2.google.com.",
      "ip": "216.239.34.10",
      "size": 59,
      "rtt": 15.129,
      "rcode": "NOERROR",
      "flags": "QR AA",
      "id": 7611,
      "short_answers": "142.251.40.228",
      "sections": {
        "answer": [
          {
            "rrname": "www.google.com.",
            "rrtype": "A",
            "ttl": 300,
            "rdata": [
              "142.251.40.228"
            ]
          }
        ]
      }
    },
    {
      "name": "ns3.google.com.",
      "ip": "2001:4860:4802:36::a",
      "size": 59,
      "rtt": 14.638,
      "rcode": "NOERROR",
      "flags": "QR AA",
      "id": 57517,
      "short_answers": "142.250.65.164",
      "sections": {
        "answer": [
          {
            "rrname": "www.google.com.",
            "rrtype": "A",
            "ttl": 300,
            "rdata": [
              "142.250.65.164"
            ]
          }
        ]
      }
    },
    {
      "name": "ns3.google.com.",
      "ip": "216.239.36.10",
      "size": 59,
      "rtt": 15.393,
      "rcode": "NOERROR",
      "flags": "QR AA",
      "id": 24607,
      "short_answers": "142.251.40.228",
      "sections": {
        "answer": [
          {
            "rrname": "www.google.com.",
            "rrtype": "A",
            "ttl": 300,
            "rdata": [
              "142.251.40.228"
            ]
          }
        ]
      }
    },
    {
      "name": "ns4.google.com.",
      "ip": "2001:4860:4802:38::a",
      "size": 59,
      "rtt": 8.974,
      "rcode": "NOERROR",
      "flags": "QR AA",
      "id": 44152,
      "short_answers": "142.250.65.164",
      "sections": {
        "answer": [
          {
            "rrname": "www.google.com.",
            "rrtype": "A",
            "ttl": 300,
            "rdata": [
              "142.250.65.164"
            ]
          }
        ]
      }
    },
    {
      "name": "ns4.google.com.",
      "ip": "216.239.38.10",
      "size": 59,
      "rtt": 8.613,
      "rcode": "NOERROR",
      "flags": "QR AA",
      "id": 34167,
      "short_answers": "142.251.40.228",
      "sections": {
        "answer": [
          {
            "rrname": "www.google.com.",
            "rrtype": "A",
            "ttl": 300,
            "rdata": [
              "142.251.40.228"
            ]
          }
        ]
      }
    }
  ]
}
```

Are all the salesforce.com/A answer sets the same?

```
$ zonequery.py salesforce.com salesforce.com A | jq -r '.responses[].short_answers'
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130
104.109.10.129,104.109.11.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130

$ zonequery.py salesforce.com salesforce.com A | jq -r '.responses[].short_answers' | sort -u | wc -l
1

YES.
```

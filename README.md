# query_all_auths
Query all DNS authoritative servers

Script to query all the authoritative servers for a zone, for a given
query name and type. The default output, in text format, provides an
abbreviated form of the data in the answer section of the DNS responses.
With the "-j" option, more complete output is provided in JSON format.
In either case, the list of RDATA per RRset is presented in sorted
order, to make it easier to compare the answers from each server with
simple scripts.

This program can also be invoked as an AWS lambda function via the
lambda_handler() function.

Author: Shumon Huque

## Pre-requisites

* Python3
* Additional modules:
  * dnspython
  * sortedcontainers


## Usage

```
$ query_all_auths.py -h
usage: query_all_auths.py [-h] [-v] [-4 | -6] [--bufsize N] [--noedns]
                          [--nsid] [--subnet SUBNET] [--dnssec] [-j]
                          [--timeout N] [--retries N] [--notcpfallback]
                          [--tcp] [--section name]
                          zone qname qtype

Version 0.2.2
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
  -j               Emit JSON output (default is text)
  --timeout N      Query timeout in secs (default: 3)
  --retries N      Number of UDP retries (default: 2)
  --notcpfallback  Do not fall back to TCP on truncation
  --tcp            Use TCP only (default: UDP with TCP fallback)
  --section name   Specify response section to display (default: all)
```

## Example output

```
$ query_all_auths.py -j google.com www.google.com A

{
  "timestamp": 1653262479.4152172,
  "query": {
    "zone": "google.com",
    "qname": "www.google.com",
    "qtype": "A"
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
      "rtt": 8.157,
      "rcode": "NOERROR",
      "response": {
        "short_answers": "142.250.65.164",
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
      "rtt": 8.351,
      "rcode": "NOERROR",
      "response": {
        "short_answers": "142.251.40.228",
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
      "rtt": 16.612,
      "rcode": "NOERROR",
      "response": {
        "short_answers": "142.250.65.164",
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
      "rtt": 15.092,
      "rcode": "NOERROR",
      "response": {
        "short_answers": "142.251.40.228",
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
      "rtt": 16.075,
      "rcode": "NOERROR",
      "response": {
        "short_answers": "142.250.65.164",
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
      "rtt": 15.405,
      "rcode": "NOERROR",
      "response": {
        "short_answers": "142.251.40.228",
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
      "rtt": 8.145,
      "rcode": "NOERROR",
      "response": {
        "short_answers": "142.250.65.164",
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
      "rtt": 9.046,
      "rcode": "NOERROR",
      "response": {
        "short_answers": "142.251.40.228",
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
$ query_all_auths.py -j salesforce.com salesforce.com A | jq -r '.responses[].response.short_answers'
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

$ query_all_auths.py -j salesforce.com salesforce.com A | jq -r '.responses[].response.short_answers' | sort -u | wc -l
1

YES.
```

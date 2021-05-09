# query_all_auths
Query all DNS authoritative servers

Script to query all the authoritative servers for a zone,
for a given query name and type. Output can be optionally
provided in JSON format. It can also be run as an AWS lambda
function.

Author: Shumon Huque

## Pre-requisites

* Python3
* Additional modules:
  * dnspython
  * sortedcontainers


## Usage

```
$ query_all_auths.py -h
usage: query_all_auths.py [-h] [-v] [-4 | -6] [--bufsize N | --noedns] [-j]
                          zone qname qtype

Version 0.1.0
Query all nameserver addresses for a given zone, qname, and qtype.

positional arguments:
  zone           DNS zone name
  qname          Query name
  qtype          Query type

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  increase output verbosity
  -4             Use IPv4 transport only
  -6             Use IPv6 transport only
  --bufsize N    Set EDNS buffer size in octets (default: 1420)
  --noedns       Don't use EDNS
  -j             Emit JSON output (default is text)
```

## Example output

```
$ query_all_auths.py -j google.com www.google.com A | jq .

{
  "timestamp": 1611190883.6877074,
  "query": {
    "zone": "google.com",
    "qname": "www.google.com",
    "qtype": "A"
  },
  "answer": [
    {
      "name": "ns1.google.com.",
      "ip": "2001:4860:4802:32::a",
      "rcode": "NOERROR",
      "answers": "172.217.10.100"
    },
    {
      "name": "ns1.google.com.",
      "ip": "216.239.32.10",
      "rcode": "NOERROR",
      "answers": "172.217.10.36"
    },
    {
      "name": "ns2.google.com.",
      "ip": "2001:4860:4802:34::a",
      "rcode": "NOERROR",
      "answers": "172.217.10.100"
    },
    {
      "name": "ns2.google.com.",
      "ip": "216.239.34.10",
      "rcode": "NOERROR",
      "answers": "172.217.10.36"
    },
    {
      "name": "ns3.google.com.",
      "ip": "2001:4860:4802:36::a",
      "rcode": "NOERROR",
      "answers": "172.217.10.100"
    },
    {
      "name": "ns3.google.com.",
      "ip": "216.239.36.10",
      "rcode": "NOERROR",
      "answers": "172.217.10.36"
    },
    {
      "name": "ns4.google.com.",
      "ip": "2001:4860:4802:38::a",
      "rcode": "NOERROR",
      "answers": "172.217.10.100"
    },
    {
      "name": "ns4.google.com.",
      "ip": "216.239.38.10",
      "rcode": "NOERROR",
      "answers": "172.217.10.36"
    }
  ]
}
```

Are all the salesforce.com/A answer sets the same?

```
$ query_all_auths.py -j salesforce.com salesforce.com A | jq '.answer[].answers'
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"

$ query_all_auths.py -j salesforce.com salesforce.com A | jq '.answer[].answers' | sort -u
"104.109.10.129,104.109.11.129,104.109.12.129,184.25.103.129,184.25.179.132,184.31.10.133,184.31.3.130,23.1.106.133,23.1.35.132,23.1.99.130"

YES.
```

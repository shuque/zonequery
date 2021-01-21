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
query_all_authservers.py version 0.0.1
Usage: query_all_authservers.py [Options] <zone> <qname> <qtype>

       Options:
       -h          Print this help string
       -4          Use IPv4 transport only
       -6          Use IPv6 transport only
       -e          Disable EDNS (and NSID)
       -j          Output JSON (default is text output)
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

#!/usr/bin/env python3
#

from zonequery import lambda_handler

event = {
    'zone': 'huque.com',
    'qname': 'www.huque.com',
    'qtype': 'CNAME',
    'edns': True,
}

result = lambda_handler(event, {})
print(result)

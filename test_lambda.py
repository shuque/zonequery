#!/usr/bin/env python3
#

from query_all_auths import lambda_handler

event = {
    'zone': 'huque.com',
    'qname': 'www.huque.com',
    'qtype': 'CNAME',
    'edns': True,
}

result = lambda_handler(event, {})
print(result)

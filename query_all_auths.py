#!/usr/bin/env python3
#

"""
Query all nameserver addresses for a given zone, qname, and qtype.

"""

import os
import sys
import getopt
import json
import time
import dns.resolver
import dns.query
import dns.rdatatype
import dns.rdataclass
import dns.rcode
from sortedcontainers import SortedList


PROGNAME = os.path.basename(sys.argv[0])
VERSION = "0.0.1"

TIMEOUT = 3
RETRIES = 2

DEFAULT_EDNS = True
DEFAULT_EDNS_BUFSIZE = 1420
DEFAULT_JSON = False
DEFAULT_IP_RRTYPES = [dns.rdatatype.AAAA, dns.rdatatype.A]


class Config:

    """Configuration parameters"""

    def __init__(self, zone, qname, qtype):
        self.zone = zone
        self.qname = qname
        self.qtype = qtype
        self.edns = DEFAULT_EDNS
        self.edns_bufsize = DEFAULT_EDNS_BUFSIZE
        self.json = DEFAULT_JSON
        self.ip_rrtypes = DEFAULT_IP_RRTYPES

    def set_edns(self, value):
        """Set EDNS preference"""
        self.edns = value

    def set_ip_rrtypes(self, value):
        """Set IP RRTYPES preference"""
        self.ip_rrtypes = value

    def set_json(self, value):
        """Set JSON output preference"""
        self.json = value


def usage(msg=None):
    """Print usage string and terminate program."""

    if msg:
        print(msg)

    print("""\
{0} version {1}
Usage: {0} [Options] <zone> <qname> <qtype>

       Options:
       -h          Print this help string
       -4          Use IPv4 transport only
       -6          Use IPv6 transport only
       -e          Disable EDNS (and NSID)
       -j          Output JSON (default is text output)
""".format(PROGNAME, VERSION)
)
    sys.exit(4)


def process_args(arg_vector):
    """Process command line options and arguments"""

    try:
        (options, args) = getopt.getopt(arg_vector, 'h46ej')
    except getopt.GetoptError as exc_info:
        usage("{}".format(exc_info))

    for (opt, _) in options:
        if opt == "-h":
            usage()

    if len(args) != 3:
        usage("Missing positional arguments. 3 required")

    zone, qname, qtype = args
    config = Config(zone, qname, qtype)

    for (opt, _) in options:
        if opt == "-4":
            config.set_ip_rrtypes([dns.rdatatype.A])
        elif opt == "-6":
            config.set_ip_rrtypes([dns.rdatatype.AAAA])
        elif opt == "-e":
            config.set_edns(False)
        elif opt == "-j":
            config.set_json(True)

    return config


class Answer:

    """DNS Answer Class"""

    def __init__(self, caller, nsname, ipaddr):
        self.caller = caller
        self.nsname = nsname
        self.ipaddr = ipaddr
        self.qname = caller.config.qname
        self.qtype = caller.config.qtype
        self.rcode = None
        self.answers = SortedList()
        self.nsid = None
        self.info = []
        self.get_answer()

    def get_answer(self):
        """Obtain answer to DNS query"""
        msg = self.send_query()

        if self.caller.config.edns:
            for option in msg.options:
                if option.otype == dns.edns.NSID:
                    self.nsid = option.data.decode()

        for rrset in msg.answer:
            for rdata in rrset:
                self.answers.add(rdata.to_text())
        self.rcode = msg.rcode()

    def get_result(self):
        """Make result dictionary"""
        answer_dict = {}
        answer_dict['name'] = self.nsname.to_text()
        answer_dict['ip'] = self.ipaddr
        if self.nsid:
            answer_dict['nsid'] = self.nsid
        answer_dict['rcode'] = dns.rcode.to_text(self.rcode)
        answer_dict['answers'] = ",".join(self.answers)
        if self.info:
            answer_dict['info'] = ";".join(self.info)
        return answer_dict

    def send_query_tcp(self, msg, timeout=TIMEOUT):
        """send DNS query over TCP to given IP address"""

        res = None
        try:
            res = dns.query.tcp(msg, self.ipaddr, timeout=timeout)
        except dns.exception.Timeout:
            info = f"WARN: TCP query timeout for {self.ipaddr}"
            if not self.caller.config.json:
                print(info)
            self.info.append(info)
        return res

    def send_query_udp(self, msg, timeout=TIMEOUT, retries=RETRIES):
        """send DNS query over UDP to given IP address"""

        gotresponse = False
        res = None
        while (not gotresponse) and (retries > 0):
            retries -= 1
            try:
                res = dns.query.udp(msg, self.ipaddr, timeout=timeout)
                gotresponse = True
            except dns.exception.Timeout:
                info = f"WARN: UDP query timeout for {self.ipaddr}"
                if not self.caller.config.json:
                    print(info)
                self.info.append(info)
        return res

    def send_query(self):
        """Send DNS query"""

        msg = self.make_query_message()
        res = self.send_query_udp(msg, timeout=TIMEOUT, retries=RETRIES)
        if res and (res.flags & dns.flags.TC):
            info = "WARN: response was truncated; retrying with TCP"
            if not self.caller.config.json:
                print(info)
            self.info.append(info)
            return self.send_query_tcp(msg, timeout=TIMEOUT)
        return res

    def make_query_message(self):
        """Construct DNS query message"""

        msg = dns.message.make_query(self.qname, self.qtype)
        msg.flags &= ~dns.flags.RD
        if self.caller.config.edns:
            msg.use_edns(edns=0,
                         payload=self.caller.config.edns_bufsize,
                         options=[dns.edns.GenericOption(dns.edns.NSID, b'')])
        return msg


class AllAnswers:

    """DNS All Answers Class"""

    def __init__(self, config):
        self.config = config
        self.answer_list = []                  # list of Answer objects
        self.result = self.init_result()
        self.nslist = self.get_nslist()
        self.get_all_answers()

    def init_result(self):
        """Initialize result dictionary"""
        result = {}
        result['timestamp'] = time.time()
        result['query'] = {
            "zone": self.config.zone,
            "qname": self.config.qname,
            "qtype": self.config.qtype
        }
        result['answer'] = []
        return result

    def get_result(self):
        """Return result dictionary"""
        for answer in self.answer_list:
            self.result['answer'].append(answer.get_result())
        return self.result

    def get_all_answers(self):
        """Get answers from all authority servers"""
        for nsname in self.nslist:
            for ipaddr in self.get_iplist(nsname):
                answer = Answer(self, nsname, ipaddr)
                self.answer_list.append(answer)

    def get_nslist(self):
        """Get NS name list for given zone"""

        nslist = SortedList()
        msg = dns.resolver.resolve(self.config.zone, dns.rdatatype.NS).response
        for rrset in msg.answer:
            if rrset.rdtype != dns.rdatatype.NS:
                continue
            for rdata in rrset:
                nslist.add(rdata.target)
        return nslist

    def get_iplist(self, nsname):
        """Get IP address list for given name"""

        iplist = []
        for rrtype in self.config.ip_rrtypes:
            msg = dns.resolver.resolve(nsname, rrtype,
                                       raise_on_no_answer=False).response
            for rrset in msg.answer:
                if rrset.rdtype != rrtype:
                    continue
                for rdata in rrset:
                    iplist.append(rdata.address)
        return iplist


def main(config):
    """main function, invoked by either command line or lambda"""

    answers = AllAnswers(config)
    return answers.get_result()


def lambda_handler(event, context):
    """AWS Lambda function to return results"""

    print("Received event: " + json.dumps(event, indent=2))

    _ = context
    zone = event['zone']
    qname = event['qname']
    qtype = event['qtype']
    config = Config(zone, qname, qtype)
    if "edns" in event:
        config.set_edns(event['edns'])
    # Lambda still doesn't support IPv6, sigh ..
    config.set_ip_rrtypes([dns.rdatatype.A])
    return main(config)


if __name__ == '__main__':

    CONFIG = process_args(sys.argv[1:])
    RESULT = main(CONFIG)
    if CONFIG.json:
        print(json.dumps(RESULT))
    else:
        for ADICT in RESULT['answer']:
            NSID = ADICT['nsid'] if 'nsid' in ADICT else ''
            print("{} {} {} {}".format(ADICT['answers'],
                                       ADICT['name'],
                                       ADICT['ip'],
                                       NSID))

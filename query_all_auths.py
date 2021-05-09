#!/usr/bin/env python3
#

"""
Query all nameserver addresses for a given zone, qname, and qtype.

"""

import argparse
import json
import time
import dns.resolver
import dns.query
import dns.rdatatype
import dns.rdataclass
import dns.rcode
from sortedcontainers import SortedList


__version__ = "0.1.1"
__description__ = f"""\
Version {__version__}
Query all nameserver addresses for a given zone, qname, and qtype."""

DEFAULT_TIMEOUT = 3
DEFAULT_RETRIES = 2
DEFAULT_EDNS_BUFSIZE = 1420
DEFAULT_IP_RRTYPES = [dns.rdatatype.AAAA, dns.rdatatype.A]


class Config:

    """
    Configuration parameters. Most of the parameters will be
    populated by argparse.parse_args(), to which an instance of
    this class is passed.
    """

    __slots__ = [
        'zone', 'qname', 'qtype',
        'verbose',
        'ip_rrtypes',
        'bufsize',
        'json',
        'timeout',
        'retries',
        'tcponly',
    ]

    def __init__(self):
        self.ip_rrtypes = DEFAULT_IP_RRTYPES


def process_arguments(arguments=None):
    """Process command line arguments"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__description__,
        allow_abbrev=False)
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="increase output verbosity")
    parser.add_argument("zone",
                        help="DNS zone name")
    parser.add_argument("qname",
                        help="Query name")
    parser.add_argument("qtype",
                        help="Query type")
    transports = parser.add_mutually_exclusive_group()
    transports.add_argument("-4", dest='ip_rrtypes',
                            action='store_const', const=[dns.rdatatype.A],
                            help="Use IPv4 transport only")
    transports.add_argument("-6", dest='ip_rrtypes',
                            action='store_const', const=[dns.rdatatype.AAAA],
                            help="Use IPv6 transport only")
    edns = parser.add_mutually_exclusive_group()
    edns.add_argument("--bufsize", type=int, metavar='N',
                      default=DEFAULT_EDNS_BUFSIZE,
                      help="Set EDNS buffer size in octets (default: %(default)d)")
    edns.add_argument("--noedns", dest='bufsize',
                      action='store_const', const=0,
                      help="Don't use EDNS")
    parser.add_argument("-j", dest='json', action='store_true',
                        help="Emit JSON output (default is text)")
    edns.add_argument("--timeout", type=int, metavar='N',
                      default=DEFAULT_TIMEOUT,
                      help="Query timeout in secs (default: %(default)d)")
    edns.add_argument("--retries", type=int, metavar='N',
                      default=DEFAULT_RETRIES,
                      help="Number of UDP retries (default: %(default)d)")
    parser.add_argument("--tcp", dest='tcponly', action='store_true',
                        help="Use TCP only (default: UDP with TCP fallback)")

    config = Config()
    if arguments is not None:
        return parser.parse_args(namespace=config, args=arguments)
    return parser.parse_args(namespace=config)


class Answer:

    """DNS Answer Class"""

    def __init__(self, caller, nsname, ipaddr):
        self.caller = caller
        self.nsname = nsname
        self.ipaddr = ipaddr
        self.qname = caller.config.qname
        self.qtype = caller.config.qtype
        self.query_start_time = None
        self.rtt = 0                          # in milliseconds
        self.rcode = None
        self.answers = SortedList()
        self.nsid = None
        self.info = []
        self.error = []
        self.get_answer()

    def get_answer(self):
        """Obtain answer to DNS query"""
        msg = self.send_query()
        if msg is None:
            self.error.append("Failed to get response")
            return

        if self.caller.config.bufsize != 0:
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
        if self.info:
            answer_dict['info'] = ";".join(self.info)
        if self.error:
            answer_dict['error'] = ";".join(self.error)
            return answer_dict
        if self.nsid:
            answer_dict['nsid'] = self.nsid
        answer_dict['rtt'] = self.rtt
        answer_dict['rcode'] = dns.rcode.to_text(self.rcode)
        answer_dict['answers'] = ",".join(self.answers)
        return answer_dict

    def set_query_start_time(self):
        """Set or reset query start time"""
        self.query_start_time = time.time()

    def compute_rtt(self):
        """Compute response time for query in milliseconds"""
        self.rtt = round(1000.0 * (time.time() - self.query_start_time), 3)

    def send_query_tcp(self, msg):
        """send DNS query over TCP to given IP address"""

        res = None
        timeout = self.caller.config.timeout
        self.set_query_start_time()
        try:
            res = dns.query.tcp(msg, self.ipaddr, timeout=timeout)
        except dns.exception.Timeout:
            info = f"WARN: TCP query timeout for {self.ipaddr}"
            if not self.caller.config.json:
                print(info)
            self.info.append(info)
        self.compute_rtt()
        return res

    def send_query_udp(self, msg):
        """send DNS query over UDP to given IP address"""

        gotresponse = False
        res = None
        timeout = self.caller.config.timeout
        retries = self.caller.config.retries
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
        if self.caller.config.tcponly:
            return self.send_query_tcp(msg)
        self.set_query_start_time()
        res = self.send_query_udp(msg)
        if res and (res.flags & dns.flags.TC):
            info = "WARN: response was truncated; retrying with TCP"
            if not self.caller.config.json:
                print(info)
            self.info.append(info)
            return self.send_query_tcp(msg)
        self.compute_rtt()
        return res

    def make_query_message(self):
        """Construct DNS query message"""

        msg = dns.message.make_query(self.qname, self.qtype)
        msg.flags &= ~dns.flags.RD
        if self.caller.config.bufsize != 0:
            msg.use_edns(edns=0,
                         payload=self.caller.config.bufsize,
                         options=[dns.edns.GenericOption(dns.edns.NSID, b'')])
        return msg


class AllAnswers:

    """DNS All Answers Class"""

    def __init__(self, config):
        self.config = config
        self.answer_list = []                  # list of Answer objects
        self.info = []
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
        result['nslist'] = []
        result['answer'] = []
        return result

    def get_result(self):
        """Return result dictionary"""
        for answer in self.answer_list:
            self.result['answer'].append(answer.get_result())
        if self.info:
            self.result['info'] = self.info
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
        try:
            msg = dns.resolver.resolve(self.config.zone, dns.rdatatype.NS).response
        except dns.exception.DNSException as excinfo:
            errmsg = f"Couldn't query NS list for {self.config.zone}: {excinfo}"
            self.info.append(errmsg)
            if not self.config.json:
                print(errmsg)
            return nslist
        for rrset in msg.answer:
            if rrset.rdtype != dns.rdatatype.NS:
                continue
            for rdata in rrset:
                nslist.add(rdata.target)
        for nsname in nslist:
            self.result['nslist'].append(nsname.to_text())
        return nslist

    def get_iplist(self, nsname):
        """Get IP address list for given name"""

        iplist = []
        for rrtype in self.config.ip_rrtypes:
            try:
                msg = dns.resolver.resolve(nsname, rrtype,
                                            raise_on_no_answer=False).response
            except dns.exception.DNSException as excinfo:
                errmsg = f"Couldn't resolve NS address for {nsname} {rrtype}: {excinfo}"
                self.info.append(errmsg)
                if not self.config.json:
                    print(errmsg)
                continue
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
    arglist = ["-4"]               # Lambda still doesn't support IPv6, sigh.
    if "edns" not in event:
        arglist.append('--noedns')
    arglist.append(event['zone'])
    arglist.append(event['qname'])
    arglist.append(event['qtype'])
    config = process_arguments(arglist)
    return main(config)


if __name__ == '__main__':

    CONFIG = process_arguments()
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

#!/usr/bin/env python3
#

"""
Query all nameserver addresses for a given zone, qname, and qtype.

"""

import argparse
import json
import time
import struct
import socket
import select
import dns.resolver
import dns.query
import dns.inet
import dns.rdatatype
import dns.rdataclass
import dns.rcode
import dns.flags
import dns.message
from sortedcontainers import SortedList


__version__ = "0.3.0"
__description__ = f"""\
Version {__version__}
Query all nameserver addresses for a given zone, qname, and qtype."""

DEFAULT_TIMEOUT = 3
DEFAULT_RETRIES = 2
DEFAULT_EDNS_BUFSIZE = 1420
DEFAULT_IP_RRTYPES = [dns.rdatatype.AAAA, dns.rdatatype.A]


class QueryError(Exception):
    """QueryError Class"""


def query_type(qtype):
    """Check qtype argument value is well formed"""
    try:
        dns.rdatatype.from_text(qtype)
    except Exception as catchall_except:
        raise ValueError(f"invalid query type: {qtype}") from catchall_except
    return qtype.upper()


def process_arguments(arguments=None):
    """Process command line arguments"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__description__,
        allow_abbrev=False)
    parser.add_argument("zone", help="DNS zone name")
    parser.add_argument("qname", help="Query name")
    parser.add_argument("qtype", help="Query type", type=query_type)

    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="increase output verbosity")

    ip_rrtypes = parser.add_mutually_exclusive_group()
    ip_rrtypes.add_argument("-4", dest='ip_rrtypes',
                            action='store_const', const=[dns.rdatatype.A],
                            default=DEFAULT_IP_RRTYPES,
                            help="Use IPv4 transport only")
    ip_rrtypes.add_argument("-6", dest='ip_rrtypes',
                            action='store_const', const=[dns.rdatatype.AAAA],
                            default=DEFAULT_IP_RRTYPES,
                            help="Use IPv6 transport only")

    edns = parser.add_mutually_exclusive_group()
    edns.add_argument("--bufsize", type=int, metavar='N',
                      default=DEFAULT_EDNS_BUFSIZE,
                      help="Set EDNS buffer size in octets (default: %(default)d)")
    edns.add_argument("--noedns", dest='bufsize',
                      action='store_const', const=0,
                      help="Don't use EDNS")

    parser.add_argument("--nsid", dest='nsid', action='store_true',
                        help="Send NSID EDNS option")
    parser.add_argument("--subnet", dest='subnet',
                        help="EDNS Client Subnet (e.g. 1.2.3.4/24)")
    parser.add_argument("--dnssec", dest='dnssec', action='store_true',
                        help="Set DNSSEC-OK bit in queries")

    parser.add_argument("--text", dest='text', action='store_true',
                        help="Emit abbreviated text output (default is json)")
    edns.add_argument("--timeout", type=int, metavar='N',
                      default=DEFAULT_TIMEOUT,
                      help="Query timeout in secs (default: %(default)d)")
    edns.add_argument("--retries", type=int, metavar='N',
                      default=DEFAULT_RETRIES,
                      help="Number of UDP retries (default: %(default)d)")
    parser.add_argument("--notcpfallback", dest='notcpfallback', action='store_true',
                        help="Do not fall back to TCP on truncation")
    parser.add_argument("--tcp", dest='tcponly', action='store_true',
                        help="Use TCP only (default: UDP with TCP fallback)")
    parser.add_argument("--section", dest='section', metavar='name',
                        help="Specify response section to display (default: all)",
                        choices=['answer', 'authority', 'additional'])

    if arguments is not None:
        return parser.parse_args(args=arguments)
    return parser.parse_args()


class Answer:

    """DNS Answer Class; represents a DNS answer from a single nameserver"""

    def __init__(self, caller, nsname, ipaddr):
        self.caller = caller
        self.nsname = nsname
        self.ipaddr = ipaddr
        self.family = dns.inet.af_for_address(ipaddr)
        self.qname = caller.config.qname
        self.qtype = caller.config.qtype
        self.query_start_time = None
        self.rtt = 0                          # in milliseconds
        self.rcode = None
        self.msg = None
        self.short_answers = SortedList()
        self.nsid = None
        self.subnet = None
        self.size = 0
        self.udp_truncated = False
        self.tcp_fallback = False             # did TCP fallback happen?
        self.info = []
        self.error = []
        self.get_answer()

    @staticmethod
    def rrset_to_dict(rrset):
        """Convert DNS rrset to dictionary"""
        rrdict = {
            'rrname': str(rrset.name),
            'rrtype': dns.rdatatype.to_text(rrset.rdtype),
            'ttl': rrset.ttl,
            'rdata': []
        }
        for rdata in sorted(rrset):
            rrdict['rdata'].append(rdata.to_text())
        return rrdict

    @staticmethod
    def section_to_list(section):
        """Convert DNS message section to list of rrset_dicts"""
        section_list = []
        for rrset in section:
            rrdict = Answer.rrset_to_dict(rrset)
            section_list.append(rrdict)
        return section_list

    def get_answer(self):
        """Obtain answer to DNS query"""
        self.msg = self.send_query()
        if self.msg is None:
            self.error.append("Failed to get response")
            return

        if self.caller.config.bufsize != 0:
            for option in self.msg.options:
                if option.otype == dns.edns.NSID:
                    self.nsid = option.data.decode()
                elif option.otype == dns.edns.ECS:
                    ecs_text = option.to_text()
                    if ecs_text.startswith('ECS '):
                        ecs_text = ecs_text[4:]
                    self.subnet = ecs_text

        for rrset in self.msg.answer:
            for rdata in rrset:
                self.short_answers.add(rdata.to_text())
        self.rcode = self.msg.rcode()

    def get_sections(self):
        """Get response section information"""
        requested = self.caller.config.section
        response_dict = {}
        if self.msg.answer and requested in [None, 'answer']:
            answer_list = Answer.section_to_list(self.msg.answer)
            response_dict['answer'] = answer_list
        if self.msg.authority and requested in [None, 'authority']:
            authority_list = Answer.section_to_list(self.msg.authority)
            response_dict['authority'] = authority_list
        if self.msg.additional and requested in [None, 'additional']:
            additional_list = Answer.section_to_list(self.msg.additional)
            response_dict['additional'] = additional_list
        return response_dict

    def get_result(self):
        """Make result dictionary"""
        answer_dict = {}
        answer_dict['name'] = self.nsname.to_text()
        answer_dict['ip'] = self.ipaddr
        if self.info:
            answer_dict['info'] = ";".join(self.info)
        if self.error:
            answer_dict['error'] = ";".join(self.error)
        if self.udp_truncated:
            answer_dict['udp_truncated'] = True
        if self.tcp_fallback:
            answer_dict['tcp_fallback'] = True
        if self.error:
            return answer_dict
        if self.size:
            answer_dict['size'] = self.size
        if self.nsid:
            answer_dict['nsid'] = self.nsid
        if self.subnet:
            answer_dict['subnet'] = self.subnet
        answer_dict['rtt'] = self.rtt
        answer_dict['rcode'] = dns.rcode.to_text(self.rcode)
        answer_dict['flags'] = dns.flags.to_text(self.msg.flags)
        answer_dict['id'] = self.msg.id
        answer_dict['short_answers'] = ",".join(self.short_answers)
        answer_dict['sections'] = self.get_sections()
        return answer_dict

    def set_query_start_time(self):
        """Set or reset query start time"""
        self.query_start_time = time.time()

    def compute_rtt(self):
        """Compute response time for query in milliseconds"""
        self.rtt = round(1000.0 * (time.time() - self.query_start_time), 3)

    def send_query_tcp(self, msg):
        """send wire format DNS query over TCP"""

        res = None
        timeout = self.caller.config.timeout

        self.set_query_start_time()
        try:
            wire = _send_tcp(msg, self.ipaddr, 53, self.family, timeout)
            self.size = len(wire)
            res = dns.message.from_wire(wire)
        except QueryError as error:
            info = f"WARN: TCP query error for {self.ipaddr}: {error}"
            if self.caller.config.text:
                print(info)
            self.info.append(info)
        self.compute_rtt()
        return res

    def send_query_udp(self, msg):
        """send wire format DNS query over UDP"""

        res = None
        timeout = self.caller.config.timeout
        attempts_left = self.caller.config.retries + 1
        ipaddress = self.ipaddr

        sock = socket.socket(self.family, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        while attempts_left > 0:
            attempts_left -= 1
            try:
                wire = _send_udp(sock, msg, ipaddress, 53)
                self.size = len(wire)
                res = dns.message.from_wire(wire)
                break
            except QueryError as error:
                info = f"WARN: UDP query error {error}"
                if self.caller.config.text:
                    print(info)
                self.info.append(info)
        return res

    def send_query(self):
        """Send DNS query"""

        msg = self.make_query_message()
        wire_msg = msg.to_wire()

        if self.caller.config.tcponly:
            return self.send_query_tcp(wire_msg)
        self.set_query_start_time()
        res = self.send_query_udp(wire_msg)
        if res and (res.flags & dns.flags.TC):
            self.udp_truncated = True
            info = "WARN: UDP response was truncated"
            if self.caller.config.text:
                print(info)
            self.info.append(info)
            if not self.caller.config.notcpfallback:
                self.tcp_fallback = True
                return self.send_query_tcp(wire_msg)
            return None
        self.compute_rtt()
        return res

    def make_query_message(self):
        """Construct DNS query message"""

        msg = dns.message.make_query(self.qname, self.qtype)
        msg.flags &= ~dns.flags.RD
        if self.caller.config.bufsize != 0:
            flags = dns.flags.DO if self.caller.config.dnssec else 0
            options_list = []
            if self.caller.config.nsid:
                options_list.append(dns.edns.GenericOption(dns.edns.NSID, b''))
            if self.caller.config.subnet:
                options_list.append(dns.edns.ECSOption.from_text(self.caller.config.subnet))
            msg.use_edns(edns=0,
                         payload=self.caller.config.bufsize,
                         ednsflags=flags,
                         options=options_list)
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
            "qtype": self.config.qtype,
        }
        if self.config.bufsize != 0:
            result['query']['edns_buf_size'] = self.config.bufsize
        result['nslist'] = {}
        result['responses'] = []
        return result

    def get_result(self):
        """Return result dictionary"""
        for answer in self.answer_list:
            self.result['responses'].append(answer.get_result())
        if self.info:
            self.result['info'] = self.info
        return self.result

    def get_all_answers(self):
        """Get answers from all authority servers"""
        for nsname in self.nslist:
            iplist = self.get_iplist(nsname)
            self.result['nslist'][nsname.to_text()] = iplist
            for ipaddr in iplist:
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
            if self.config.text:
                print(errmsg)
            return nslist
        for rrset in msg.answer:
            if rrset.rdtype != dns.rdatatype.NS:
                continue
            for rdata in rrset:
                nslist.add(rdata.target)
        for nsname in nslist:
            self.result['nslist'][nsname.to_text()] = []
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
                if self.config.text:
                    print(errmsg)
                continue
            for rrset in msg.answer:
                if rrset.rdtype != rrtype:
                    continue
                for rdata in rrset:
                    iplist.append(rdata.address)
        return iplist


def _send_udp(sock, pkt, host, port):
    """Send single request with UDP"""

    response, responder = b"", ("", 0)
    try:
        sock.sendto(pkt, (host, port))
        while True:
            response, responder = sock.recvfrom(65535)
            if responder[0:2] == (host, port):
                break
    except socket.timeout as socket_timeout:
        raise QueryError("UDP request timed out") from socket_timeout
    sock.close()
    return response


def _send_tcp(pkt, host, port, family, timeout):
    """Send the request packet via TCP, using select"""

    pkt = struct.pack("!H", len(pkt)) + pkt       # prepend 2-byte length
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    #sock.setblocking(0)
    response = b""

    try:
        sock.connect((host, port))
        if not _send_socket(sock, pkt):
            raise QueryError("send() on socket failed.")
    except socket.error as socket_error:
        sock.close()
        raise QueryError("tcp socket send error: %s" % socket_error) from socket_error

    while True:
        try:
            ready_r, _, _ = select.select([sock], [], [])
        except select.error as select_error:
            raise QueryError("fatal error from select(): %s" % select_error) from select_error
        if ready_r and (sock in ready_r):
            lbytes = _recv_socket(sock, 2)
            if len(lbytes) != 2:
                raise QueryError("recv() on socket failed.")
            resp_len, = struct.unpack('!H', lbytes)
            response = _recv_socket(sock, resp_len)
            break

    sock.close()
    return response


def _send_socket(sock, message):
    """Send message on a connected socket"""
    try:
        octets_sent = 0
        while octets_sent < len(message):
            sentn = sock.send(message[octets_sent:])
            if sentn == 0:
                raise QueryError("send() returned 0 bytes")
            octets_sent += sentn
    except Exception as catchall_error:
        raise QueryError("sendSocket error: %s" % catchall_error) from catchall_error
    else:
        return True


def _recv_socket(sock, num_octets):
    """Read and return num_octets of data from a connected socket"""
    response = b""
    octets_read = 0
    while octets_read < num_octets:
        chunk = sock.recv(num_octets-octets_read)
        chunklen = len(chunk)
        if chunklen == 0:
            return b""
        octets_read += chunklen
        response += chunk
    return response


def text_output(result):
    """Output results in abbreviated text format"""

    for adict in result['responses']:
        if 'error' in adict:
            info = adict['info'] if 'info' in adict else ''
            print("ERROR: {} {} {} {}".format(adict['error'],
                                              info,
                                              adict['name'],
                                              adict['ip']))
        else:
            nsid = adict['nsid'] if 'nsid' in adict else ''
            print("{} {} {} {}".format(adict['short_answers'],
                                       adict['name'],
                                       adict['ip'],
                                       nsid))


def main(config):
    """main function, invoked by either command line or lambda"""

    answers = AllAnswers(config)
    return answers.get_result()


def lambda_handler(event, context):
    """AWS Lambda function to return results"""

    print("Received event: " + json.dumps(event, indent=2))
    _ = context
    arglist = ["-4"]               # Lambda still doesn't support IPv6, sigh.
    if "tcp" in event:
        arglist.append('--tcp')
    if "notcpfallback" in event:
        arglist.append('--notcpfallback')
    if "noedns" in event:
        arglist.append('--noedns')
    if 'bufsize' in event:
        arglist.extend(['--bufsize', event['bufsize']])
    if "dnssec" in event:
        arglist.append('--dnssec')
    if "nsid" in event:
        arglist.append('--nsid')
    if 'subnet' in event:
        arglist.extend(['--subnet', event['subnet']])
    if 'timeout' in event:
        arglist.extend(['--timeout', event['timeout']])
    if 'retries' in event:
        arglist.extend(['--retries', event['retries']])
    arglist.append(event['zone'])
    arglist.append(event['qname'])
    arglist.append(event['qtype'])
    config = process_arguments(arglist)
    return main(config)


if __name__ == '__main__':

    CONFIG = process_arguments()
    RESULT = main(CONFIG)
    if not CONFIG.text:
        print(json.dumps(RESULT, indent=2))
    else:
        text_output(RESULT)

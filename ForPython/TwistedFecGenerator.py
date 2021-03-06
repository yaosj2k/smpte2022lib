#! /usr/bin/env python
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#       OPTIMIZED AND CROSS PLATFORM SMPTE 2022-1 FEC LIBRARY IN C, JAVA, PYTHON, +TESTBENCH
#
#   Description : SMPTE 2022-1 FEC Library
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com / david.fischer@hesge.ch
#   Copyright   : 2008-2013 smpte2022lib Team. All rights reserved.
#   Sponsoring  : Developed for a HES-SO CTI Ra&D project called GaVi
#                 Haute école du paysage, d'ingénierie et d'architecture @ Genève
#                 Telecommunications Laboratory
#**************************************************************************************************#
#
#  This file is part of smpte2022lib.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from:
#    git clone git://github.com/davidfischer-ch/smpte2022lib.git
#

import logging
import socket
from FecGenerator import FecGenerator
from RtpPacket import RtpPacket
from twisted.internet.protocol import DatagramProtocol

log = logging.getLogger('smpte2022lib')


# FIXME send to multicast address fail (?)
class TwistedFecGenerator(DatagramProtocol):
    u"""
    A SMPTE 2022-1 FEC streams generator with network skills based on :mod:`twisted`.
    This generator listen to incoming RTP media stream, compute and output corresponding FEC streams.
    It is required to use reactor in order to run the generator.

    **Example usage**

    >>> from IPSocket import IPSocket
    >>> from twisted.internet import reactor
    >>> media = IPSocket(TwistedFecGenerator.DEFAULT_MEDIA)
    >>> col = IPSocket(TwistedFecGenerator.DEFAULT_COL)
    >>> row = IPSocket(TwistedFecGenerator.DEFAULT_ROW)
    >>> generator = TwistedFecGenerator(media['ip'], 'MyTwistedFecGenerator', 5, 6, col, row)
    >>> reactor.listenMulticast(media['port'], generator, listenMultiple=True)
    <__main__.TwistedFecGenerator on 5004>
    >>> print generator._generator
    Matrix size L x D            = 5 x 6
    Total invalid media packets  = 0
    Total media packets received = 0
    Column sequence number       = 1
    Row    sequence number       = 1
    Media  sequence number       = None
    Medias buffer (seq. numbers) = []

    Then you only need to start reactor with ``reactor.run()``.
    """

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    DEFAULT_MEDIA = '239.232.0.222:5004'
    DEFAULT_COL = '127.0.0.1:5006'  # '232.232.0.222:5006'
    DEFAULT_ROW = '127.0.0.1:5008'  # '232.232.0.222:5008'

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constructor >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def __init__(self, group, name, L, D, col_socket, row_socket):
        u"""
        Construct a TwistedFecGenerator.

        :param group: IP address of incoming RTP media stream
        :type group: str
        :param name: Name of current instance (reactor's stuff)
        :type name: str
        :param L: Horizontal size of the FEC matrix (columns)
        :type L: int
        :param D: Vertical size of the FEC matrix (rows)
        :type D: int
        :param col_socket: Socket of output FEC stream (column)
        :type col_socket: IPSocket
        :param row_socket: Socket of output FEC stream (row)
        :type row_socket: IPSocket
        """
        self.group = group
        self.name = name
        self.col_socket = col_socket
        self.row_socket = row_socket
        self._generator = FecGenerator(L, D)
        self._generator.onNewCol = self.onNewCol
        self._generator.onNewRow = self.onNewRow
        self._generator.onReset = self.onReset

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Functions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def startProtocol(self):
        log.info('SMPTE 2022-1 FEC Generator by David Fischer')
        log.info('started Listening %s' % self.group)
        self.transport.joinGroup(self.group)
        self.transport.setLoopbackMode(False)
        self.transport.setTTL(1)

    def datagramReceived(self, datagram, socket):
        media = RtpPacket(bytearray(datagram), len(datagram))
        log.debug('Incoming media packet seq=%s ts=%s psize=%s socket=%s' %
                  (media.sequence, media.timestamp, media.payload_size, socket))
        self._generator.putMedia(media)

    def onNewCol(self, col, generator):
        u"""
        Called by self=FecGenerator when a new column FEC packet is generated and available for output.

        Send the encapsulated column FEC packet.

        :param col: Generated column FEC packet
        :type col: FecPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        col_rtp = RtpPacket.create(col.sequence, 0, RtpPacket.MP2T_PT, col.bytes)
        log.info('Send COL FEC packet seq=%s snbase=%s LxD=%sx%s trec=%s socket=%s' %
                 (col.sequence, col.snbase, col.L, col.D, col.timestamp_recovery, self.col_socket))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(col_rtp.bytes, (self.col_socket['ip'], self.col_socket['port']))

    def onNewRow(self, row, generator):
        u"""
        Called by self=FecGenerator when a new row FEC packet is generated and available for output.

        Send the encapsulated row FEC packet.

        :param row: Generated row FEC packet
        :type row: FecPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        row_rtp = RtpPacket.create(row.sequence, 0, RtpPacket.MP2T_PT, row.bytes)
        log.info('Send ROW FEC packet seq=%s snbase=%s LxD=%sx%s trec=%s socket=%s' %
                 (row.sequence, row.snbase, row.L, row.D, row.timestamp_recovery, self.col_socket))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(row_rtp.bytes, (self.row_socket['ip'], self.row_socket['port']))

    def onReset(self, media, generator):
        u"""
        Called by self=FecGenerator when the algorithm is resetted (an incoming media is out of sequence).

        Log a warning message.

        :param media: Out of sequence media packet
        :type row: RtpPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        log.warning('Media seq=%s is out of sequence (expected %s) : FEC algorithm resetted !' %
                    (media.sequence, generator._media_sequence))

    @staticmethod
    def main():
        u"""
        This is a working example utility using this class, this method will :

        * Parse arguments from command line
        * Register handlers to SIGTERM and SIGINT
        * Instantiate a :mod:`TwistedFecGenerator` and start it
        """
        import signal
        from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
        from IPSocket import IPSocket
        from twisted.internet import reactor

        HELP_MEDIA = 'Socket of input stream'
        HELP_COL = 'Socket of generated FEC column stream'
        HELP_ROW = 'Socket of generated FEC row stream'

        dmedia = TwistedFecGenerator.DEFAULT_MEDIA
        dcol = TwistedFecGenerator.DEFAULT_COL
        drow = TwistedFecGenerator.DEFAULT_ROW

        parser = ArgumentParser(
            formatter_class=ArgumentDefaultsHelpFormatter,
            epilog='''This utility create SMPTE 2022-1 FEC streams from a sniffed source stream.
                      SMPTE 2022-1 help streaming systems to improve QoE of real-time RTP transmissions.''')
        parser.add_argument('-m', '--media', type=IPSocket, help=HELP_MEDIA, default=dmedia)
        parser.add_argument('-c', '--col', type=IPSocket, help=HELP_COL, default=dcol)
        parser.add_argument('-r', '--row', type=IPSocket, help=HELP_ROW, default=drow)
        args = parser.parse_args()

        def handle_stop_signal(SIGNAL, stack):
            log.info('\nGenerator stopped\n')
            reactor.stop()

        signal.signal(signal.SIGTERM, handle_stop_signal)
        signal.signal(signal.SIGINT, handle_stop_signal)

        TwistedFecGenerator(args.media['ip'], 'MyGenerator', 5, 6, args.col, args.row)
        # Disabled otherwise multicast packets are received twice !
        # See ``sudo watch ip maddr show`` they will be 2 clients if uncommented :
        #reactor.listenMulticast(args.media['port'], generator, listenMultiple=True)
        reactor.run()

    # @staticmethod
    # def test():
    #     u"""
    #     The following example code generate media packets in order to create input data for
    #     :mod:`TwistedFecGenerator`. Two threads are spawn to receive and log incoming FEC packets.

    #     .. warning::

    #         FIXME TODO

    #         * start TwistedFecGenerator
    #         * generate random media payload
    #         * check fec packets payload
    #     """
    #     from IPSocket import IPSocket
    #     import threading
    #     from time import sleep

    #     media = IPSocket(TwistedFecGenerator.DEFAULT_MEDIA)
    #     col = IPSocket(TwistedFecGenerator.DEFAULT_COL)
    #     row = IPSocket(TwistedFecGenerator.DEFAULT_ROW)

    #     def receiver(name, fec_socket):
    #         log.info('[%s] Thread started' % name)
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #         sock.bind((fec_socket['ip'], fec_socket['port']))
    #         #sock.bind(('', fec_socket['port']))
    #         #mreq = struct.pack("4sl", socket.inet_aton(fec_socket['ip']), socket.INADDR_ANY)
    #         #sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    #         while True:
    #             data = bytearray(sock.recv(10240))
    #             log.info('[%s] Incoming FEC packet\\n%s\\n' % (name, FecPacket(data, len(data))))

    #     t = threading.Thread(target=receiver, args=('COL', col))
    #     t.daemon = True
    #     t.start()

    #     t = threading.Thread(target=receiver, args=('ROW', row))
    #     t.daemon = True
    #     t.start()

    #     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #     sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    #     for i in range(5*6+1):
    #         packet = RtpPacket.create(i, i*100, RtpPacket.MP2T_PT, 'salut les loulous')
    #         sock.sendto(packet.bytes, (media['ip'], media['port']))

    #     sleep(10)

if __name__ == '__main__':
    import doctest
    from Utils import setup_logging
    setup_logging(name='smpte2022lib', filename=None, console=True, level=logging.DEBUG)
    log.info('Testing TwistedFecGenerator with doctest')
    doctest.testmod(verbose=False)
    log.info('OK')
    TwistedFecGenerator.main()

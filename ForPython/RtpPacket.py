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

import struct


class RtpPacket(object):
    u"""
    This represent a real-time transport protocol (RTP) packet.

    * :rfc:`3550`
    * `Wikipedia (RTP) <http://en.wikipedia.org/wiki/Real-time_Transport_Protocol>`_
    * `Parameters (RTP) <http://www.iana.org/assignments/rtp-parameters/rtp-parameters.xml>`_

    **Packet header**

    * RFC 3550 page 13

    .. code-block:: text

        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |V=2|P|X|  CC   |M|     PT      |       sequence number         |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |                           timestamp                           |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |           synchronization source (SSRC) identifier            |
       +=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
       |            contributing source (CSRC) identifiers             |
       |                             ....                              |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    **Extension header**

    * RFC 3550 page 19

    .. code-block:: text

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      defined by profile       |           length              |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                        header extension                       |
        |                             ....                              |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constants >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    ER_VERSION = 'RTP Header : Version must be set to 2'
    ER_PADDING_LENGTH = 'RTP Header : Bad padding length'
    ER_EXTENSION_LENGTH = 'RTP Header : Bad extension length'
    ER_PAYLOAD = 'RTP packet must have a payload'

    HEADER_LENGTH = 12
    V_MASK = 0xc0
    V_SHIFT = 6
    P_MASK = 0x20
    X_MASK = 0x10
    CC_MASK = 0x0f
    M_MASK = 0x80
    PT_MASK = 0x7f
    DYNAMIC_PT = 96  # Dynamic payload type
    MP2T_PT = 33  # MPEG2 TS payload type
    MP2T_CLK = 90000  # MPEG2 TS clock rate [Hz]
    S_MASK = 0x0000ffff
    TS_MASK = 0xffffffff

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @property
    def valid(self):
        u"""
        Returns True if this packet is a valid RTP packet.
        """
        return len(self.errors) == 0

    @property
    def validMP2T(self):
        u"""
        Returns True if this packet is a valid RTP packet containing a MPEG2-TS payload.
        """
        return self.valid and self.payload_type == RtpPacket.MP2T_PT

    @property
    def errors(self):
        u"""
        Returns an array containing any errors (TODO).

        :return: array of error message(s).

        **Example usage**

        Testing invalid header:

        >>> rtp = RtpPacket(bytearray(RtpPacket.HEADER_LENGTH-1), RtpPacket.HEADER_LENGTH-1)
        >>> print(rtp.errors)
        ['RTP Header : Version must be set to 2', 'RTP packet must have a payload']

        Testing a valid RTP packet with a MPEG2-TS payload:

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, 'salut')
        >>> print(rtp.errors)
        []
        """
        errors = []
        if self._errors:
            errors.append(self._errors)
        if self.version != 2:
            errors.append(RtpPacket.ER_VERSION)
        if self.payload_size == 0:
            errors.append(RtpPacket.ER_PAYLOAD)
        return errors

    @property
    def clock_rate(self):
        u"""
        TODO
        """
        return RtpPacket.MP2T_CLK if self.payload_type == RtpPacket.MP2T_PT else 1

    @property
    def header_size(self):
        u"""
        Returns the length (aka size) of the header.

        **Example usage**

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, 'salut')
        >>> print(rtp.header_size)
        12
        """
        return RtpPacket.HEADER_LENGTH + 4*len(self.csrc)

    @property
    def payload_size(self):
        u"""
        Returns the length (aka size) of the payload.

        **Example usage**

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, 'salut')
        >>> print(rtp.payload_size)
        5
        """
        return len(self.payload) if self.payload else 0

    @property
    def time(self):
        u"""
        TODO
        """
        return self.timestamp / self.clock_rate

    @property
    def header_bytes(self):
        u"""
        TODO

        *Example usage*

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, bytearray.fromhex(u'00 01 02 03'))
        >>> print(rtp)
        version      = 2
        errors       = []
        padding      = False
        extension    = False
        marker       = False
        payload type = 33
        sequence     = 6
        timestamp    = 777
        clock rate   = 90000
        time         = 0
        ssrc         = 0
        csrc count   = 0
        payload size = 4
        >>> header = rtp.header_bytes
        >>> assert(len(header) == 12)
        >>> print(''.join(' %02x' % b for b in header))
         80 21 00 06 00 00 03 09 00 00 00 00
        >>> header += rtp.payload
        >>> rtp2 = RtpPacket(header, len(header))
        >>> assert(rtp == rtp2)

        >>> rtp = RtpPacket.create(0xffffffff, 0xffffffffff, RtpPacket.DYNAMIC_PT, bytearray(1023))
        >>> print(rtp)
        version      = 2
        errors       = []
        padding      = False
        extension    = False
        marker       = False
        payload type = 96
        sequence     = 65535
        timestamp    = 4294967295
        clock rate   = 1
        time         = 4294967295
        ssrc         = 0
        csrc count   = 0
        payload size = 1023
        >>> header = rtp.header_bytes
        >>> assert(len(header) == 12)
        >>> print(''.join(' %02x' % b for b in header))
         80 60 ff ff ff ff ff ff 00 00 00 00
        >>> header += rtp.payload
        >>> rtp2 = RtpPacket(header, len(header))
        >>> assert(rtp == rtp2)
        """
        cc = len(self.csrc)
        bytes = bytearray(RtpPacket.HEADER_LENGTH + 4*cc)
        bytes[0] = (((self.version << RtpPacket.V_SHIFT) & RtpPacket.V_MASK) +
                    (RtpPacket.P_MASK if self.padding else 0) +
                    (RtpPacket.X_MASK if self.extension else 0) +
                    (cc & RtpPacket.CC_MASK))
        bytes[1] = ((RtpPacket.M_MASK if self.marker else 0) +
                    (self.payload_type & RtpPacket.PT_MASK))
        struct.pack_into('!H', bytes, 2, self.sequence)
        struct.pack_into('!I', bytes, 4, self.timestamp)
        struct.pack_into('!I', bytes, 8, self.ssrc)
        i = 12
        for contributor in self.csrc:
            struct.pack_into('!I', bytes, i, contributor)
            i += 4
        return bytes

    @property
    def bytes(self):
        return self.header_bytes + self.payload

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constructor >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def __init__(self, bytes, length):
        u"""
        This constructor will parse input bytes array to fill packet's fields.
        In case of error (e.g. bad version number) the constructor will abort filling fields and
        un-updated fields are set to their corresponding default value.

        :param bytes: Input array of bytes to parse as a RTP packet
        :type bytes: bytearray
        :param length: Amount of bytes to read from the array of bytes
        :type length: int

        **Example usage**

        Testing invalid headers:

        >>> rtp = RtpPacket(bytearray(RtpPacket.HEADER_LENGTH-1), RtpPacket.HEADER_LENGTH-1)
        >>> assert(not rtp.valid)  # Bad length
        >>> rtp = RtpPacket(bytearray(RtpPacket.HEADER_LENGTH), RtpPacket.HEADER_LENGTH)
        >>> assert(not rtp.valid)  # Bad version
        >>> bytes = bytearray(RtpPacket.HEADER_LENGTH)
        >>> bytes[0] = 0xa0
        >>> rtp = RtpPacket(bytes, RtpPacket.HEADER_LENGTH)
        >>> assert(not rtp.valid)  # Padding enabled but not present

        Testing header fields value:

        >>> bytes = bytes.fromhex(u'80 a1 a4 25 ca fe b5 04 b0 60 5e bb 12 34')
        >>> rtp = RtpPacket(bytes, len(bytes))
        >>> assert(rtp.valid)
        >>> print(rtp)
        version      = 2
        errors       = []
        padding      = False
        extension    = False
        marker       = True
        payload type = 33
        sequence     = 42021
        timestamp    = 3405690116
        clock rate   = 90000
        time         = 37841
        ssrc         = 2959105723
        csrc count   = 0
        payload size = 2
        >>> assert(rtp.csrc == [] and rtp.payload[0] == 0x12 and rtp.payload[1] == 0x34)

        Testing header fields value (with padding, extension and ccrc):

        >>> bytes = bytes.fromhex( \
            u'b5 a1 a4 01 ca fe a4 21 b0 60 5e bb 11 11 11 11 22 22 22 22 33 \
              33 33 33 44 44 44 44 55 55 55 55 00 00 00 04 87 65 43 21 12 34 00 02')
        >>> rtp = RtpPacket(bytes, len(bytes))
        >>> assert(rtp.valid)
        >>> assert(rtp.version == 2 and rtp.padding and rtp.extension and rtp.marker)
        >>> assert(rtp.payload_type == 33 and rtp.sequence == 0xa401 and rtp.timestamp == 3405685793)
        >>> assert(rtp.clock_rate == 90000 and rtp.ssrc == 2959105723 and len(rtp.csrc) == 5)
        >>> assert(rtp.csrc[0] == 286331153 and rtp.csrc[1] == 572662306 and rtp.csrc[2] == 858993459)
        >>> assert(rtp.csrc[3] == 1145324612 and rtp.csrc[4] == 1431655765 and len(rtp.payload) == 2)
        >>> assert(rtp.payload[0] == 0x12 and rtp.payload[1] == 0x34)
        """
        # Fields default values
        self.version = 0
        self.padding = False
        self.extension = False
        self.marker = False
        self.payload_type = 0
        self.sequence = 0
        self.timestamp = 0
        self.ssrc = 0
        self.csrc = []
        self.payload = []
        self._errors = None

        offset = RtpPacket.HEADER_LENGTH
        if length < offset:
            return
        self.version = (bytes[0] & RtpPacket.V_MASK) >> 6
        if self.version != 2:
            return
        self.padding = (bytes[0] & RtpPacket.P_MASK) == RtpPacket.P_MASK
        if self.padding:  # Remove padding if present
            padding_length = bytes[-1]
            if padding_length == 0 or length < (offset + padding_length):
                self._errors = RtpPacket.ER_PADDING_LENGTH
                return
            length -= padding_length
        self.extension = (bytes[0] & RtpPacket.X_MASK) == RtpPacket.X_MASK
        cc = bytes[0] & RtpPacket.CC_MASK
        self.csrc = []  # cc > 0 ? new long[cc] : null
        self.marker = (bytes[1] & RtpPacket.M_MASK) == RtpPacket.M_MASK
        self.payload_type = bytes[1] & RtpPacket.PT_MASK
        self.sequence = bytes[2]*256 + bytes[3]
        self.timestamp = ((bytes[4]*256 + bytes[5])*256 + bytes[6])*256 + bytes[7]
        self.ssrc = ((bytes[8]*256 + bytes[9])*256 + bytes[10])*256 + bytes[11]

        for i in range(cc):
            self.csrc.append(
                ((bytes[offset]*256 + bytes[offset+1])*256 + bytes[offset+2])*256 + bytes[offset+3])
            offset += 4
            # FIXME In session.c of VLC they store per-source statistics in a rtp_source_t struct

        if self.extension:  # Extension header (ignored for now)
            extensionLength = bytes[offset+2]*256 + bytes[offset+3]
            offset += 4 + extensionLength
            if length < offset:
                self._errors = RtpPacket.ER_EXTENSION_LENGTH
                return

        # And finally ... The payload !
        self.payload = bytes[offset:length]

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Functions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#    public int compareTo(RtpPacket pPacket):
#        BEFORE = -1
#        EQUAL   = 0
#        AFTER   = 1

#        # This optimization is usually worthwhile, and can always be added
#        if (this == pPacket) return EQUAL
#        if (this.sequence < pPacket.sequence) return BEFORE
#        if (this.sequence > pPacket.sequence) return AFTER
#        return EQUAL

    @staticmethod
    def create(sequence, timestamp, payload_type, payload):
        u"""
        Create a valid RTP packet with a given payload.

        :param sequence: Packet sequence number (16 bits)
        :type sequence: int
        :param timestamp: Packet timestamp (32 bits)
        :type timestamp: int
        :param payload_type: Packet payload type (7 bits)
        :type payload_type: int
        :param payload: Packet payload, can be an array of bytes or a string
        :type payload: bytearray

        **Example usage**

        >>> p = RtpPacket.create(10, 1024, RtpPacket.MP2T_PT, 'The payload string')
        >>> q = RtpPacket.create(11, 1028, RtpPacket.MP2T_PT, bytearray.fromhex(u'00 11 22 33'))
        >>> r = RtpPacket.create(11, 1028, RtpPacket.DYNAMIC_PT, bytearray.fromhex(u'cc aa ff ee'))
        >>> assert(p.validMP2T and q.validMP2T and r.valid)
        """
        rtp = RtpPacket(None, 0)
        rtp.version = 2
        rtp.padding = False
        rtp.extension = False
        rtp.marker = False
        rtp.payload_type = payload_type & RtpPacket.PT_MASK
        rtp.sequence = sequence & RtpPacket.S_MASK
        rtp.timestamp = timestamp & RtpPacket.TS_MASK
        rtp.ssrc = 0
        rtp.csrc = []
        rtp.payload = payload
        return rtp

    def __eq__(self, other):
        u"""
        TODO

        .. warning::

            Test equality only on some fields (not all) !
        """
        if isinstance(other, self.__class__):
            return (self.sequence == other.sequence and self.timestamp == other.timestamp and
                    self.payload_type == other.payload_type and self.payload == other.payload)

    def __str__(self):
        u"""
        Returns a string containing a formated representation of the packet fields.

        **Example usage**

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, 'salut les loulous')
        >>> print(rtp)
        version      = 2
        errors       = []
        padding      = False
        extension    = False
        marker       = False
        payload type = 33
        sequence     = 6
        timestamp    = 777
        clock rate   = 90000
        time         = 0
        ssrc         = 0
        csrc count   = 0
        payload size = 17
        """
        return ("version      = %s\n"
                "errors       = %s\n"
                "padding      = %s\n"
                "extension    = %s\n"
                "marker       = %s\n"
                "payload type = %s\n"
                "sequence     = %s\n"
                "timestamp    = %s\n"
                "clock rate   = %s\n"
                "time         = %s\n"
                "ssrc         = %s\n"
                "csrc count   = %s\n"
                "payload size = %s" %
                (self.version, self.errors, self.padding, self.extension, self.marker,
                 self.payload_type, self.sequence, self.timestamp, self.clock_rate,
                 self.time, self.ssrc, len(self.csrc), self.payload_size))

if __name__ == '__main__':
    print('Testing RtpPacket with doctest')
    import doctest
    doctest.testmod(verbose=False)
    print ('OK')

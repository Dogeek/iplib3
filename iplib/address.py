from typing import List, Optional

# IPv4 constants
IPV4_MAX_SEGMENT_COUNT = 4
IPV4_MAX_SEGMENT_VALUE = 0xFF # (255)
# 0xFFFFFFFF (8)
IPV4_MAX_VALUE = 4294967295

# IPv6 constants
IPV6_MAX_SEGMENT_COUNT = 8
IPV6_MAX_SEGMENT_VALUE = 0xFFFF # (65535)
# 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF (32)
IPV6_MAX_VALUE = 340282366920938463463374607431768211455


class PureAddress:
    """
    Base class for IP addresses
    """
    __slots__ = ('_num',)

    def __init__(self):
        self._num = 0

    @property
    def num(self):
        """
        Negative numbers aren't valid,
        they are treated as zero.
        """

        return max(0, self._num)

    def num_to_ipv4(self) -> str:

        return self._num_to_ipv4(self.num)

    def num_to_ipv6(self, shorten=True, remove_zeroes=True) -> str:
        """ Todo: toggleable shortening and optionally
        remove one section of zeroes """

        return self._num_to_ipv6(self.num, shorten, remove_zeroes)

    @staticmethod
    def _num_to_ipv4(num: int) -> str:
        """
        Generates an IPv4 string from an integer
        """

        segments = []
        for _ in range(IPV4_MAX_SEGMENT_COUNT):
            num, segment = divmod(num, IPV4_MAX_SEGMENT_VALUE+1)
            segments.append(segment)
        return '.'.join(map(str, segments[::-1]))

    @staticmethod
    def _num_to_ipv6(num: int, shorten: bool, remove_zeroes: bool) -> str:
        """
        Generates an IPv6 string from an integer,
        with optional zero removal and shortening.
        """

        segments = []
        for _ in range(IPV6_MAX_SEGMENT_COUNT):
            num, segment = divmod(num, IPV6_MAX_SEGMENT_VALUE+1)
            segments.append(hex(segment).split('x')[1].upper())

        if remove_zeroes and '0' in segments:

            # Goes over the segments to find the
            # longest strip with nothing but zeroes
            # and replaces it with an empty string
            # the final str.join will turn to ::.

            longest = 0
            longest_idx = 0
            current = 0
            current_idx = 0
            
            for idx, seg in enumerate(segments):

                if seg == '0':

                    if not current:
                        current_idx = idx
                    current += 1

                else:

                    if current > longest:
                        longest = current
                        longest_idx = current_idx
                        current = 0

            segments = segments[:longest_idx] + [''] + segments[longest_idx+longest:]

        if not shorten:

            # Fills up any segments to full length by
            # adding missing zeroes to the front, if any.

            segments = [seg.zfill(4) if seg else '' for seg in segments]

        return ':'.join(segments[::-1])


class IPAddress(PureAddress):
    __slots__ = ('_num', '_port', '_ipv4', '_ipv6')

    def __new__(cls, address: Optional[int]=None, **kwargs):
        if isinstance(address, str):
            cls = IPv4 if '.' in address else IPv6

        self = object.__new__(cls)

        self.__init__(address, **kwargs)
        return self

    def __init__(self, address_num=0, port=None):
        self._num = address_num if address_num is not None else 0
        self._port = port
        self._ipv4 = None
        self._ipv6 = None

    def __repr__(self) -> str:
        return f"ipaddress.{self.__class__.__name__}({self.__str__()})"

    def __str__(self) -> str:
        
        if self.num <= IPV4_MAX_VALUE:
            if self._ipv4 is None:
                self._ipv4 = self.as_ipv4
            return str(self._ipv4)

        elif IPV4_MAX_VALUE < self.num <= IPV6_MAX_VALUE:
            if self._ipv6 is None:
                self._ipv6 = self.as_ipv6
            return str(self._ipv6)
        
        else:
            raise ValueError(f"No valid address representation exists for {self.num}")

    @property
    def as_ipv4(self):
        return IPv4(self.num_to_ipv4())

    @property
    def as_ipv6(self):
        return IPv6(self.num_to_ipv6())


class IPv4(IPAddress):
    __slots__ = ('_num', '_address', '_port')
    
    def __init__(self, address: str, port=None):
        self._address = address
        self._num = self.ipv4_to_num()
        self._port = port

    def __str__(self):
        if self._port is not None:
            return f"{self._address}:{self._port}"
        else:
            return self._address

    def ipv4_to_num(self) -> int:
        """
        Takes a valid IPv4 address and turns
        it into an equivalent integer value.

        Raises ValueError on invalid IPv4 format.
        """

        segments = list(map(int, self._address.split('.')))[::-1]
        total = 0

        for idx, num in enumerate(segments):
            total += num * 2**(idx * 8)
    
        return total


class IPv6(IPAddress):
    __slots__ = ('_num', '_address', '_port')

    def __init__(self, address: str, port=None):
        self._address = address
        self._num = self.ipv6_to_num()
        self._port = port

    def __str__(self):
        if self._port is not None:
            return f"[{self._address}]:{self._port}"
        else:
            return self._address

    def ipv6_to_num(self) -> int:
        """
        Takes a valid IPv6 address and turns
        it into an equivalent integer value.

        Raises ValueError on invalid IPv6 format.
        """

        halves = self._address.split('::')
        segments = []

        if len(halves) == 2: # Address with zero-skip part
            total_length = sum(map(len, halves))
            
            if halves[0]:
                segments.extend(halves[0].split(':'))
            
            segments.extend(['0000' for _ in range(IPV6_MAX_SEGMENT_COUNT - total_length)])
            
            if halves[1]:
                segments.extend(halves[1].split(':'))

        elif len(halves) == 1: # Full address
            segments.extend(halves[0].split(':'))

        else:
            raise ValueError("Invalid IPv6 address format; only one zero-skip allowed")

        processed_segments: List[int] = list(map(lambda num: int(num, 16), segments[::-1]))
        total = 0

        if (segment_count := len(processed_segments) > IPV6_MAX_SEGMENT_COUNT):
            raise ValueError(f"Invalid IPv6 address format; too many segments ({segment_count} > {IPV6_MAX_SEGMENT_COUNT})")

        if (value := max(processed_segments) > IPV6_MAX_SEGMENT_VALUE):
            raise ValueError(f"Invalid IPv6 address format; segment max value passed ({value} > {IPV6_MAX_SEGMENT_VALUE})")

        for idx, num in enumerate(segments):
            total += num * 2**(idx * 16)

        return total

# Validator regex: r"""
# (([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|
# ([0-9a-fA-F]{1,4}:){1,7}:|
# ([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|
# ([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|
# ([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|
# ([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|
# ([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|
# [0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|
# :((:[0-9a-fA-F]{1,4}){1,7}|:)|
# fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|
# ::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|
# 1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|
# (2[0-4]|1{0,1}[0-9]){0,1}[0-9])|
# ([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|
# 1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|
# (2[0-4]|1{0,1}[0-9]){0,1}[0-9]))
# """ @ https://stackoverflow.com/a/17871737

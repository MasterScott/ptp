from __future__ import print_function

import os
import re

from lxml import etree
from lxml.etree import LxmlError

from libptp import constants
from libptp.info import Info
from libptp.report import AbstractReport


class W3AFReport(AbstractReport):
    """Retrieve the information of a w3af report."""

    __tool__ = 'w3af'
    __version__ = ['1.6.0.2']

    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'
    INFO = 'Information'

    # Convert the W3AF's ranking scale to an unified one.
    RANKING_SCALE = {
        HIGH: constants.HIGH,
        MEDIUM: constants.MEDIUM,
        LOW: constants.LOW,
        INFO: constants.INFO}

    def __init__(self, *args, **kwargs):
        AbstractReport.__init__(self, *args, **kwargs)
        self.re_version = re.compile(r'Version: (\S*)\s')
        self.vulns = []

    @classmethod
    def is_mine(cls, pathname, filename=None):
        """Check if it is a W3af report and if I can handle it.

        Return True if it is mine, False otherwise.

        """
        fullpath = cls._get_fullpath(pathname, filename=filename)
        if not fullpath:
            return False
        if not fullpath.endswith('.xml'):
            return False
        try:
            root = etree.parse(fullpath).getroot()
        except LxmlError:  # Not a valid XML file.
            return False
        return cls._is_w3af(root)

    @classmethod
    def _is_w3af(cls, xml_report):
        """Check if the xml_report comes from W3AF.

        Returns True if it is from W3AF, False otherwise.

        """
        raw_metadata = xml_report.find('.//w3af-version')
        if raw_metadata is None:
            return False
        return True

    def parse(self, pathname=None, filename=None):
        """Parse a w3af resport."""
        # Reconstruct the path to the report if any.
        self.directory = ''
        if not pathname is None:
            self.directory = pathname
        if not filename is None:
            self.directory = os.path.join(self.directory, filename)

        # Parse the XML report thanks to lxml.
        self.root = etree.parse(self.directory).getroot()
        # Parse specific stuff.
        self.parse_xml_metadata()
        self.parse_xml_report()
        # TODO: Return something like an unified version of the report.
        return self.vulns

    def parse_xml_metadata(self):
        """Retrieve the metadata of the report.

        #TODO: Complete the docstring.

        """
        raw_metadata = self.root.find('.//w3af-version').text
        # Find the version of w3af.
        version = self.re_version.findall(raw_metadata)
        if len(version) >= 1:  # In case we found several version numbers.
            version = version[0]
        # Reconstruct the metadata
        # TODO: Retrieve the other metadata likes the date, etc.
        metadata = {
            'version': version,}
        if self.check_version(metadata):
            self.metadata = metadata
        else:
            # TODO: Implement custom exception
            raise ValueError(
                'PTP does NOT support this version of W3AF.')

    def parse_xml_report(self):
        """Retrieve the results from the report.

        Retrieve the following attributes:
            + severity

        #TODO: Complete the docstring.

        """
        for vuln in self.root.findall('.//vulnerability'):
            info = Info(
                # Convert the severity of the issue thanks to an unified
                # ranking scale.
                ranking=self.RANKING_SCALE[vuln.get('severity')]
                )
            self.vulns.append(info)
# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""
Download utilities using urllib2.

Main API usage:
    >>> from downloadutils import download_file
    >>> new_file = download_file("http://duckduckgo.com", content_type="html")

Raises InvenioDownloadError exception.
"""

import urllib2
import time
import os

from tempfile import mkstemp

class InvenioDownloadError(Exception):
    """A generic download exception."""
    pass


def download_into_tempfile(url):
    """
    Creates a temporary file in /tmp before calling the
    download function.

    @param url: where the file lives on the interwebs
    @type url: string

    @return: request and path to the new file.
    """
    tmpfd, tmpfile = mkstemp(prefix="downloadutils_")
    os.close(tmpfd)
    try:
        req = download(url, tmpfile)
    except:
        os.remove(tmpfile)
        raise
    return req, tmpfile


def download(url, new_file):
    """
    Actually does the lower level call and downloads a file from
    given URL and desired output filename, if given. If not,
    a temporary file will be created.

    @param url: where the file lives on the interwebs
    @type url: string

    @param new_file: where the file should live after download.
    @type new_file: string

    @return: connection object on success, False on failure
    @raise InvenioDownloadError: raised upon URL/HTTP errors or IOError
    """
    try:
        conn = urllib2.urlopen(url)
        response = conn.read()
        conn.close()
    except (urllib2.URLError, urllib2.HTTPError), e:
        raise InvenioDownloadError('Error downloading from %s: \n%s\n' % (url, str(e)))

    try:
        new_file_fd = open(new_file, 'w')
        new_file_fd.write(response)
        new_file_fd.close()
    except IOError, e:
        raise InvenioDownloadError('Error saving to file %s: \n%s\n' % (new_file, str(e)))

    return conn

def download_file(url_for_file, downloaded_file=None, content_type=None, \
                  retry_count=3, timeout=2.0):
    """
    Will download a file from given URL to the desired path. Will retry
    a number of times based on retry_count (default 3) parameter and sleeps
    a number of seconds based on given timeout (default 2.0 seconds) between
    each request. Returns the path to the downloaded file if successful.
    Otherwise an exception is raised.

    Given a content-type string, the function will make sure that the desired
    type is given in the HTTP request headers. For example: application/pdf.

    @param url_for_file: where the file lives on the interwebs
    @type url_for_file: string

    @param downloaded_file: where the file should live after download.
    @type downloaded_file: string
                                      Optional.
    @param content_type: desired content type to check for, if given.
    @type content_type: string

    @param retry_count: number of times to retry. Optional. Defaults to 3
    @type retry_count: int

    @param timeout: number of seconds to sleep between attempts.
                             Optional. Defaults to 2.0
    @type timeout: float

    @return: the path of the downloaded file
    @raise InvenioDownloadError: raised upon URL/HTTP errors or wrong content-type
    """
    attempts = 0
    while attempts < retry_count:
        try:
            if not downloaded_file:
                request, downloaded_file = download_into_tempfile(url_for_file)
            else:
                request = download(url_for_file, downloaded_file)
        except InvenioDownloadError:
            attempts += 1
            time.sleep(timeout)
            continue
        else:
            if content_type and content_type not in request.headers['content-type']:
                raise InvenioDownloadError('The downloaded file is not of the desired content type')
            # successfully downloaded, return filepath
            return downloaded_file
    raise InvenioDownloadError('Download of file failed')

"""$Id$"""

__author__ = "Sam Ruby <http://intertwingly.net/> and Mark Pilgrim <http://diveintomark.org/>"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Sam Ruby and Mark Pilgrim"
__license__ = "Python"

import timeoutsocket
timeoutsocket.setDefaultSocketTimeout(10)
import urllib2
import logging
from logging import *
from xml.sax import SAXParseException
from xml.sax.xmlreader import InputSource
import re
import xmlEncoding

MAXDATALENGTH = 200000

def _validate(aString, firstOccurrenceOnly=0, loggedEvents=[]):
  """validate RSS from string, returns validator object"""
  from xml.sax import make_parser, handler
  from base import SAXDispatcher
  from exceptions import UnicodeError
  from cStringIO import StringIO
  
  source = InputSource()
  source.setByteStream(StringIO(aString))

  validator = SAXDispatcher()
  validator.setFirstOccurrenceOnly(firstOccurrenceOnly)

  validator.loggedEvents += loggedEvents

  xmlver = re.match("^<\?\s*xml\s+version\s*=\s*['\"]([-a-zA-Z0-9_.:]*)['\"]",aString)
  if xmlver and xmlver.group(1)<>'1.0':
    validator.log(logging.BadXmlVersion({"version":xmlver.group(1)}))

  parser = make_parser()
  parser.setFeature(handler.feature_namespaces, 1)
  parser.setContentHandler(validator)
  parser.setErrorHandler(validator)
  parser.setEntityResolver(validator)
  if hasattr(parser, '_ns_stack'):
    # work around bug in built-in SAX parser (doesn't recognize xml: namespace)
    # PyXML doesn't have this problem, and it doesn't have _ns_stack either
    parser._ns_stack.append({'http://www.w3.org/XML/1998/namespace':'xml'})

  try:
    parser.parse(source)
  except SAXParseException:
    pass
  except UnicodeError:
    import sys
    exctype, value = sys.exc_info()[:2]
    validator.log(logging.UnicodeError({"exception":value}))

  return validator

def validateStream(aFile, firstOccurrenceOnly=0):
  return {"feedType":validator.feedType, "loggedEvents":validator.loggedEvents}

def validateString(aString, firstOccurrenceOnly=0):
  loggedEvents = []
  try:
    xmlEncoding.detect(aString, loggedEvents)
  except:
    pass
  validator = _validate(aString, firstOccurrenceOnly, loggedEvents)
  return {"feedType":validator.feedType, "loggedEvents":validator.loggedEvents}

def validateURL(url, firstOccurrenceOnly=1, wantRawData=0):
  """validate RSS from URL, returns events list, or (events, rawdata) tuple"""
  loggedEvents = []
  request = urllib2.Request(url)
  request.add_header("Accept-encoding", "gzip")
  request.add_header("User-Agent", "FeedValidator/1.3")
  try:
    usock = urllib2.urlopen(request)
    rawdata = usock.read(MAXDATALENGTH)
  except urllib2.HTTPError, status:
    raise ValidationFailure(logging.HttpError({'status': status}))
  except urllib2.URLError, x:
    raise ValidationFailure(logging.HttpError({'status': x.reason}))

  if usock.headers.get('content-encoding', None) == 'gzip':
    import gzip, StringIO
    try:
      rawdata = gzip.GzipFile(fileobj=StringIO.StringIO(rawdata)).read()
    except:
      import sys
      exctype, value = sys.exc_info()[:2]
      event=logging.IOError({"message": 'Server response declares Content-Encoding: gzip', "exception":value})
      raise ValidationFailure(event)

  encoding = None
  try:
    encoding = xmlEncoding.detect(rawdata, loggedEvents)
  except:
    pass

  # Does that agree with the Content-Type?
  contentType = usock.headers.get('content-type', None)
  if contentType:
    from cgi import parse_header
    h = parse_header(contentType)
    ct = h[0]
    if not(ct.lower() in ['text/xml', 'application/xml', 'application/rss+xml', 'application/rdf+xml', 'application/x.atom+xml', 'application/atom+xml']):
      loggedEvents.append(UnexpectedContentType({"contentType": contentType}))
    if 'charset' in h[1]:
      charset = h[1]['charset']
      if not(charset) and h[0].lower().startswith('text/'):
        charset = 'US-ASCII'
      if charset and encoding and charset.lower() != encoding.lower():
        # RFC 3023 requires us to use 'charset', but a number of aggregators
        # ignore this recommendation, so we should warn.
        loggedEvents.append(EncodingMismatch({"charset": charset, "encoding": encoding}))

        try:
          # attempt to follow RFC 3023
          declmatch = re.compile(u'^<\?xml[^>]*?>'.encode(charset))
          newdecl = ("<?xml version='1.0' encoding='%s'?>" % charset).encode(charset)
          if declmatch.search(rawdata):
            rawdata = declmatch.sub(newdecl, rawdata)
          else:
            rawdata = newdecl + u' ' + rawdata
	  encoding=charset
        except:
          pass

  if encoding and not xmlEncoding.isCommon(encoding):
    try:
      import codecs
      rawdata = xmlEncoding.asUTF8(codecs.getdecoder(encoding)(rawdata)[0])
      encoding='utf-8'
    except:
      pass

  rawdata = rawdata.replace('\r\n', '\n').replace('\r', '\n') # normalize EOL
  usock.close()
  validator = _validate(rawdata, firstOccurrenceOnly, loggedEvents)
  params = {"feedType":validator.feedType, "loggedEvents":validator.loggedEvents}
  if wantRawData:
    params['rawdata'] = rawdata
  return params

__all__ = ['base',
           'channel',
           'compatibility',
           'image',
           'item',
           'logging',
           'rdf',
           'root',
           'rss',
           'skipHours',
           'textInput',
           'util',
           'validators',
           'validateURL',
           'validateString']

__history__ = """
$Log$
Revision 1.14  2004/04/29 20:47:09  rubys
Try harder to handle obscure encodings

Revision 1.13  2004/04/24 01:50:32  rubys
Attempt to respect RFC 3023.

Revision 1.12  2004/04/10 16:34:37  rubys
Allow application/rdf+xml

Revision 1.11  2004/03/30 09:03:30  josephw
Check Content-Type against valid feed types, and against the actual XML
character encoding.

Revision 1.10  2004/03/30 08:26:28  josephw
Check XML character encoding before parsing.

Revision 1.9  2004/03/28 11:37:41  josephw
Replaced 'from logging import *', so validtest.py works again.

Revision 1.8  2004/03/28 10:58:07  josephw
Catch and show ValidationFailure in check.cgi. Changed text_html.py
to allow global events, with no specific document location. Moved DOCSURL
into config.py. Moved trivial HTML list-delimiter definitions into
text_html.py.

Revision 1.7  2004/03/28 09:49:58  josephw
Accept URLs relative to the current directory in demo.py. Added a top-level
exception to indicate validation failure; catch and print it in demo.py.

Revision 1.6  2004/03/23 02:03:00  rubys
Dummy up line, column and other info needed for cgi

Revision 1.5  2004/03/23 01:33:04  rubys
Apply patch from Joseph Walton to provide better error reporting when
servers are misconfigured for gzip encoding.

Revision 1.4  2004/02/07 14:23:19  rubys
Fix for bug 892178: must reject xml 1.1

Revision 1.3  2004/02/07 02:15:43  rubys
Implement feature 890049: gzip compression support
Fix for bug 890054: sends incorrect user-agent

Revision 1.2  2004/02/06 15:06:10  rubys
Handle 404 Not Found errors
Applied path 891556 provided by aegrumet

Revision 1.1.1.1  2004/02/03 17:33:14  rubys
Initial import.

Revision 1.24  2003/12/11 16:32:08  f8dy
fixed id tags in header

Revision 1.23  2003/08/09 17:09:34  rubys
Remove misleading mapping of LookupError to UnicodeError

Revision 1.22  2003/08/06 05:40:00  f8dy
patch to send a real User-Agent on HTTP requests

Revision 1.21  2003/08/05 18:51:38  f8dy
added hack to work around bug in built-in SAX parser (doesn't recognize xml: namespace)

Revision 1.20  2003/07/09 16:24:30  f8dy
added global feed type support

Revision 1.19  2002/12/22 19:01:17  rubys
Integrate in SOAP support

Revision 1.18  2002/11/04 01:06:43  rubys
Remove remaining call to preValidate

Revision 1.17  2002/11/04 00:28:55  rubys
Handle LookupError (e.g., unknown encoding)

Revision 1.16  2002/10/31 00:52:21  rubys
Convert from regular expressions to EntityResolver for detecting
system entity references

Revision 1.15  2002/10/30 23:03:01  f8dy
security fix: external (SYSTEM) entities

Revision 1.14  2002/10/22 19:41:07  f8dy
normalize line endings before parsing (SAX parser is not Mac-CR-friendly)

Revision 1.13  2002/10/22 16:35:11  f8dy
commented out fallback except (caller handles it gracefully anyway)

Revision 1.12  2002/10/22 16:24:04  f8dy
added UnicodeError support for feeds that declare utf-8 but use 8-bit characters anyway

Revision 1.11  2002/10/18 13:06:57  f8dy
added licensing information

"""

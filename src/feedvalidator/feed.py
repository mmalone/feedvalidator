"""$Id$"""

__author__ = "Sam Ruby <http://intertwingly.net/> and Mark Pilgrim <http://diveintomark.org/>"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Sam Ruby and Mark Pilgrim"
__license__ = "Python"

from base import validatorBase
from validators import *
from logging import *

#
# Atom root element
#
class feed(validatorBase):
  def getExpectedAttrNames(self):
      return [(None, u'version')]

  def prevalidate(self):
    self.setFeedType(TYPE_ATOM)
    self.links = []
    
  def validate(self):
    try:
      version = self.attrs.getValue((None,'version'))
      if not version:
        self.log(MissingAttribute({"element":self.name, "attr":"version"}))
      elif version in ['0.1', '0.2', '0.2.1']:
        self.log(ObsoleteVersion({"element":self.name, "version":version}))
    except:
      self.log(MissingAttribute({"element":self.name, "attr":"version"}))
    if not 'title' in self.children:
      self.log(MissingElement({"parent":self.name, "element":"title"}))

    # must have an alternate
    if [link for link in self.links if link.rel == u'alternate']:
      self.log(ValidAtomLinkRel({"parent":self.name, "element":"link", "attr":"rel", "attrvalue":"alternate"}))
    else:
      self.log(MissingAlternateLink({"parent":self.name, "element":"link", "attr":"rel", "attrvalue":"alternate"}))

    # link/type pair must be unique
    types={}
    for link in self.links:
      if not link.type in types: types[link.type]=[]
      if link.rel in types[link.type]:
        self.log(DuplicateAtomLink({"parent":self.name, "element":"link"}))
      else:
        types[link.type] += [link.rel]

  def do_entry(self):
    from entry import entry
    return entry()

  def do_title(self):
    from content import content
    return content(), noduplicates()

  def do_tagline(self):
    from content import content
    return content(), noduplicates()

  def do_info(self):
    from content import content
    return content(), noduplicates()
  
  def do_id(self):
    return nonblank(), rfc2396_full(), noduplicates()

  def do_link(self):
    from link import link
    self.links += [link()]
    return self.links[-1]
  
  def do_modified(self):
    return iso8601_z(), noduplicates()

  def do_author(self):
    from author import author
    return author(), noduplicates()

  def do_contributor(self):
    from author import author
    return author(), noduplicates()

  def do_copyright(self):
    from content import content
    return content(), noduplicates()

  def do_generator(self):
    from generator import generator
    return generator(), noduplicates()

__history__ = """
$Log$
Revision 1.4  2004/02/17 23:17:45  rubys
Commit fixes for bugs 889545 and 893741: requiring non-relative URLs in
places where a relative URL is OK (example: rdf).

Revision 1.3  2004/02/17 22:42:02  rubys
Remove dependence on Python 2.3

Revision 1.2  2004/02/16 16:25:25  rubys
Fix for bug 890053: detecting unknown attributes, based largely
on patch 895910 by Joseph Walton.

Revision 1.1.1.1  2004/02/03 17:33:15  rubys
Initial import.

Revision 1.15  2003/12/12 14:35:08  f8dy
fixed link rel=alternate logic to pass new "link not missing" tests

Revision 1.14  2003/12/12 11:30:39  rubys
Validate feed links

Revision 1.13  2003/12/12 05:42:05  rubys
Rough in some support for the new link syntax

Revision 1.12  2003/12/11 23:16:32  f8dy
passed new generator test cases

Revision 1.11  2003/12/11 20:13:58  f8dy
feed title, copyright, and tagline may be blank

Revision 1.10  2003/12/11 18:20:46  f8dy
passed all content-related testcases

Revision 1.9  2003/12/11 16:32:08  f8dy
fixed id tags in header

Revision 1.8  2003/12/11 04:50:53  f8dy
added test cases for invalid letters in urn NSS, fixed RE to match

Revision 1.7  2003/08/05 15:03:19  rubys
Handle complex (nested) content.  Remove copy/paste error in handing
of copyright.

Revision 1.6  2003/08/05 14:03:23  rubys
Tagline is optional

Revision 1.5  2003/08/05 07:59:04  rubys
Add feed(id,tagline,contributor)
Drop feed(subtitle), entry(subtitle)
Check for obsolete version, namespace
Check for incorrect namespace on feed element

Revision 1.4  2003/08/03 18:46:04  rubys
support author(url,email) and feed(author,copyright,generator)

Revision 1.3  2003/07/09 16:24:30  f8dy
added global feed type support

Revision 1.2  2003/07/07 10:35:50  rubys
Complete first pass of echo/pie tests

Revision 1.1  2003/07/07 00:54:00  rubys
Rough in some pie/echo support

"""

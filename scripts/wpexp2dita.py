#
# PROLOG SECTION
# wpexp2dita.py
#
# A script that reads a WordPress XML export file and
# creates DITA XML source files from it that can be used to
# make a site archive.
#
# A DITA concept is created for each page or post on the
# WordPress site. In addition two ditamap files are
# created that are suitable for processing the DITA concept
# files to either epub, xhtml or pdf format.
#
# The purpose of creating this set of files is to produce
# a readable archive of the content on the WordPress site
# that can be viewed when the site is not available or has
# been shut down.
#
# Files "tags.txt" and "categories.txt" are written that
# list all the tags and categories referenced by post and
# pages on the site.
#
# Debugging and error information may be written to
# the log file.
#
# Note: by setting the values in the input file, it
# is possible to restrict the archive to content created on
# the site in a particular set of years or with particular
# categories or tags.
#
# Tested with Python 3.7.2
# January 10, 2019
#
# Author: Dick Johnson
#
###################################

###################################
# ENVIRONMENT SETUP SECTION
###################################

# import needed modules
import os
import os.path
from xml.etree.ElementTree import *
import shutil
from PIL import Image
import urllib.request
import urllib.error
import urllib.parse
from bs4 import BeautifulSoup
import codecs
import datetime
import sys
from distutils.dir_util import copy_tree

# set and define global variables for this script
gallery_count = 0

# file object for the web site error log file
log_file = "wpexp2ditaError.log"
log_fileobj = None
logfp = None
log_file_lines = 0

# namespace definitions for namespaces found in the
# WordPress export file
wpns = "{http://wordpress.org/export/1.2/}"
dcns = "{http://purl.org/dc/elements/1.1/}"
contentns = "{http://purl.org/rss/1.0/modules/content/}"

# Set defaults for all the parameters.
# Things that can be in a parameter file.
parm_file = "wpexp2dita.xml"
splash_page_image = 'templates/processing_files/NanAnna.JPG'
splash_page = "common/processing_files/splash_pages/splashpage_newsfromnanarchive.dita"
include_pages = None
website = None
input_file = None
archive_title = None
# Set the default list of post/page creation years to include.
# If the list is empty, include everything.
year_list = []
# same for categories
category_list = []
ucategory_list = []
# same for tags
tags_list = []
utags_list = []

# constants
dbgflag = False
develflag = False
template = "templates/template.dita"
template_map_web = "templates/export_template_web.ditamap"
template_map_pdf = "templates/export_template_pdf.ditamap"
template_dir_map = "templates/template_dir.ditamap"
missing_image_base = "missing_image.jpg"
missing_image = "common/processing_files/images/"+missing_image_base



# other definitions
WPIMAGE = 'wp-image-'
SCAPTION = 'caption'
SIFRAME = 'youtube_video'
SGALLERY = 'gallery'
SGALLERTB = 'gallery_bank'
REMOVE = "*Remove this element"
MISSING = "*MISSING*"
missing_keys = []

# define the files to save information about tags and categories
cat_file = "categories.txt"
tag_file = "tags.txt"

###################################
# FUNCTION DEFINITION SECTION
###################################   

#
# Function to write a text line to the
# web site error log
#
def wpexp2ditaLog(*s):
    global log_file, log_fileobj, log_file_lines
    
    if debugMode():
        print("wpexp2ditaLog:",s)

    if log_fileobj == None:
        log_fileobj = open(log_file,"w")
        
    sline = ""
    for ss in s:
        sline=sline+ss+" "
    print(sline,file=log_fileobj)
    log_file_lines = log_file_lines+1
    if debugMode():
      print("***wpexp2ditaLog:",sline)

    return

#
# Function to close the web site error log
#
def wpexp2ditaLogClose():
    global log_fileobj
    if not log_fileobj == None:
        log_fileobj.close()
        log_fileobj = None
        if debugMode():
           print(log_file,"is closed")

#
# Function to parse an XML parameter file
#
def parseParms(xfile):
    if debugMode():
        print("parseParms:",xfile)

    pdict = {}

    try:
        statxml = os.stat(xfile)
        
    except:
        print("Error, file",xfile,"not found")
        return None
    
    try:
        t = parse(xfile)       
    except:
        print("Error,could not parse",xfile)
        return None

    root = t.getroot()
    kids = list(root)
    for k in kids:
        pdict[k.tag] = k.text

    return pdict

#
# Function to return a time stamp string
#
def tStamp():
    return datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

#
# Function to run the script in developer mode. This
# buts extra information in the output files to make
# it easier to fix problems in the input.
#
def setdevel(flag):
    global develflag
    develflag = flag
    if develflag:
        print("we are in developer mode!")
    return

#
# Are we in developer mode?
#
def develMode():
    return develflag

#
# Function to set the debug flag.
# Setting the flag to True will produce lots
# of output that traces the execution
# of the script.
#
def setdebug(flag):
    """
    Set the debug flag:
    
    True = print details of execution
    False = print minimal progress messages
    
    """
    global dbgflag
    dbgflag = flag
    if dbgflag:
        print ("**setdebug - debug flag set to",dbgflag) 
    return

#
# Function to resize the image files to maximum sizes.
#
def resizeImages(imagedir):
    if debugMode():
        print("resizeImages",imagedir)

    # maximum image width in pixels we allow
    maxwidth = 450

    if debugMode():
        print("maximum image width",maxwidth)

    cnt = 0
    tot = 0

    # get the file names of all the images
    fnames = os.walk(imagedir)

    # loop through all the images
    for f in fnames:
        dirp = f[0]
        dirn = f[1]
        fns  = f[2]
        
        fmts = {}
        widths = {}
        heights = {}
        for img in fns:
            tot=tot+1
            infile = dirp+"/"+img
            try:
                im = Image.open(infile)
                width  = im.size[0]
                height = im.size[1]
        
                # change widths, if required
                if width>maxwidth:
                    cnt = cnt+1
                    newheight = int((float(maxwidth)/float(width))*float(height))
                    newwidth = maxwidth
                    if debugMode():
                        print("resize",width,height,"to",newwidth,newheight,img)
                    out = im.resize((newwidth,newheight))
                    out.save(infile)
            except:
                wpexp2ditaLog("skipping non-image",infile)

        
    return cnt    
    
#
# Function to return the dbgflag value (controls debugging output)
# True means to print debugging output.
#
def debugMode():
    return dbgflag

#
# Function to empty a directory
#
def EmptyDir(d):
    if debugMode():
        print("EmptyDir",d)

    if d==None:
        return
    
    if os.path.isdir(d):
      files=os.walk(d)
      
      # delete all the files
      for item in files:
          for sdir in item[1]:
              EmptyDir(item[0]+os.sep+sdir)
          for f in item[2]:
              ff = item[0]+os.sep+f
              os.remove(ff)
              if debugMode():
                print("  removed",ff)
    else:
        os.mkdir(d)
        print("created",d)

    if debugMode():
        print("all files deleted from",d)                 
    
#
# Function to return the type of a file
#
def fTP(f):
    b = os.path.basename(f)
    
    sp = b.split('.')
    if len(sp)>1:
        return sp[len(sp)-1]
    else:
        return "?"

#
# Function to convert post/page content to DITA.
# We can only handle a simple subset of all html.
# Output a list of DITA section elements
#
def html2dita(item):
    global gallery_count
    
    if debugMode():
        print("html2dita",item.tag)
    
    ret = None
 
    etitle = item.find("title")
    item_title = etitle.text
    
    econtent = item.find(contentns+'encoded')
    # filter the raw text to replace [caption, etc
    # with <caption
    if not econtent.text == None:
        ftext = filterText(econtent.text)
        
        # try to make html out of the text in the post/page
        soup = BeautifulSoup(ftext,"html.parser")
        stext = soup.prettify()
    else:
        # item has no text at all
        stext = " "
    
    # wrap the text in an outer div root element
    stext = "<div>"+stext+"</div>"
   
    # Parse the post text string as XML.
    # cceate an XML element from the converted text.
    e = fromstring(stext)

    if debugMode() and develMode():
        print(" **** html2dita initial XML")
        dump(e)

    # initialize for related-links
    related = []
    
    #
    # First pass: make all simple tag substitutions
    #

    # process figure/figcaption
    figures = e.iter("figure")
    for fig in figures:
        fig.tag = 'div'
        figcaps = fig.iter("figcaption")
        for figc in figcaps:
            figc.tag = 'p'
            brs = figc.iter("br")
            for br in brs:
                br.tag = REMOVE
    
        
    # process the anchors
    anchors = e.iter("a")
    for a in anchors:
        href = a.get("href")
        # handle images
        if isImage(href):
            hrefb = os.path.basename(href)
            alttext = a.get('alt')
            a.tag = 'div'
            a.attrib = {}
 
            figtext = alttext
            if figtext == None:
                figtext = a.text
            a.text = ""
            et = Element("p")
            et.text = figtext
            a.insert(0,et)
            
        # it is not an image
        else:
            if fTP(os.path.basename(href)) in ['pdf','zip']:
                a.tag = 'xref'
                a.text = os.path.basename(href)
                a.attrib = {}
                a.set("href",href)
                a.set("scope","external")
                if fTP(os.path.basename(href)) == 'pdf':
                    a.set("format","pdf")
            # check for any links and add them to related links
            elif isURL(href):
                # turn the link into text
                a.tag="ph"
                save_text = a.text+" "+href
                a.clear()
                a.text = save_text
                elink = Element("link")
                elinkt = SubElement(elink,"linktext")
                elinkt.text = a.text
                elink.set("href",href)
                elink.set("scope","external")
                elink.set("format","html")
                # queue this link to related links
                related.append(elink)
            else:
                # some other anchor
                a.tag = 'xref'
                a.text = os.path.basename(href)
                a.attrib = {}
                a.set("href",href)
                a.set("scope","external")

    # handle youtube videos
    for v in e.iter(SIFRAME):
        vid = v.get('src')
        v.tag = 'p'
        v.clear()
        vo = SubElement(v,'object')
        vo.set('data',vid)
        vo.set('outputclass','iframe')

    # caption becomes p
    for c in e.iter(SCAPTION):
        c.tag = 'p'
        alist = []
        for attr in c.attrib:
            alist.append(attr)
        for attr2 in alist:
            del c.attrib[attr2]

    # text for galleries
    for g in e.iter(SGALLERTB):
        album = g.get('album_id')
        g.tag = 'ph'
        g.attrib = {}
        g.text = 'Gallery Album '+album
        print("  >>",SGALLERTB,"in",item_title)
        gallery_count = gallery_count + 1

    # Remove gallery
    for g in e.iter(SGALLERY):
        print("  >>",SGALLERY,"in",item_title)
        gallery_count = gallery_count + 1
        g.tag = REMOVE
 
    # h4 becomes p
    for h4 in e.iter("h4"):
        h4.tag = "p"

    # h5 becomes p
    for h5 in e.iter("h5"):
        h5.tag = "p"

    # em becomes i
    for em in e.iter("em"):
        em.tag = "i"

    # strong becomes b
    for em in e.iter("strong"):
        em.tag = "b"

    # h2 becomes b
    for em in e.iter("h2"):
        em.tag = "b"

    # h3 becomes p followed by b
    for em in e.iter("h3"):
        h3t = em.text
        em.clear()
        em.tag = "p"
        emb = SubElement(em,"b")
        emb.text = h3t

    # blockquote becomes p
    for bq in e.iter("blockquote"):
        bq.tag = "p"

    # span becomes div
    for bq in e.iter("span"):
        bq.tag = "div"
        
    # img becomes image
    for img in e.iter("img"):
        src = img.get("src")
        ikey = path2fnft(src)
        alist = []
        for attr in img.attrib:
            alist.append(attr)
        for attr in alist:
            del img.attrib[attr]
        img.set("href",iPath(ikey))
        img.set('placement','break')
        img.set('align','left')
        img.tag = "image"
        
    # table becomes simpletable
    #  tr becomes strow
    #  td becomes stentry
    for tab in e.iter("table"):
        tab.tag = "simpletable"
    for tr in e.iter("tr"):
        tr.tag = "strow"
    for td in e.iter("td"):
        td.tag = "stentry"

    # get rid of unwanted attributes
    unwanted = ["itemprop","content","style","class","title"]
    for et in e.iter():
        for attr in unwanted:
            if attr in et.attrib:
                del et.attrib[attr]
        

    if debugMode() and develMode():
        print(" **** html2dita start pass 2 XML")
        dump(e)
        
    #
    # Second pass: create multiple sections for h2 and
    # nested sectiondiv for h3.
    #

    slist = []
    elist = list(e)
    # initialize a section
    section = Element("section")
    sectionp = section
    slist.append(section)
    sectid = "body_section"
    section.set("id",sectid)
    nsect = 0

    # pick up text not inside an element
    sectionp.text = e.text

    # add the elements to the current section
    for ee in elist:
        sectionp.append(ee) 
    
    # check for DITA tag nesting problems
    for ss in slist:

        for parent, children in get_parent_children_mapping(ss).items():
            ptag = parent.tag
            
            if children:
                for child in children:
                    ctag = child.tag
                    # honor any element remove requests
                    if ctag==REMOVE:
                        # check for <li><a> and add a text to li
                        # to avoid an empty li bullet
                        if child.get("oldtag") == "a":
                            if parent.tag == "li":
                                if parent.text == None:
                                    parent.text = child.text
                                else:
                                    parent.text = parent.text+" "+child.text
                                
                        parent.remove(child)
                        continue
                    # perform any fixups
                    if (ptag=="text") and (ctag=="b"):
                        wpexp2ditaLog(item_title," %%% fixing",ctag,"inside",ptag)
                        child.tag = "text"
                        continue
                    if (ptag=="p") and (ctag=="p"):
                        wpexp2ditaLog(item_title," %%% fixing",ctag,"inside",ptag)
                        child.tag = "i"
                        continue
                    if ctag=="iframe":
                        wpexp2ditaLog(item_title," %%% remove",ctag)
                        parent.remove(child)
                        continue
                    if (ptag=='text') and (ctag=='i'):
                        ctext = child.text
                        wpexp2ditaLog(item_title," %%% remove italics around",ctext[0:10])
                        parent.remove(child)
                        parent.text = parent.text+" "+ctext
                        continue
                    if ctag=='dd':
                        wpexp2ditaLog(item_title," %%% remove",ctag)
                        parent.remove(child)
                        continue
                    if ctag=="i":
                        ctxt = child.text
                        if not (ctxt==None) and ("Click any photo") in ctxt:
                            wpexp2ditaLog(item_title,"%%% remove Click any photo",ctag)
                            parent.remove(child)
                            continue

    if debugMode() and develMode():
        print(" **** html2dita final XML")
        dump(e)

    
    return slist, related

#
# Function to return child elements of a parent element
#
def get_children(parent):
    return [child for child in parent]

#
# Function to map parents to a list of children
#
def get_parent_children_mapping(tree):
    return { parent: get_children(parent) for parent in tree.iter() }

#
# Function to filter the input text before we parse it as html
#
def filterText(t):
    if debugMode():
        print('filterText:',t[0:40])
    
    # here you can edit the node text as a string
    ft = t

    # replace blank lines with <p/>
    ft = blank2p(ft)
    
    # things to look for
    subs = {'caption':SCAPTION ,'iframe':SIFRAME,'gallery_bank':SGALLERTB,'gallery':SGALLERY}
    
    # look for substitutions
    for s in subs:
        ssub = subs[s]
        found = True
        # check for a substitution needed
        while found:
            found = False
            sfind = '['+s
            i = ft.find(sfind)
            if i>=0:
                # we found something we need to replace
                found = True
                # set start of an element
                ft = ft[:i]+'<'+ft[i+1:]
                j = ft.find(']',i)
                # change end of element
                if j>=0:
                    if s == 'caption':
                        ft = ft[:j]+'>'+ft[j+1:]
                    else:
                        ft = ft[:j]+'/>'+ft[j+1:]
                        
        # substitute for the original text
        ft = ft.replace('<'+s,'<'+ssub)
        ft = ft.replace('[/'+s+']','</'+ssub+'>')
            
            
    return ft

#
# Function to format a URL used to retrieve an image
# by quoting any Unicode characters.
#
def formatURL(u):
    if debugMode():
        print("formatURL:",u)

    uret = u

    # break the URL into parts
    parts = urllib.parse.urlsplit(uret)
    # convert any Unicode to ascii
    oldpath = parts.path
    newpath = urllib.parse.quote(oldpath)
    # if nothing changed, return the original url
    if newpath==oldpath:
        return u

    # return the new url
    newparts = []
    for p in parts:
        newparts.append(p)
    newparts[2] = newpath
    return urllib.parse.urlunsplit(newparts)
    

#
# Function to retrieve an image from the site and store it in a file.
#
def storeImage(imgpath,ipath,idir):
    if debugMode():
        print("storeImage:",imgpath,ipath,idir)
    
    timeout = 10
    
    fpath = ipath
    # set the location to store the image on disk
    iipath = idir+os.sep+imgpath
    retpath = imagesubdir+os.sep+imgpath

    # check if the file is already available locally
    try:
        statr = os.stat(iipath)
    except:
        statr = None

    # if we already have this image, do nothing further
    if not statr == None:
        
        if debugMode():
            print("file",iipath,"stored already")
        return retpath

    # skip image storage while developing
    if develMode():
        if debugMode():
            print("Skip image store in develMode")
        return retpath
    
    # encode any unicode characters in the path to the image
    ufpath = formatURL(fpath)
    
    try:
      # read the image url into a disk file
      uret = urllib.request.urlretrieve(ufpath,iipath)
      if debugMode():
          print("urlretrieve returns",uret)
          print("image",iipath,"stored")
          print("  from",ufpath)

    except urllib.error.URLError as e:
      wpexp2ditaLog(" storeImage URL error",e)
      wpexp2ditaLog("  URL:",fpath)
      wpexp2ditaLog("  reason",e.reason)
      return False

    except urllib.error.HTTPError as e:
      wpexp2ditaLog(" storeImage HTTP error",e)
      wpexp2ditaLog("  URL:",fpath)
      wpexp2ditaLog(" code and reason",e.code,e.reason)
      return False

    except:
      wpexp2ditaLog(" storeImage: other error reading url",ufpath)
      wpexp2ditaLog("  args:",imgpath,ipath,idir)
      return False
        
        
    return retpath

#
# Function to return the file name/type for an output file
#
def itemFile(item,ftype):
    epostid = item.find(wpns+'post_id')
    pidtext = '00000'+epostid.text
    pidtext = pidtext[-5:]
    eposttype = item.find(wpns+'post_type')
    if ftype=='xml':
        item_file = itemdir+"/"+eposttype.text+"_"+pidtext+'.'+ftype
    else:
        item_file = outdir+'/'+eposttype.text+"_"+pidtext+'.'+ftype
    
    return item_file
    
#
# Function to save a page/post item as a file
#
def writeItem(item):
    item_file = itemFile(item,'xml')
    if debugMode():
        print("writing file",item_file)

    # write the item file out
    fp = open(item_file,"w",5000,'utf-8')
    econtent = item.find(contentns+'encoded')
    ectext = econtent.text
    if ectext == None:
        ectext = " "
    cont = '<item>'+ectext+'</item>'
    fp.write(cont)
    fp.close()

#
# Function to save a DITA topic as a file
#
def writeDITA(item,dstring):
    dita_file = itemFile(item,'dita')
    if debugMode():
        print("writing file",dita_file)

    # write the item DITA file out
    fp = open(dita_file,"w")
    fp.write(dstring)
    fp.close()

    return os.path.basename(dita_file)
        
#
# Function to make a DITA topic from an page/post item.
#  item = element for an item
#  topic_string = DITA topic template in a string
#
def item2DITA(item,topic_string):
    if debugMode():
        print("item2DITA",item.tag,topic_string[0:10])

    DITAnode = None
    
    # initialize the DITA XML from the template
    root = fromstring(topic_string)
    tree = ElementTree()
    tree._setroot(root)
    # find the body
    econbody = root.find('conbody')
    
    # start by setting the title
    eititle = item.find('title')
    edtitle = root.find('title')
    edtitle.text = eititle.text
    if develMode():
        edtitle.text = itemFile(item,'dita')+": "+edtitle.text

    # point to the shortdesc element
    edshort = root.find("shortdesc")
    
    # set the author information
    eprolog = root.find('prolog')
    eauthors = eprolog.findall('author')
    eiauthor = item.find(dcns+'creator')
    creator = eiauthor.text
    for a in eauthors:
        a.text = author_table[creator]
        if debugMode():
            print("author set to",a.text)

    
    
    # set the dates
    epubdate = item.find(wpns+'post_date')
    pubstring = epubdate.text[0:10]
    if develMode():
        edtitle.text = edtitle.text+" - "+pubstring
    edates = eprolog.find('critdates')
    ecreate = edates.find('created')
    ecreate.set('date',pubstring)
    erevised = edates.find('revised')
    erevised.set('modified',pubstring)

    # set the short description
    edshort.text = "Posted "+pubstring+" by "+author_table[creator]

    # make the metadata list
    meta_list = []
    all_cats = item.findall('category')
    for c in all_cats:
        try:
           mkey = c.get('nicename')           
           metadata = meta_table[c.get('nicename')]
           meta_list.append(metadata)
           if debugMode():
            print(' *metadata*',c.get('domain'),metadata)
        except:
            meta_list.append(c.text)

    # set the topic metadata index and keyword information
    emetadata = eprolog.find('metadata')
    ekeywords = emetadata.find('keywords')
    for m in meta_list:
        ek = SubElement(ekeywords,'indexterm')
        ek.text = m
    
    elink = item.find('link')
    eother = SubElement(emetadata,'othermeta')
    eother.set('content',elink.text)
    eother.set('name','URL')
    epostid = item.find(wpns+'post_id')
    eother = SubElement(emetadata,'othermeta')
    eother.set('content',epostid.text)
    eother.set('name','post_id')
    eposttype = item.find(wpns+'post_type')
    eother = SubElement(emetadata,'othermeta')
    eother.set('content',eposttype.text)
    ret_type = eposttype.text
    eother.set('name','post_type')

    # if there is a featured image, create a section for it
    allpmeta = item.findall(wpns+'postmeta')
    if len(allpmeta)>0:
        for pm in allpmeta:
            ekey = pm.find(wpns+'meta_key')
            if not ekey==None:
                if ekey.text=='_thumbnail_id':
                    evalue = pm.find(wpns+'meta_value')
                    if debugMode():
                        print("**featured image is",evalue.text)
                    esection = SubElement(econbody,'section')
                    ep = SubElement(esection,'p')
                    eimage = SubElement(ep,'image')
                    eimage.set("id","featured_image")
                    eimage.set("href",iPath(evalue.text))

    # convert the html body text to DITA sections
    sections, links = html2dita(item)

    # add the sections to the output
    for s in sections:
        econbody.append(s)
        if debugMode():
            print("**section:")
            dump(s)
            print()

    # add in any related links
    if len(links)>0:
        erl = SubElement(root,"related-links")
        for link in links:
            erl.append(link)
            
    if debugMode():
        print("*dump of root")
        dump(root)
    
    return ret_type, doctype+tostring(root).decode()


#
# Function to return an image fn.ft from a key
#
def iPath(key):
    ikey = MISSING
    if key in attachments:
        ikey = key
    elif '-' in key:
        kkey = key.split('-')
        ikey = kkey[0]+'.'+fTP(key)
        if not ikey in attachments:
            ikey = MISSING

    # if image was not found, look for an alias
    if ikey == MISSING and not key == MISSING:
        alias = findImageAlias(attachments,key)
        if len(alias)>0:
            # we found an alias
            ikey = alias[0]
            wpexp2ditaLog("image alias: "+ikey)
    if ikey==MISSING:
        if not key==MISSING:
            wpexp2ditaLog("missing image key: "+key)
            missing_keys.append(key)
        
    return attachments[ikey]

#
# Function to test if a file is an image type
#
def isImage(f):
    iexts = (".PNG",".JPG",".GIF",".BMP",".JPEG")
    fdata = os.path.splitext(f)
    fext = fdata[1]
    fext = fext.upper()
    if fext in iexts:
        return True
    else:
        return False
    
#
# Function to test if "file" is actually a URL
#
def isURL(f):
    
    if f.find("http:")>=0:
        return True
    elif f.find("https:")>=0:
        return True
    elif f.find("news:")>=0:
        return True
    elif f.find("mailto:")>=0:
        return True
    else:
        return False

#
# Function to dump the parameter dictionary
#
def dumpPdict(p):
    for par in p:
        print(par)
        print("  ",p[par])

    return

#
# Function to get the categories for a page/post
#
def getCategories(p):
    ret = []
    cats = p.findall("category")
    
    for c in cats:
        cd = c.get("domain")
        if cd == "category":
            ret.append(c.text.upper())
    
    return ret

#
# Function to get the tags for a page/post
#
def getTags(p):
    ret = []
    cats = p.findall("category")
    
    for c in cats:
        cd = c.get("domain")
        if cd == "post_tag":
            ret.append(c.text.upper())
            
    return ret

#
# Function to create unique image fn/ft from image path
#
def path2fnft(p):
    if debugMode():
        print("path2fnft:",p)

    ret = MISSING
    uploads = "uploads"
    
    # break path into pieces
    parts = p.split('/')
    
    # look for required part of path
    try:
        ppos = parts.index(uploads)
        lparts = len(parts)
    
    except:
        wpexp2ditaLog("path2fnft invalid path "+p)
        return ret

    # check for enough parts in path
    if ppos+3 >= lparts:
        wpexp2ditaLog("path2fnft invalid path "+p)
        return ret

    # get and check path parts
    yr = parts[ppos+1]
    mn = parts[ppos+2]
    fnft = parts[ppos+3]
    
    try:
        i = int(yr)
        j = int(mn)
    except:
        wpexp2ditaLog("path2fnft invalid path "+p)
        return ret
        
    ret = "image_"+yr+"_"+mn+"_"+fnft       
        
    return ret

#
# Function to replace blank lines with <p/> to stop DITA
# from mashing all the text together.
#
def blank2p(txt):
    if debugMode():
        print("blank2p:",len(txt),txt[0:20])

    # split the text into lines
    lines = txt.splitlines()
    nline = len(lines)
    if debugMode():
        print("lines",nline)

    # handle trivial cases
    if nline <= 1:
        return txt

    # replace blank lines with <p/>
    for n in range(nline):
        line = lines[n]
        if line == '' or line.isspace():
            lines[n] = "<p/>"

    # combine the lines back together into a single string
    txt2 = os.linesep.join(lines)

    return txt2

#
# Function to find a missing attachment pattern
# by looking for an alias.
#
def findImageAlias(attachments,key):

    if debugMode():
        print("findImageAlias:",key)

    # special case
    if key == MISSING:
        return ret
    
    ret = []
    kparts = key.split('.')
    kfn = kparts[0]
    
    for a in attachments:
        aparts = a.split('.')
        afn = aparts[0]
        if len(aparts) == 2:
            if kfn in afn:
                ret.append(a)
            elif afn in kfn:
                ret.append(a)

    return ret

###################################
# PROCESSING INITIALIZATION SECTION
###################################

# set debugging controls
setdebug(False)
setdevel(False)

#
# print script signon message
#
print("wpexp2dita utility begins at",tStamp())

#
# Set the input parameters for the WordPress site being processed
#

# parse the input parameters file
if len(sys.argv)>1:
    parm_file = sys.argv[1]
else:
    parm_file = "wpexp2dita.xml"
    
wpexp2ditaLog("parm file set to "+parm_file)
pdict = parseParms(parm_file)

# set the parameters for this run
for p in pdict:
    stmt = p+"='"+pdict[p]+"'"
    exec(stmt)

# reformat some parameters
if len(year_list)>0:
    year_list = year_list.split(",")
if len(category_list)>0:
    category_list = category_list.split(",")
    ucategory_list = [c.upper() for c in catregory_list]
if len(tags_list)>0:
    tags_list = tags_list.split(",")
    utags_list = [t.upper() for t in tags_list]
    
if include_pages != None:
    c1 = include_pages[0]
    if c1.upper() == "Y":
        include_pages = True
    else:
        include_pages = False
        

# initial setup of the output directory
# set output directory
outdir = "wpexp2dita."+website

# create a directory for the images and items
imagesubdir = "images"
imagedir = outdir+"/"+imagesubdir
try:
    os.mkdir(imagedir)
except:
    pass
itemsubdir = "items"
itemdir = outdir+"/"+itemsubdir
try:
    os.mkdir(itemdir)
except:
    pass 

total_nodes = 0
image_count = 0

node_data = {}

###################################
#
# MAIN PROCESSING SECTION
#
###################################

# build an XML tree from the WordPress export XML file

if not os.path.exists(input_file):
    print("Error, input file does not exist")
    print("  "+input_file)
    exit(0)
    
try:
    tree = parse(input_file)
    root = tree.getroot()
except:
    print("Error, could not parse",input_file)
    exit(0)

# get the root element of the tree and validate it
root = tree.getroot()
if debugMode():
    print("XML root:",root.tag)
if not root.tag == 'rss':
    print("Error, root element is not rss")
    exit(0)

# display the input parameters and files being used
print("settings:")
print("input file:",input_file)
print("  output title:",archive_title)
print("  website:",website)
print("  output DITA files:",outdir)
print("  output images:",imagedir)
print("  topic template file:",template)
print("  splash page file:",splash_page)
print("  splash page images:",splash_page_images)
print("  bookmap template file:",template_map_pdf)
print("  web map template file:",template_map_web)
print("  content type template file:",template_dir_map)
print("  include pages:",include_pages)
if len(year_list)>0:
    print("  years included:",year_list)
if len(category_list)>0:
    print("  categories included:",category_list)
if len(tags_list)>0:
    print("  tags included:",tags_list)
if develMode():
    print("*** Running in developer mode")

wpexp2ditaLog(tStamp()+" Start error log")

# do some more input file format validation and collect some
# basic information
chan = root.find('channel')
if not chan.tag == 'channel':
    print("Error, input file has no channel element")
    exit(0)

# stuff we put in the book title
echant = chan.find("title")
chan_title = echant.text
echanl = chan.find("link")
chan_link = echanl.text
echandesc = chan.find("description")
chan_desc = echandesc.text
echanpDate = chan.find("pubDate")
chan_pubDate = echanpDate.text

author0 = chan.find(wpns+'author')
if author0 == None:
    print("Error, input file has no wp:author elements")
    exit(0)

# read in the web template ditamap file
fp = open(template_map_web,"r")
mapstring = fp.read()
fp.close()
# save the web doctype
pw = mapstring.find("<map")
mapdoctype = mapstring[0:pw]
# initialize the web map DITA XML
maproot = fromstring(mapstring)

# read in the pdf template ditamap file
fp = open(template_map_pdf,"r")
mapstringpdf = fp.read()
fp.close()
# save the pdf doctype
pw = mapstringpdf.find("<bookmap")
mapdoctypew = mapstringpdf[0:pw]
# initialize the pdf map DITA XML
maprootpdf = fromstring(mapstringpdf)

# create the author table dictionary
author_table = {}
all_authors = chan.findall(wpns+'author')
print("there are",len(all_authors),"item authors")
for au in all_authors:
    elogin = au.find(wpns+'author_login')
    login = elogin.text
    efirst = au.find(wpns+'author_first_name')
    elast = au.find(wpns+'author_last_name')
    first_name = efirst.text
    if first_name == None:
        first_name = ""
    last_name = elast.text
    if last_name == None:
        last_name = ""
    author_table[login] = first_name+" "+last_name
    print("  ",login,"=",author_table[login])

# create the metadata tables of tags and categories
cat_list = []
tag_list = []
meta_table = {}
all_cats = chan.findall(wpns+'category')
print("there are",len(all_cats),"categories")
for c in all_cats:
    ckey = c.find(wpns+'category_nicename').text
    ctext = c.find(wpns+'cat_name').text
    meta_table[ckey] = ctext
    if not ctext in cat_list:
        cat_list.append(ctext.upper())
        
all_terms = chan.findall(wpns+'term')
print("there are",len(all_terms),"terms")
for t in all_terms:
    tkey = t.find(wpns+'term_slug').text
    ttext = t.find(wpns+'term_name').text
    meta_table[tkey] = ttext
    if not ttext in tag_list:
        tag_list.append(ttext.upper())

# save the category and tag information in output files
print("there are",len(cat_list),"categories")
f = codecs.open(cat_file,"w","utf-8")
for c in sorted(cat_list):
    print(c,file=f)
f.close()
print("there are",len(tag_list),"tags")
f = codecs.open(tag_file,"w","utf-8")
for c in sorted(tag_list):
    print(c,file=f)
f.close()

# get a list of all the page/post items
allitems = chan.findall('item')
print("there are",len(allitems),"items")

plist = {}
# count post types and build lists for each type
for a in allitems:
    pt = a.find(wpns+'post_type')
    pts = pt.text
    if pts in plist:
        plist[pts].append(a)
    else:
        plist[pts] = [a]

for p in plist:
    print("%5d %s" % (len(plist[p]),p))

# images with post_id key
attachments = {}

print("Loading attachments (images)")

# Load the attachments (images) plus the missing image file
# and remember in the attachments dictionary where they are.
shutil.copy(missing_image,imagedir)
splash_page_path = os.path.basename(splash_page)
copy_tree(splash_page_images,imagedir)
# Store the splashpage
shutil.copy(splash_page,outdir)

# try to link in the splash page
efrontm = maprootpdf.find("frontmatter")
if efrontm != None:
    esplash = Element("topicref")
    esplash.set("href",splash_page_path)
    efrontm.insert(0,esplash)
else:
    wpexp2ditaLog("Error, could not add splash page link")

attachments[MISSING] = imagesubdir+"/"+missing_image_base
ni = 0

# load the images from the site
for a in plist['attachment']:
    ni = ni+1
    if ni%100 == 0:
        print(" 100 images processed")
    # element for post_id
    ide = a.find(wpns+'post_id')
    # image id
    id = ide.text
    # element for attachment url
    aurl = a.find(wpns+'attachment_url')
    # url for attachment on WordPress site
    furl = aurl.text
    # image base filename/type from original url
    ibase = path2fnft(furl)
    # return where image was stored
    ret = storeImage(ibase,furl,imagedir)
    # store information about the image in a dictionary
    attachments[id] = ret
    attachments[ibase] = ret
    # convenient alias
    attachments[WPIMAGE+id] = ret
    if debugMode():
        exit(0)   
   
# resize the images we just read to disk
print("resize images in",imagedir)
resizeImages(imagedir)

# read in the template DITA file (a concept)
fp = open(template,"r")
tstring = fp.read()
fp.close()
# save doctype
p = tstring.find("<concept")
doctype = tstring[0:p]          

# sort the pages and post by reverse posting date
if debugMode():
    print("creating sorted lists of pages and posts")
post_slist = []
page_slist = []

# first and last year for the content items
year_first = None
year_last  = None

for p in plist['post']:
    epdate = p.find(wpns+'post_date')
    pyear = epdate.text[0:4]
    post_slist.append([epdate.text,p])
    if year_first == None:
        year_first = pyear
    if year_last == None:
        year_last = pyear
    if pyear<year_first:
        year_first = pyear
    if pyear>year_last:
        year_last = pyear
        
if include_pages:
  for p in plist['page']:
    epdate = p.find(wpns+'post_date')
    pyear = epdate.text[0:4]
    page_slist.append([epdate.text,p])
    if year_first == None:
        year_first = pyear
    if year_last == None:
        year_last = pyear
    if pyear<year_first:
        year_first = pyear
    if pyear>year_last:
        year_last = pyear
        
        
if include_pages:
 page_slist.sort(reverse=True)
post_slist.sort(reverse=True)

# process all the page/post items
print("processing posts and pages")
topics = []
ptypes = {}
nditafile = 0
for tp in post_slist+page_slist:
        # set year this was created
        tcreate = tp[0][0:4]
        tpost = tp[1]
        tcats = getCategories(tpost)
        ttags = getTags(tpost)
        # select certain creation years, if required
        if len(year_list)>0:
            if tcreate in year_list:
                process=True
            else:
                process=False
        else:
            process=True

        # do any necessary category selection
        if process & (len(ucategory_list)>0):
            cflag = False
            for c in tcats:
                if c.upper() in ucategory_list:
                    cflag = True
                    break
            if cflag:
                process = True
            else:
                process = False

        # do any necessary tag selection
        if process & (len(utags_list)>0):
            tflag = False
            for t in ttags:
                tup = t.upper()
                if tup in utags_list:
                    tflag = True
                    break
            if tflag:
                process = True
            else:
                process = False
                
        # this one is to be processed
        if process:
          # create DITA file text
          ptype, DITAstr = item2DITA(tpost,tstring)
          writeItem(tpost)
          # write out the DITA file
          df = writeDITA(tpost,DITAstr)
          nditafile = nditafile+1
          topics.append(df)
          ptypes[df] = ptype

# set the web version ditamap title
maproot.set("title",archive_title)

# set the book ditamap title
booktitle = maprootpdf.find("booktitle")
mainbooktitle = booktitle.find("mainbooktitle")
mainbooktitle.text = archive_title
booktitlealt = booktitle.find("booktitlealt")
if len(year_list)==0:
  if year_first == year_last:
    btatext = year_first
  else:
    btatext = year_first+"-"+year_last
else:
    btatext = ""
    for y in year_list:
        btatext = btatext+y+" "
        
# set the alternate title
if len(category_list)>0:
    btatext = btatext+", categories: "
    for c in category_list:
        btatext = btatext+" "+c
        
if len(tags_list)>0:
    btatext = btatext+", tags: "
    for t in tags_list:
        btatext = btatext+" "+t
        
booktitlealt.text = chan_desc

# add subtitles with more information
btalt = SubElement(booktitle,"booktitlealt")
btalt.text = "Site title: "+chan_title
btalt = SubElement(booktitle,"booktitlealt")
btalt.text = "Year range: "+btatext
btalt = SubElement(booktitle,"booktitlealt")
btalt.text = "Site URL: "+chan_link
btalt = SubElement(booktitle,"booktitlealt")
btalt.text = "Exported: "+chan_pubDate

# get the chapter elements needed
chapters = maprootpdf.findall('chapter')
for c in chapters:
    nav = c.get('navtitle')
    if nav=='Posts':
        chapter_post = c
    else:
        chapter_page = c

# add all the topicrefs for the included topics
for t in topics:
    etopic = SubElement(maproot,'topicref')
    etopic.set('href',t)
    if ptypes[t] == 'post':
        eptopic = SubElement(chapter_post,'topicref')
    else:
        eptopic = SubElement(chapter_page,'topicref')
    eptopic.set('href',t)
    eptopic.set('toc','no')
                                 
# write out the web ditamap
outstr = mapdoctype+tostring(maproot).decode()
outmappath = outdir+os.sep+"WordPress.ditamap"
fp = open(outmappath,"w")
print("writing",outmappath)
fp.write(outstr)
fp.close()

# write out the pdf ditamap
outstr = mapdoctypew+tostring(maprootpdf).decode()
outmappath = outdir+os.sep+"WordPress_pdf.ditamap"
fp = open(outmappath,"w")
print("writing",outmappath)
fp.write(outstr)
fp.close()

# show cat and tag files
if debugMode():
    print()
    print(cat_file,"written")
    print(tag_file,"written")

# print some final statistics
if debugMode():
    print()
    print("galleries =",gallery_count)

print(nditafile,"DITA files written")
wpexp2ditaLogClose()
print(log_file_lines,"lines written to",log_file)

# all done
print()
print("wpexp2dita utility ends at",tStamp())





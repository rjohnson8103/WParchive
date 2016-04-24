#
# PROLOG SECTION
# deconstructwp.py
#
# A script that extracts newsfromnan WordPress content into files.
#
# This script is the first part of a 2-part process to extract
# content items from a WordPress web site and archive
# them as a PDF. The 2nd part script, manifest2dita.py, reads the
# output produced by this script and transforms it into a set of
# DITA topics and maps that can be published as PDF.
#
# Outputs:
#  An XML manifest file (manifest.xml) that catalogs
#  all the information extracted from the WordPress site.
#
#  A subdirectory for each content type containing one
#  file for each node containing its text.
#
# Tested with Python 3.3.2
# April 24, 2016
#
# Author: Dick Johnson
#
###################################

###################################
# ENVIRONMENT SETUP SECTION
###################################

# import the common processing code
from ditapub import *
import datetime
import urllib.request
import urllib.error
import urllib.parse
from bs4 import BeautifulSoup
from PIL import Image

# file object for the web site error log file
log_fileobj = None

blogid = 1

UNCAT = "Uncategorized"
SGALLERY = "[gallery "
SCAPTION = "[caption "
FEATURED_IMAGE = "featured"

user_dict = {}

###################################
# FUNCTION DEFINITION SECTION
###################################

#
# Function to write a text line to the
# web site error log
#
def webErrorLog(*s):
    global log_fileobj
    log_file = "deconstructError.log"
        
    if log_fileobj == None:
        log_fileobj = open(log_file, "w")

    print(s, file=log_fileobj)
    print("***webErrorLog:",s)

    return

#
# Function to close the web site error log
#
def webErrorLogClose():
    global log_fileobj
    if not log_fileobj == None:
        log_fileobj.close()
        log_fileobj = None

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
# Function to get the categories and terms for a post.
#
def getPostCats(p):
    
    cats = []
    terms = []
    pterms = p["terms"]
    
    for t in pterms:
        tax = t["taxonomy"]
        
        if tax == "category":
            cats.append(t["name"].replace(" ","_"))
        if tax == "post_tag":
            terms.append(t["name"])

    return cats, terms

#
# Function to get the primary category for a post
#
def getCategory(p):

    if p['post_type'] == 'page':
        return "StaticPages"
    
    clist, tlist = getPostCats(p)

    if len(clist)==0:
        print("Error, post has n category!")
        formatDict(p)
        exit(0)

    cdef = clist[0]
    for c in clist:
        if not c==UNCAT:
            return c
        else:
            cdef = c

    return cdef

#
# Function to get information about a user id
#
def getWPUser(id):
    if debugMode():
        print("getWPUser",id)

    sendf=False
    for i in range(get_maxretry()):
            try:
                ret=proxy.wp.getUser(blogid,get_user(),get_password(),id)
                sendf=True
                break;
            except xmlrpc.client.Fault as err:
                print("A fault occurred")
                print("Fault code: %d" % err.faultCode)
                print("Fault string: %s" % err.faultString)
                exit(0)
            except xmlrpc.client.ProtocolError as err:
                print("A protocol error occurred")
                print("URL: %s" % err.url)
                print("HTTP/HTTPS headers: %s" % err.headers)
                print("Error code: %d" % err.errcode)
                print("Error message: %s" % err.errmsg)
                exit(0)

            except:
                errCnt()
                print(" WordPress XMLRPC error!",i+1)
                ret="WordPress XMLRPC error"
                time.sleep(get_retrysleep())

    if not sendf:
        ret=proxy.wp.wp.getUser(blogid,get_user(),get_password(),id)
        
    # return the user structure
    return ret

#
# Function to get all WordPress posts
#
def getWPposts(ptype):
    if debugMode():
        print("getWPposts",blogid)

    qarg = {"post_type":ptype,"number":500}
    
    sendf=False
    for i in range(get_maxretry()):
            try:
                ret=proxy.wp.getPosts(blogid,get_user(),get_password(),qarg)
                sendf=True
                break;
            except xmlrpc.client.Fault as err:
                print("A fault occurred")
                print("Fault code: %d" % err.faultCode)
                print("Fault string: %s" % err.faultString)
                exit(0)
            except xmlrpc.client.ProtocolError as err:
                print("A protocol error occurred")
                print("URL: %s" % err.url)
                print("HTTP/HTTPS headers: %s" % err.headers)
                print("Error code: %d" % err.errcode)
                print("Error message: %s" % err.errmsg)
                exit(0)

            except:
                errCnt()
                print(" WordPress XMLRPC error!",i+1)
                ret="WordPress XMLRPC error"
                time.sleep(get_retrysleep())

    if not sendf:
        ret=proxy.wp.wp.getPosts(blogid,get_user(),get_password().qarg)
        
    # return the posts content structure
    return ret

#
# Function to get WordPress media library information
#
def getWPMediaLibrary():
    if debugMode():
        print("getWPMediaLibrary")

    sendf=False
    for i in range(get_maxretry()):
            try:
                ret=proxy.wp.getMediaLibrary(blogid,get_user(),get_password())
                sendf=True
                break;
            except xmlrpc.client.Fault as err:
                print("A fault occurred")
                print("Fault code: %d" % err.faultCode)
                print("Fault string: %s" % err.faultString)
                exit(0)
            except xmlrpc.client.ProtocolError as err:
                print("A protocol error occurred")
                print("URL: %s" % err.url)
                print("HTTP/HTTPS headers: %s" % err.headers)
                print("Error code: %d" % err.errcode)
                print("Error message: %s" % err.errmsg)
                exit(0)

            except:
                errCnt()
                print(" WordPress XMLRPC error!",i+1)
                ret="WordPress XMLRPC error"
                time.sleep(get_retrysleep())

    if not sendf:
        ret=proxy.wp.wp.getMediaLibrary(blogid,get_user(),get_password())
        
    # return the media content structure
    return ret

#
# Function to get the thumbnail URL for a media id
#
def getMediaThumbURL(id):
    if debugMode():
        print("getMediaThumbURL:",id)

    url = None
    
    for m in MediaLib:
        if id==m['attachment_id']:
            mdata = m['metadata']
            link = m['link']
            msizes = mdata['sizes']
            mimage = msizes['thumbnail']['file']
            url = os.path.dirname(link)+'/'+mimage

    if url==None:
        print("Error!, link for",id,"not found")

    return url
#
# Function to map an image uri to a unique filename
#
def mapFname(uri):
    global file_ident
    
    if debugMode():
        print("mapFname",uri)
    
    base = os.path.basename(uri)

    p = base.find(".")
    
    ret = base[0:p]+"_"+str(file_ident)+base[p:]

    # replace umlauts
    ret = ret.replace("ü","ue")
    
    file_ident = file_ident+1
    
    return ret

#
# Function to empty a directory
#
def EmptyDir(d):
    if debugMode():
        print("EmptyDir",d)

    if os.path.isdir(d):
      files=os.walk(d)
      # delete all the files
      for item in files:
          for f in item[2]:
              ff = item[0]+os.sep+f
              os.remove(ff)
              if debugMode():
                print("  removed",ff)
    else:
        os.mkdir(d)
    # delete any subdirectories
    dirs = os.walk(d)
    for dd in dirs:
        for ddir in dd[1]:
          os.rmdir(dd[0]+os.sep+ddir)

    print("all files deleted from",d)
    
#
# Function to list the supported XMLRPC methods
#
def listMethods():
    if debugMode():
        print("listMethods:")
        
    try:
       ret=proxy.system.listMethods()
    except xmlrpc.client.Fault as err:
        print("A fault occurred")
        print("Fault code: %d" % err.faultCode)
        print("Fault string: %s" % err.faultString)
        exit(0)
    except xmlrpc.client.ProtocolError as err:
        print("A protocol error occurred")
        print("URL: %s" % err.url)
        print("HTTP/HTTPS headers: %s" % err.headers)
        print("Error code: %d" % err.errcode)
        print("Error message: %s" % err.errmsg)
        exit(0)



    if debugMode():
        print("Supported XMLRPC Methods")
        for m in ret:
            print("  ",m)

    return ret


#
# Function to retrieve an image from the site and store it in a file.
#
def storeImage(imgpath,ipath,url,idir):
    if debugMode():
        print("storeImage:",imgpath,ipath,url,idir)
    
    timeout = 10
    # set url to fetch the image from using absolute or relative url
    if not "http:" in ipath:
        fpath = url+ipath
    else:
        fpath = ipath
    # set the location to store the image on disk
    iipath = idir+os.sep+imgpath

    # encode any unicode characters
    ufpath = formatURL(fpath)
    
    try:
      # read the url into a disk file
      uret = urllib.request.urlretrieve(ufpath,iipath)
      if debugMode():
          print("image",iipath,"stored")

    except urllib.error.URLError as e:
      webErrorLog(" storeImage URL error",e)
      webErrorLog("  URL:",fpath)
      return False

    except:
      webErrorLog(" storeImage other error",ufpath)
      webErrorLog("  args:",imgpath,ipath,url,idir)
      return False
        
        
    return True

#
# Function to format a dictionary
#
def formatDict(d):
    if type(d) is dict:
        for dd in d:
            print(dd,d[dd])
    else:
        print("formatDict arg is not a dictionary.")
        print(d)

#
# Function to expand gallery short codes like [gallery ids="17,16,15,14"]
#
def expandGallery(s):
    if debugMode():
        print("expandGallery:",s)
        
    # get start of gallery
    i = s.find(SGALLERY)

    if i<0:
        print("expandGallery found no gallery!")
        print(s)
        exit(0)

    # get end of gallery
    iend = s.find("]",i)

    gal = s[i:iend+1]

    # get ids in the gallery
    ii = gal.find('"')
    iiend = gal.find('"',ii+1)
    ids = gal[ii+1:iiend]
    ilist = ids.split(',')
    
    # get the media thunb URLs from the ids
    thumbs = {}
    for il in ilist:
        thumbs[il] = getMediaThumbURL(il)
    
    # create replacement string
    srep = "\n"
    for img in thumbs:
        url = thumbs[img]
        ap = '<img class="gallery-image" src="'+url+'"/>'
        ap = ap+"\n"
        srep = srep+ap

    # replace the gallery
    sret = s.replace(gal,srep)
            
    return sret

#
# Function to test if file is an image
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
# Function to turn text lines into <p> elements
#
def makeParagraphs(s):
    if debugMode():
        print("makeParagraphs:",s[0:20])
    
    sss = s.strip()
    splist = []

    slines = sss.splitlines()
    nlines = len(slines)
    if debugMode():
      print("text contains",nlines,"lines of text")
    if nlines>0:
        for ss in slines:
            sp = "<p>"+ss+"</p>"
            splist.append(XML(sp))
    
    return splist

#
# Function to make last minute changes to the text
#
def filterText(s):

    ss = s

    # handle ü
    ss = ss.replace("&#252;","ue")

    return ss

###################################
# PROCESSING INITIALIZATION SECTION
###################################

# set debugging control
setdebug(False)
# only process a single node, if true
testmode = False

# set the CMS to WordPress
set_cms("WordPress")

# set retry/sleep values
set_maxretry(5)
set_retrysleep(5)
set_maxretry(1)
set_retrysleep(1)

# unique file identifier
file_ident = 0

#
# signon to the site for XML-RPC
#
print("deconstructwp utility begins")
print()

# set the site URL
WordPressurl = "http://local.sample.com/"

# set the url to be used for XML-RPC calls
WordPress = WordPressurl+"xmlrpc.php"
set_cms_url(WordPress)

# calculate the relative base to the URL
set_base_url(baseURL(WordPressurl))

# set the site user and password
user="admin"
set_user(user)
password = "password"
set_password(password)

print("WordPress URL:",WordPressurl)
print(" username:",user,",password:",password)

print("max communication retry:",get_maxretry())
print("communication retry sleep:",get_retrysleep())
print()

# initial setup of the output directory
# set output directory
outdir = "deconstruct"
EmptyDir(outdir)
# create a directory for the images
imagedir = outdir+os.sep+"images"
os.mkdir(imagedir)

# set the XML manifest output file
xml_file = "manifestwp.xml"

total_nodes = 0
image_count = 0

istored = {}
unparsed = []

###################################
#
# MAIN PROCESSING SECTION
#
###################################

# start up server communication
print("starting communication with server",WordPressurl)
try:
    proxy = xmlrpc.client.ServerProxy(WordPress, allow_none=True)
    print("Communication started.")
except:
    webErrorLog("Error, could not set server proxy!")
    exit(0)

# initialize some variables    
set_proxy(proxy)

# read in all the posts/pages and make the category list
Posts = getWPposts('post')
Pages = getWPposts('page')
for pg in Pages:
    Posts.append(pg)
category_list=[]

print()
for p in Posts:
    if debugMode():
        print("Post:",p["post_name"])        
    c = getCategory(p)
    if not c in category_list:
      category_list.append(c)
                
if debugMode():
    print("category list:",category_list)

catdirs = {}
# create directories for the categories used
for tp in category_list:
    catdir = outdir+os.sep+tp
    os.mkdir(catdir)
    print("created",catdir)
    catdirs[tp]=catdir

# get information about all the media
MediaLib = getWPMediaLibrary()
if debugMode():
    for m in MediaLib:
        print()
        formatDict(m)

print()
print("there are",len(Posts),"posts")
print("there are",len(Pages),"pages")
print("there are",len(MediaLib),"items in the media library")
print("there are",len(category_list),"categories")

# initialize the xml output file
# and create the XML root
melement = Element("manifest")
# base level information
tree = ElementTree(melement)
root = tree.getroot()
ctype_dict = {}
    
stampe = SubElement(root,"timestamp")
today = date.today()
stampe.text = today.isoformat()
ose = SubElement(root,"os")
ose.text = os.environ["OS"]
compe = SubElement(root,"computer")
compe.text = os.environ["COMPUTERNAME"]
unamee = SubElement(root,"computer_user")
unamee.text = os.environ["USERNAME"]
cmse = SubElement(root,"CMS")
cmse.text = "WordPress"
root.set("images",imagedir)
root.set("outdir",outdir)

# add category base for each category
for c in category_list:
    # directory for the files
    cdir = catdirs[c]
    ce = SubElement(root,"ctype")
    ce.set("type",c)
    ce.set("dir",cdir)
    ctype_dict[c]=ce

#
# Now process all the posts
#

for p in Posts:
    print()
    pid = p["post_id"]
    # collect post information
    ptitle = p["post_title"]
    if ptitle=="":
        ptitle="notitle"
    pname = p["post_name"]
    plink = p['link']
    # pick yymmdd from date
    pdate = str(p['post_date'])[0:8]
    pcats,ptags = getPostCats(p)
    pcat = getCategory(p)
    # add the node to the manifest
    ce = ctype_dict[pcat]
    ne = SubElement(ce,"node")
    ne.set("created",pdate)
    print('Post',pid,': "'+ptitle+'"',pname,pcat)
    # get author information
    pauthid = p['post_author']
    if not pauthid in user_dict:
        pret = getWPUser(pauthid)
        dname = pret['display_name']
        user_dict[pauthid] = dname
    ne.set("user",user_dict[pauthid])
    
    imagese = SubElement(ne,"images")
    
    # check for a featured image
    PTHUMB = "post_thumbnail"
    pimage = None
    if PTHUMB in p:
        pthumb = p[PTHUMB]
        if not pthumb==[]:
            pimage = pthumb["thumbnail"]
            if debugMode():
              print("featured image",pimage)
            # read the image and store it
            ibase = os.path.basename(pimage)
            imguri = pimage
            ibase = mapFname(imguri)
            irc = storeImage(ibase,imguri,WordPressurl,imagedir)
            # save image data
            impath = imagedir+"/"+ibase
            im = Image.open(impath)
            width  = im.size[0]
            height = im.size[1]
            ie = SubElement(imagese,"image")
            ie.set("field",FEATURED_IMAGE)
            ie.set("uri",pimage)
            ie.text = "image of "+pthumb['title']
            ie.set("filename",impath)
            ie.set("height",str(height))
            ie.set("width",str(width))
            image_count = image_count+1
                         
        
    # set output file path
    fpath = catdirs[pcat]+os.sep+"post_"+pid+"_"+pname+".html"
    fpath = fpath.replace("-","_")
    # get the raw node text
    ftext = p['post_content']
    # try to make html out of it
    soup = BeautifulSoup(ftext)
    stext = soup.prettify()
    # wrap the text in an outer root element
    stext = "<div>"+stext+"</div>"

    # expand any galleries to image references
    if SGALLERY in stext:
        print(" expanding a gallery")
        stext = expandGallery(stext)

    # delete [caption ...] shortcodes
    if SCAPTION in stext:
        while SCAPTION in stext:
          cstart = stext.find(SCAPTION)
          cend = stext.find("]",cstart)
          stext = stext[0:cstart]+stext[cend+1:]
        stext = stext.replace("[/caption]","")
   
    # parse the post string as XML
    parse_error = False
    
    temproot = fromstring(stext)
           
    # make a list of all the img elements
    imgs = temproot.findall(".//img")
    if len(imgs)>0:
        print(" post has",len(imgs),"image references")
    ifailures = False
    
    for img in imgs:
        image_count = image_count+1
        isrc = img.get("src")
        siteurl = get_base_url()
        ibase = os.path.basename(isrc)
        imguri = isrc
        ibase = mapFname(imguri)
          
        # read and store an image
        irc = storeImage(ibase,imguri,WordPressurl,imagedir)
          
        if not irc:
            ifailures = True
        img.set("src",os.path.dirname(isrc)+"/"+ibase)
        if debugMode():
            print("  store referenced image",ibase)
            print("  href",img.get("src"))

    # fix any image anchors
    aa = temproot.findall(".//a")
    for a in aa:
        ahref = a.get("href")
        if isImage(ahref):
            del a.attrib['href']
          

    # turn any leading or trailing text into paragraph elements
    nl = 0
    # look for leading text in root element
    if not temproot.text==None:
        if debugMode():
          print("TEXT:",len(temproot.text))
          print(temproot.text)
        # convert the text to paragraphs
        elist = makeParagraphs(temproot.text)

        # replace the text with paragraphs
        j = 0
        for enew in elist:
            if debugMode():
              print("inserting text element",j)
              print(tostring(enew))
            temproot.insert(j,enew)
            j=j+1
        temproot.text = None

    # look for trailing text in the last sub-element
    elast = None
    for e in temproot.iter():
      elast = e
      nl=nl+1

    if not elast==None:           
     if not elast.tail==None:
        if debugMode():
          print("TAIL:",len(elast.tail))
          print(elast.tail)
        # convert the text to paragraphs
        elist = makeParagraphs(elast.tail)

        # replace the text with paragraphs
        j = nl
        for enew in elist:
            if debugMode():
              print("enew:")
              print(tostring(enew))
              print("inserting tail element",j)
            temproot.insert(j,enew)
            j=j+1
        elast.tail = None
          
            
    # replace the original text
    stext = tostring(temproot).decode()

    # filter the final text
    stext = filterText(stext)
    
    
    if ifailures:
        webErrorLog("image failures in",fpath,ptitle)
 
        
    # write out the text to a file
    print(" writing",fpath)
    f = open(fpath,"w")
    f.write(stext)
    f.close()
    total_nodes = total_nodes+1
            
    # populate manifest XML for this post
    ne.set("id",p['post_id'])
    ne.text = ptitle
    ne.set("link",plink)
    ne.set("path",fpath)
    tes = SubElement(ne,"tags")
    if len(ptags)>0:
        for tag in ptags:
            te = SubElement(tes,"tag")
            te.text = tag

# write the manifest XML file
print()
print("processing complete")
print()
print("Writing output XML manifest file",xml_file)
tree.write(xml_file,encoding="UTF-8")
print()

# terminate
webErrorLogClose()
print("Node count",total_nodes)
print("Image count",image_count)
print("deconstructwp utility ends")




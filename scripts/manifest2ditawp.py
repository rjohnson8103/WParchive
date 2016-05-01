#
# PROLOG SECTION
# manifest2ditawp.py
#
# A script that processes newsfromnan posts mined by
# deconstructwp.py and creates dita source files from them.
# 
# Tested with Python 3.4.3
# May 1, 2016
#
# Author: Dick Johnson
#
###################################

###################################
# ENVIRONMENT SETUP SECTION
###################################

import os
from xml.etree.ElementTree import *
import shutil
from PIL import Image

# global variables for this script
dbgflag = True
develflag = False
testmode = False
cms = None
DRUPAL = "Drupal"
WORDPRESS = "WordPress"

logfp = None
# set true to add date and author to title
longtitle = False

# how to sort the topics in the output map
STITLE = 1
SCHRON = 2
sorttype = STITLE

if sorttype == SCHRON:
    NTYPE = 0
    NCREATE = 1
    NFNFT = 2
    NFPATH = 3
    NTITLE = -1
else:
    NTYPE = 0
    NTITLE = 1
    NCREATE = 2
    NFNFT = 3
    NFPATH = 4
    

# file object for the web site error log file
log_fileobj = None

# special image files used in processing
missing_image =     "common/processing_files/images/missing_image.jpg"
splash_page_image = "common/processing_files/images/splash_page_image.jpg"

###################################
# FUNCTION DEFINITION SECTION
###################################

#
# Function to write a text line to the
# web site error log
#
def webErrorLog(*s):
    global log_fileobj
    log_file = "manifest2ditaError.log"
    
    if debugMode():
        print("webErrorLog:",s)

    if log_fileobj == None:
        log_fileobj = open(log_file, "w")

    print(s, file=log_fileobj)
    print(s)

    return

#
# Function to close the web site error log
#
def webErrorLogClose():
    global log_fileobj
    if not log_fileobj == None:
        log_fileobj.close()
        log_fileobj = None
        
def setdevel(flag):
    global develflag
    develflag = flag
    if develflag:
        print("we are in developer mode!")
    return

def develMode():
    return develflag

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
# Function to resize the image files
#
def resizeImages(imagedir):
    if debugMode():
        print("resizeImages",imagedir)

    # maximum image width in pixels
    maxwidth = 450

    if debugMode():
        print("maximum image width",maxwidth)

    cnt = 0
    tot = 0

    # get the file names of all the images
    fnames = os.walk(imagedir)

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

        
    return cnt
    
#
# Function to get case sensitive file path (used for name folding issues)
#
def actualPath(fp):
    if debugMode():
        print("actualPath",fp)

    fdir = os.path.dirname(fp)
    fbase = os.path.basename(fp)
        
    if os.path.exists(fp):
        # the file exists, check for case match
        # by reading the actual filenames from the directory
        dlist = os.listdir(fdir)
        for f in dlist:
            # all OK, we have a match
            if f == fbase:
                return fp
            # check for case mismatch
            if f.upper() == fbase.upper():
                # return the correct case
                return fdir+"/"+f
        
    else:
        # return a missing file
        return missing_image_path
        
#
# Function to log text to a file.
#
def logText(s):
    global logfp

    logfile = "manifest2dita.log"

    if logfp==None:
        omode = "w"
    else:
        omode = "a"
    
    logfp = open(logfile,omode)

    logfp.write(s)
    logfp.write("\n")

    logfp.close()

    logfp = 1

#
# Function to get index of a SubElement
#
def getIndex(e,sub):
    if debugMode():
        print("getIndex",e.tag,sub)

    # all children of an element
    kids = list(e)
    ind = 1
    for kid in kids:
        # check for right subelement
        if kid.tag == sub:
            return ind
        ind = ind+1
        
    print("Error, getIndex did not find",sub,"in",e.tag)
    return None
    
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
    # delete any subdirectories
    dirs = os.walk(d)
    for dd in dirs:
        for ddir in dd[1]:
            EmptyDir(dd[0]+os.sep+ddir)
            os.rmdir(dd[0]+os.sep+ddir)

    if debugMode():
        print("all files deleted from",d)
                 
#
# Function to make a display format date for titles.
#
def titleDate(crd):
    if debugMode():
        print("titleDate",crd)

    pmonth = ["January","February","March","April","May"]
    pmonth2 = ["June","July","August","September","October","November","December"]
    pmonth = pmonth+pmonth2

    yr = crd[:4]
    mon = int(crd[4:6])
    day = crd[6:8]
    
    return pmonth[mon-1]+" "+day+", "+yr

#
# Function to create dictionary mapping child elements to parents
# since we need a parent to use remove().
#
def parentMap(tree):
    return dict((c, p) for p in tree.getiterator() for c in p)

#
# Function to create the path to an image
#
def imagePath(ifname):
    if debugMode():
        print("imagePath",ifname)

    ibase = os.path.basename(ifname)
    
    return "../images/"+ibase

    
#
# Function to update a reference to another DITA topic
#
def updateHref(h):
    global nodetypeD
    global link2idD
    if debugMode():
      print("updateHref",h)

    hret = None
    
    if h.find("/?q=node/") == 0:
        # get the node id
        id = h[9:]
        ntype = nodetypeD[id]
        hret = "../"+ntype+"/"+ntype+"_"+id+".dita"
        
    elif h in link2idD:
        id = link2idD[h]
        ntype = nodetypeD[id]
        hret = "../"+ntype+"/"+ntype+"_"+id+".dita"
 
    if hret == None:
        if debugMode():
          webErrorLog("updateHref failed for",h)
            
    return hret

#
# Function to make element text bold
#
def makeBold(e):
    if debugMode():
        print("makeBold",e.tag)

    b = Element("b")
    etext = e.text
    e.text = None
    b.text = etext
    e.insert(0,b)

    return

#
# Function to convert an html document to DITA.
# We can only handle a simple subset of all html.
#
def html2dita(e,dfile,id):
    if debugMode():
        print("html2dita",e.tag,dfile,id)
        print(" input element:",tostring(e))
    
    ret = e
    pmap = parentMap(e)

    #
    # First pass: make all simple tag substitutions
    #
    
    # a becomes xref or lines+filepath
    
    xrfs = e.iter("a")
    for xrf in xrfs:
        xrf.tag = "xref"
        href = xrf.get("href")
        if "target" in xrf.attrib:
            # remove any target attributes
            del xrf.attrib['target']
        if "title" in xrf.attrib:
            # remove any title attributes
            del xrf.attrib['title']
        # modify references to files
        if not href==None:
          if href.find("/wp-content/")>-1:
            hrefbase = os.path.basename(href)
            hreftext = xrf.text
            xrf.clear()
            xrf.tag="lines"
            xrf.text = hreftext
            xrfp = SubElement(xrf,"filepath")
            xrfp.text = "["+hrefbase+"] "
          else:
            hrefnew = updateHref(xrf.get("href"))
            if hrefnew == None:
                xrf.set("href",dfile+"#"+id)
            else: 
                xrf.set("href", hrefnew)
        else:
            # dummy out xref with no href
            xrf.tag = "p"

                      
                   
    # h4 becomes p
    for h4 in e.iter("h4"):
        h4.tag = "p"

    # em becomes b
    for em in e.iter("em"):
        em.tag = "b"

    # strong becomes b
    for em in e.iter("strong"):
        em.tag = "b"

    # blockquote becomes p
    for bq in e.iter("blockquote"):
        bq.tag = "p"
        
    # img becomes image
    for img in e.iter("img"):
        src = img.get("src")
        alt = img.text
        img.clear()
        img.set("href",imagePath(src))
        img.tag = "image"
        ealt = SubElement(img,"alt")
        ealt.text = alt

    # table becomes simpletable
    #  tr becomes strow
    #  td becomes stentry
    for tab in e.iter("table"):
        tab.tag = "simpletable"
    for tr in e.iter("tr"):
        tr.tag = "strow"
    for td in e.iter("td"):
        td.tag = "stentry"

    # get rid of content and itemprop attributes
    for et in e.iter():
        if "itemprop" in et.attrib:
            del et.attrib["itemprop"]
        if "content" in et.attrib:
            del et.attrib["content"]

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
    
    for ee in elist:
        if ee.tag=="h2":
            # h2 starts a new section with a title
            section = Element("section")
            sectionp = section
            stitle = SubElement(section,"title")
            stitle.text = ee.text
            nsect = nsect+1
            section.set("id",sectid+"_"+str(nsect))
            slist.append(section)
        elif ee.tag=="h3":
            # h3 starts a sectiondiv within the current section
            sectiondiv = ee
            ee.tag = "sectiondiv"
            # fake up a title line, since sectiondiv does not allow a title subelement
            sectiondivp = SubElement(sectiondiv,"p")
            sectiondivpb = SubElement(sectiondivp,"b")
            sectiondivpb.text = ee.text
            sectionp = sectiondiv
            nsect = nsect+1
            sectiondiv.set("id",sectid+"_div_"+str(nsect))
        else:
            # add everything else to the current section
            sectionp.append(ee)
            
        
    
    return slist

#
# Function to filter the input text
#
def filterText(t):

    # here you can edit the node text as a string
    ft = t
    
    return ft

#
# Function to create a DITA file from a node
#
def makeDITA(ts,ctp,node,idir):
    global node_data

    # maximum images per row
    maxrow = 3
    
    if debugMode():
        print("makeDITA",ctp,node.get("id"),node.text)
  
    
    # initialize the DITA XML
    root = fromstring(ts)
    tree = ElementTree()
    tree._setroot(root)
            
    node_text = node.text
    node_id = node.get("id")
    node_author = node.get("user")
    node_created = node.get("created")
    node_textp = node.get("path")
    
    # read in the node body text file
    fp = open(node_textp,"r")
    node_text = fp.read()
    fp.close()

    # set output id and file path
    ditaid = ctp+"_"+node_id
    ditafile = ditaid+".dita"

    if sorttype == SCHRON:
     node_data[node_id] = [ctp,node_created,ditafile,"?"]
    else:
     title_key = node.text.upper()
     title_key = title_key.strip()
     title_key = title_key.replace('\n','')
     while '  ' in title_key:
         title_key = title_key.replace('  ',' ')
     node_data[node_id] = [ctp,title_key,node_created,ditafile,"?"]
     
    title_date = titleDate(node_created)

    # get all the image elements for the node
    images = node.find("images")
    imagelist = iter(images)

    top_images = []
    bot_images = []
    
    # build the image lists
    for image in imagelist:
        top_images.append(image)
       
    # common for all content types
    root.set("id",ditaid)
    titlee = root.find("title")
    # title
    if develMode():
      title_date=title_date+" "+ditafile
    if longtitle:
      titlee.text = node.text+" - "+title_date+", by "+node_author
    else:
        titlee.text = node.text

    # find the body
    conbody = root.find("conbody")

    # tags
    keywords = root.find("prolog/metadata/keywords")
    tags = node.find("tags")
    tlist = iter(tags)
    for t in tlist:
        indt = SubElement(keywords,"indexterm")
        indt.text = t.text

    # create a section for the top images
    if len(top_images)>0:
        section = SubElement(conbody,"section")
        section.set("id","images_top")
        sectp = SubElement(section,"p")
        ni = 0
        for imge in top_images:
          imagefn = idir+'/'+imge.get("filename")
          imagefn = imagefn.replace("\\","/")
          img = SubElement(sectp,"image")
          img.set("href",imagePath(imagefn))
          if not imge.text==None:
            img.set("alt",imge.text)
          ni=ni+1
          if ni>=maxrow:
              sectp = SubElement(section,"p")
              ni=0
              
        
    # create a section for the text
    
    # get filtered node text
    filtered = filterText(node_text)
        
    # write out text in case we bomb out trying to parse it
    fpp = open("debug.xml","w")
    fpp.write(filtered)
    fpp.close()
        
        
    # make sure text is valid XML
    try:
        section = XML(filtered)
        # make the root be a section
        section.tag = "section"
        section.set("id","node_text")
        if debugMode():
            print("filtered section:")
            print(tostring(section))
                
            
    except:
        webErrorLog("Invalid node text in:",ctp,node.get("id"),node.text)
        logText("Invalid node text")
        logText(" node id: "+node.get("id"))
        logText(" node_text:")
        logText(node_text)
        logText(" filtered text:")
        logText(filtered)
        logText(" ")
            
        section = SubElement(conbody,"section")
        sectp = SubElement(section,"p")
        sectp.text = "** invalid XML **"

    dita_sections = html2dita(section,ditafile,ditaid)
            
    # add the text as sections
    for dita_section in dita_sections:
        if debugMode():
          print("dita_section:",tostring(dita_section))
        conbody.append(dita_section)
                 
    # create a section for the bottom images
    if len(bot_images)>0:
        section = SubElement(conbody,"section")
        section.set("id","images_bottom")
        sectp = SubElement(section,"p")
        ni=0
        for imge in bot_images:
          imagefn = idir+'/'+imge.get("filename")
          imagefn = imagefn.replace("\\","/")
          img = SubElement(sectp,"image")
          img.set("href",imagePath(imagefn))
          if not imge.text==None:
             img.set("alt",imge.text)
          ni=ni+1
          if ni>=maxrow:
              sectp = SubElement(section,"p")
              ni=0

    # patch things up for image href values
    imgs = root.findall("*//image")
    for img in imgs:
        ipath = img.get("href")
        ipath_base = os.path.basename(ipath)
        ipath_dir  = os.path.dirname(ipath)
        ipath_full = imagedir+"/"+ipath_base
        
        apath_full = actualPath(ipath_full)
        apath_base = os.path.basename(apath_full)
        
        if not os.path.exists(ipath_full):
            webErrorLog(ditafile)
            webErrorLog("missing image",ipath_full)
            img.set("href",os.path.dirname(ipath)+"/"+os.path.basename(missing_image))
        else:
            img.set("href",os.path.dirname(ipath)+"/"+apath_base)
        
    try:
        # return the DITA topic as a string
        retstr = tostring(root)
    except:
        webErrorLog("Oh oh!, the DITA file is not XML")
        dump(root)
        exit(0)
        
    return retstr
        
###################################
# PROCESSING INITIALIZATION SECTION
###################################

# set debugging controls
setdebug(False)
setdevel(False)
testmode = False

#
# signon
#
print("manifest2ditawp utility begins")
print()

# initial setup of the output directory
# set output directory
outdir = "manifest.dita"
print("empty output directory",outdir)
EmptyDir(outdir)

# create a directory for the images
imagedir = outdir+"/"+"images"
imagedir_rel = "..\\images"

# set the XML manifest input file created by deconstructwp.py
input_file = "manifestwp.xml"

# set the DITA template files
template = "templates/template.dita"
template_map = "templates/template_pdf.ditamap"
templatew_map = "templates/template_web.ditamap"
template_dir_map = "templates/template_dir.ditamap"
splash_page = "common/processing_files/splash_pages/splashpage_newsfromnanarchive.dita"

total_nodes = 0
image_count = 0

node_data = {}

###################################
#
# MAIN PROCESSING SECTION
#
###################################

# build a tree from the manifest XML
intree = ElementTree()
intree.parse(input_file)

# get the root element
root = intree.getroot()
if debugMode():
    print("XML root:",root.tag)
indir = root.get("dir")

# determine CMS
incmse = root.find("CMS")
if not incmse == None:
    cms = incmse.text
else:
    cms = DRUPAL

# display parameters
print("settings:")
print("input file:",input_file)
print("CMS:",cms)
inimages = root.get("images")
print("  input images:",inimages)
print("  output images",imagedir)
print("  topic template file:",template)
print("  web splash page file:",splash_page)
print("  bookmap template file:",template_map)
print("  web map template file:",templatew_map)
print("  content type template file:",template_dir_map)
print()

# create dictionaries of node info
nodetypeD = {}
link2idD = {}

# get the list of content types
ctypes = root.findall("ctype")

# loop thru the category nodes and build dictionaries
for ctype in ctypes:
    nodes = ctype.findall("node")
    for node in nodes:
        # get node values
        id = node.get("id")
        nlink = node.get("link")
        lpos = nlink.rfind("/")
        nlinkbase = nlink[lpos+1:]
        link2idD["?q="+nlinkbase] = id
        link2idD[nlinkbase] = id
        nodetypeD[id] = ctype.get("type")

# copy the web splash page
splash_out=shutil.copy(splash_page,outdir)
# make a copy of all the images
print("copy",inimages,"to",imagedir)
shutil.copytree(inimages,imagedir)

# add the missing image
missing_image_path = imagedir+"/"+os.path.basename(missing_image)
shutil.copyfile(missing_image,missing_image_path)
# add the splash page image
shutil.copy(splash_page_image,imagedir)

# resize the images to a maximum width
print("resizing the images")
cnt = resizeImages(imagedir)
print(cnt,"images resized")
              
# read in the template DITA file (a concept)
fp = open(template,"r")
tstring = fp.read()
fp.close()
# save doctype
p = tstring.find("<concept")
doctype = tstring[0:p]

# get the list of content types
ctypes = root.findall("ctype")

typedirs = {}
# process each content type
for ctype in ctypes:
    ctp = ctype.get("type")
    print()
    print("processing category",ctp)
    cdir = ctype.get("dir")
    # all the nodes of this content type
    nodes = ctype.findall("node")
    lnodes = len(nodes)
    if lnodes==0:
        continue
    print("  content type nodes =",lnodes)
    print("  input directory",cdir)
    ctypeout = outdir+os.sep+ctp
    print("  output directory",ctypeout)
    os.mkdir(ctypeout)
    typedirs[ctp] = ctypeout
        
    # loop through all the nodes of this type
    
    nnode = 0
    for node in nodes:
        
        # development hack to select only a small subset of nodes
        if testmode and nnode>6:
            break
        
        nnode = nnode+1
        nid = node.get("id")
        # create the node DITA topic
        makedita = makeDITA(tstring,ctp,node,imagedir_rel)
        # append the doctype to the XML for the node
        dita_file = doctype+makedita.decode()
        outpath = ctypeout+os.sep+node_data[nid][NFNFT]
        outpathr = ctp+os.sep+node_data[nid][NFNFT]
        node_data[nid][NFPATH] = outpathr
        
        # write the DITA source file out
        print("  writing",outpath)
        fp = open(outpath,"w")
        fp.write(dita_file)
        fp.close()
                                
    print()

# all topics have been created, now create a map
# for each content type and a master map for everything.

node_array = []
for tid in node_data:
    node_array.append(node_data[tid])
    
# make a list of topics in type and creation or title order
if sorttype == SCHRON:
    node_array.sort(reverse=True)
else:
    node_array.sort()

# read in the book template ditamap file
fp = open(template_map,"r")
mapstring = fp.read()
fp.close()
# save the book doctype
p = mapstring.find("<bookmap")
bookdoctype = mapstring[0:p]
# initialize the book map DITA XML
bookroot = fromstring(mapstring)

# read in the web template ditamap file
fp = open(templatew_map,"r")
mapstringw = fp.read()
fp.close()
# save the web doctype
pw = mapstringw.find("<map")
mapdoctype = mapstringw[0:pw]
# initialize the web map DITA XML
maproot = fromstring(mapstringw)

# locate the frontmatter in the PDF map
ipoint = getIndex(bookroot,"frontmatter")
# set the start of the web map
ipointw = 1

# update the web map with a splash page
mapwe = Element("topicref")
mapwe.set("href",os.path.basename(splash_out))
mapwe.set("format","dita")
maproot.insert(ipointw,mapwe)
ipointw = ipointw+1

# write out the maps for each content type
for ctype in ctypes:
  ctp = ctype.get("type")
  # read in the directory template ditamap file
  fp = open(template_dir_map,"r")
  dirmapstring = fp.read()
  fp.close()
  # save the doctype
  p = dirmapstring.find("<map")
  dirdoctype = dirmapstring[0:p]
  
  # initialize the content type map
  dirroot = fromstring(dirmapstring)
  dirroot.set("id",ctp+"_id")
  dirroot.set("title",ctp+" pages")

  # create a container topic for the content type
  container = fromstring(tstring)
  container.set("id",ctp+"_container_topic")
  title = container.find("title")
  dctp = ctp
  dctp = dctp.replace("_"," ")
  title.text = dctp.capitalize()+" topics"
  conbody = container.find("conbody")

  # put the container topic in the content type map
  contref = SubElement(dirroot,"topicref")
  fnft = ctp+"_container.dita"
  contref.set("href",fnft)
  
  # loop through the ordered array of topics of this type
  tyear = None
  ntop = 0
  for topic in [l for l in node_array if l[NTYPE]==ctp]:
    ntop=ntop+1
    tp = topic[NTYPE]
    cr = topic[NCREATE]
    cryr = cr[0:4]
    fnft = topic[NFNFT]
    fpath = topic[NFPATH]

    # create a topicref for this year, if required
    if (tyear==None) or (not tyear==cryr):
        if not tyear==None:
            # write out the previous year map
            yfnft = "year_"+tyear+".ditamap"
            outypath = typedirs[ctp]+"/"+yfnft
            fp = open(outypath,"w")
            if debugMode():
                print("writing",outypath)
            outstry = mapdoctype+tostring(yrroot).decode()
            fp.write(outstry)
            fp.close()
            # write out the container for the year
            outypath = typedirs[ctp]+"/"+ycontfnft
            fp = open(outypath,"w")
            if debugMode():
                print("  writing",outypath)
            outstry = doctype+tostring(ycontainer).decode()
            fp.write(outstry)
            fp.close() 
               
        tyear = cryr
        
        # initialize the year submap DITA XML
        yrroot = fromstring(dirmapstring)
        yrroot.set("id",ctp+"_year_"+tyear+"_id")
        yrroot.set("title",tyear)
        # put the year map in the content type map
        yfnft = "year_"+tyear+".ditamap"
        ysubmap = SubElement(contref,"topicref")
        ysubmap.set("href",yfnft)
        ysubmap.set("navtitle",tyear)
        ysubmap.set("toc","yes")
        ysubmap.set("format","ditamap")
        # create a container topic for the year map
        ycontainer = fromstring(tstring)
        ycontainer.set("id","year_"+tyear+"_container_topic")
        ytitle = ycontainer.find("title")
        ytitle.text = tyear
        yconbody = ycontainer.find("conbody")
        ycontsection = SubElement(yconbody,"section")
        ycontp = SubElement(ycontsection,"p")
        ycontp.text = tyear
        ycontsl = SubElement(ycontp,"sl")
        ycontsl.set("otherprops","pdf")
        # add the container to the year map
        ycontfnft = "year_"+tyear+"_container.dita"
        yconte = SubElement(yrroot,"topicref")
        yconte.set("href",ycontfnft)
        
        
    # add this topic to the year map below the container
    topicref = SubElement(yconte,"topicref")
    topicref.set("href",fnft)
    topicref.set("toc","no")
    # add this topic to the year container topic
    ycontsli = SubElement(ycontsl,"sli")
    ycontxref = SubElement(ycontsli,"xref")
    ycontxref.set("href",fnft)
    

  # write out the container topic
  if ntop>0:
    fnft = ctp+"_container.dita"
    outcpath = typedirs[ctp]+"/"+fnft
    fp = open(outcpath,"w")
    if debugMode():
      print("  writing",outcpath)
    outstr = doctype+tostring(container).decode()
    fp.write(outstr)
    fp.close()

    # write out the last year map
    yfnft = "year_"+tyear+".ditamap"
    outypath = typedirs[ctp]+"/"+yfnft
    fp = open(outypath,"w")
    if debugMode():
      print("writing",outypath)
    outstry = mapdoctype+tostring(yrroot).decode()
    fp.write(outstry)
    fp.close()
    # write out the container for the year
    outypath = typedirs[ctp]+"/"+ycontfnft
    fp = open(outypath,"w")
    if debugMode():
      print("writing",outypath)
    outstry = doctype+tostring(ycontainer).decode()
    fp.write(outstry)
    fp.close() 
            
    # write out content type map
    outstr = dirdoctype+tostring(dirroot).decode()
    outmappath = typedirs[ctp]+"/"+ctp+".ditamap"
    fp = open(outmappath,"w")
    if debugMode():
      print("writing",outmappath)

    # update the book map
    mape = Element("chapter")
    mape.set("href",ctp+"/"+ctp+".ditamap")
    mape.set("format","ditamap")
    bookroot.insert(ipoint,mape)
    ipoint=ipoint+1

    # update the web map
    mapwe = Element("topicref")
    mapwe.set("href",ctp+"/"+ctp+".ditamap")
    mapwe.set("format","ditamap")
    maproot.insert(ipointw,mapwe)
    ipointw = ipointw+1
  
    fp.write(outstr)
    fp.close()

print()
# write out the book map
outstr = bookdoctype+tostring(bookroot).decode()
outmappath = outdir+os.sep+"WParchive_pdf.ditamap"
fp = open(outmappath,"w")
print("writing",outmappath)
fp.write(outstr)
fp.close()

# write out the web map
outstr = mapdoctype+tostring(maproot).decode()
outmappath = outdir+os.sep+"NewsFromNan_web.ditamap"
fp = open(outmappath,"w")
print("writing",outmappath)
fp.write(outstr)
fp.close()
print()
webErrorLogClose()

print("manifest2ditawp utility ends")






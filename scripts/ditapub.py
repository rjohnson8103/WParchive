###################################
# PROLOG SECTION
# ditapub.py
#
# Common Python functions used in bulk Web CMS publishing.
# Functions defined here are mostly not dependent on a particular
# Web CMS.
#
# Tested with Python 3.2.2
# April 24, 2016
#
# Author: Dick Johnson
#
###################################

###################################
# ENVIRONMENT SETUP SECTION
###################################

# import needed modules
from xml.etree.ElementTree import *
import os
import io
import sys
import xmlrpc.client
import time
from datetime import date
import re

# global variables for this script
dbgflag = True
rpcerr = 0
tag_list = []
tp_str = type("string")

# global get/set variables
x_toc_dir = ""
x_toc_dir_abs = ""
x_toc_file = ""
x_cms_name = ""
x_cms_base_url = ""
x_cms_url = ""
x_user = ""
x_password = ""
x_blogid = ""
x_proxy = ""
x_vocabulary = ""
x_extensions = False
x_maxretry = 5
x_retrysleep = 10
x_sourcetype = "DITAXHTML"
x_outline = False
x_tagflag = False
x_linkflag = True
x_aliasbase = ""
x_tocpublish = True
x_dirscan = False

###################################
# FUNCTION DEFINITION SECTION
###################################

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
# Function to return the dbgflag value (controls debugging output)
# True means to print debugging output.
#
def debugMode():
    return dbgflag

#
# get/set functions for get/set variables
#
def set_toc_dir(td):
    global x_toc_dir
    x_toc_dir=td
def get_toc_dir():
    return x_toc_dir
def set_toc_file(tf):
    global x_toc_file
    x_toc_file=tf
def get_toc_file():
    return x_toc_file
def set_cms(c):
    global x_cms_name
    valid_cms=("WordPress","Drupal")
    if c in valid_cms:
        x_cms_name = c
    else:
        print("Error!",c," is not in",valid_cms)
        exit(0)
def get_cms():
    return x_cms_name
def set_cms_url(uu):
    global x_cms_url
    x_cms_url = uu
def get_cms_url():
    return x_cms_url
def set_base_url(b):
    global x_cms_base_url
    x_cms_base_url = b
def get_base_url():
    return x_cms_base_url
def set_user(c):
    global x_user
    x_user = c
def get_user():
    return x_user
def set_password(c):
    global x_password
    x_password = c
def get_password():
    return x_password
def set_proxy(p):
    global x_proxy
    x_proxy = p
def get_proxy():
    return x_proxy
def set_blogid(c):
    global x_blogid
    x_blogid = c
def get_blogid():
    return x_blogid
def set_vocabulary(c):
    global x_vocabulary
    x_vocabulary = c
def get_vocabulary():
    return x_vocabulary
def get_rpcerr():
    return rpcerr
def add_tag(t):
    if not t in tag_list:
        tag_list.append(t)
def get_tag_list():
    return tag_list
def set_extensions(e):
    global x_extensions
    x_extensions = e
def get_extensions():
    return x_extensions
def get_maxretry():
    return x_maxretry
def set_maxretry(n):
    global x_maxretry
    x_maxretry=n
def get_retrysleep():
    return x_retrysleep
def set_retrysleep(n):
    global x_retrysleep
    x_retrysleep=n
def set_sourcetype(t):
    global x_sourcetype
    x_sourcetype = t
def get_sourcetype():
    return x_sourcetype
def set_outline(t):
    global x_outline
    x_outline = t
def get_outline():
    return x_outline
def set_tagflag(t):
    global x_tagflag
    x_tagflag = t
def get_tagflag():
    return x_tagflag
def set_linkflag(t):
    global x_linkflag
    x_linkflag = t
def get_linkflag():
    return x_linkflag
def set_aliasbase(t):
    global x_aliasbase
    x_aliasbase = t
def get_aliasbase():
    return x_aliasbase
def set_tocpublish(t):
    global x_tocpublish
    x_tocpublish = t
def get_tocpublish():
    return x_tocpublish
def set_dirscan(t):
    global x_dirscan
    x_dirscan = t
def get_dirscan():
    return x_dirscan

#
# Function to return the input/output paths to be used, and the test flag
#
def GetInputs():
    # default to None
    source_spec = None
    output_spec = None
    test_flag = None

    # scan the command line arguments
    for i in range(len(sys.argv)):
       if i==1:
            source_spec=sys.argv[i]
       elif i==2:
            output_spec=sys.argv[i]
       elif i==3:
            test_flag=sys.argv[i]
            
    return source_spec, output_spec, test_flag
    
#
# Function to test for the existence of a remote method.
#
def testMethod(m):
    if debugMode():
        print("testMethod",m)

    prox = get_proxy()

    # get a list of all methods the server provides
    ret = prox.system.listMethods()

    if m in ret:
        return True
    else:
        return False
    
#
# Function to return the absolute page URL for a page id
#
def pageURL(id):
    if get_cms()=="WordPress":
        return get_base_url()+"?page_id="+id
    else:
        # assume Drupal format
        return get_base_url()+"?q=node/"+id
    
#
# Function to update any internal links to other pages
# referenced in a page
#
def updateLinks(pages,p,ptext):
    ppath = p['href']
    pdir = os.path.dirname(ppath)
    if debugMode():
        print("updateLinks",p["id"],ppath,len(ptext),ptext[0:10])

    nlinks = 0
    # make the page text string an element
    root = XML(ptext)
    if debugMode():
        print("root tag:",root.tag)
    # get the list of links in this page
    links = root.iterfind("*//a")

    linkerror = 0
    badlinks = []
    # loop through the links and fix the href pointers
    for link in links:
        nlinks = nlinks+1
        phref = link.get("href")
        if phref!=None:
            phref = phref.strip()
        if phref!=None and isURL(phref)==False and phref[0]!="#":
            if debugMode():
                print("  link",phref)
            # find the matching page for the link
            found = False
            for pp in pages:
                hrefpath = pp['href']
                if hrefpath!=None:
                    hrefpath = hrefpath.strip()
                if sameFile(ppath, phref, hrefpath,False):
                    # we found it, change the reference to a URL,
                    # and we didn't do name folding
                    found = True
                    link.set("href",pageURL(pp['id']))
                    if debugMode():
                        print("link href:",link.get("href"))
                    pass
                elif sameFile(ppath, phref, hrefpath,True):
                    # we found it by doing name folding
                    found = True
                    link.set("href",pageURL(pp['id']))
                    print(" *name folded link",phref,"found for",ppath)
                    if debugMode():
                        print("link href:",link.get("href"))
                    pass
                

            if not found:
                # href not resolved, delete it
                badlinks.append(phref)
                if debugMode():
                  print("Error, link",phref,"not found for",ppath)
                linkerror = linkerror + 1
                del link.attrib["href"]
                
    
    bodystr = tostring(root)
    if not isinstance(bodystr,tp_str):
        bodystr = bodystr.decode()
    
    if debugMode():
        print("there are",nlinks,"links")

    if linkerror>0:
        print("*there were",linkerror,"link errors out of",nlinks,"links for",ppath)
        for l in badlinks:
            print("  link target not found:",l)
    
        
    # return the updated file as a text string
    return bodystr

#
# Function to add a term to a vocabulary
# that exists on the site (Drupal only).
#
def addVocabularyTerm(vocab,term):
    if debugMode():
        print("getVocabularyTerm",vocab,term)
    
    if not get_extensions():
        return
    
    prox = get_proxy()

    sendf=False
    for i in range(get_maxretry()):
        try:
            ret = prox.bulkpub.addVocabularyTerm(get_user(), get_password(),vocab,term)
            sendf=True
            break;
        except:
            errCnt()
            ret="addVocabularyTerm error"
            print("addVocabularyTerm error",i+1)
            time.sleep(get_retrysleep())

    # if all the calls failed, generate an error message
    if not sendf:
        ret = prox.bulkpub.addVocabularyTerm(get_user(), get_password(),vocab,term)
        
    if debugMode():
        print(ret)

#
# Function to test if a file path is html
#
def isHTML(f):

    s = os.path.split(f)
    ftail = s[1]
    if ".HTM" in ftail.upper():
        return True
    else:
        return False
    
#
# Function to test if a "file path" is actually a URL
#
def isURL(f):

    # if there is no file, reject it also
    if f==None:
        return True

    # test for a URL in various ways
    if f.find("http:")>=0:
        return True
    elif f.find("https:")>=0:
        return True
    elif f.find("news:")>=0:
        return True
    elif f.find("mailto:")>=0:
        return True
    else:
        # it appears to be a file, and not a URL
        return False

#
# Function to check for a match on link paths
#
def sameFile(basepath0, xlinkpath0, hrefpath0, flag):
     

    # peel off any id in the link
    p = xlinkpath0.find("#")
    if p>-1:
        linkpath0 = xlinkpath0[0:p]
    else:
        linkpath0 = xlinkpath0
        
    if linkpath0 == hrefpath0:
        return True

    toc_dir = get_toc_dir()
    toc_dir_abs = os.path.abspath(toc_dir)
    
    # compare the absolute paths of the two files
    baseabs = os.path.abspath(toc_dir+os.sep+basepath0)
    basedir = os.path.dirname(baseabs)
    link0 = basedir+os.sep+linkpath0
    
    linkabs = os.path.abspath(link0)
    hrefabs = os.path.normpath(toc_dir_abs+os.sep+hrefpath0)
            
    if linkabs == hrefabs:
        return True
    elif flag and (linkabs.upper() == hrefabs.upper()):
        return True
    else:
        return False
   
#
# Function to create the XML output file that can be used to
# publish or delete the pages as a unit later on.
#
def makeXML(f,pages,media,blogid):
    if debugMode():
        print("makeXML",f)

    # create the XML root
    root = Element("manifest")

    # base level information
    tree = ElementTree(root)
    url = SubElement(root,"url")
    url.text = get_cms_url()
    usr = SubElement(root,"user")
    usr.text = get_user()
    pw = SubElement(root,"password")
    pw.text = get_password()
    bid = SubElement(root,"type")
    bid.text = str(blogid)
    tocd = SubElement(root,"tocdir")
    tocd.text = get_toc_dir()
    tocf = SubElement(root,"tocfile")
    tocf.text = get_toc_file()
    cmse = SubElement(root,"cms")
    cmse.text = get_cms()
    vocabe = SubElement(root,"vocabulary")
    vocabe.text = get_vocabulary()
    stypee = SubElement(root,"source")
    stypee.text = get_sourcetype()
    oflage = SubElement(root,"outline")
    oflage.text = flagYN(get_outline())
    lflage = SubElement(root,"links")
    lflage.text = flagYN(get_linkflag())
    abasee = SubElement(root,"aliasbase")
    abasee.text = get_aliasbase()
    tflage = SubElement(root,"tags")
    tflage.text = flagYN(get_tagflag())
    stampe = SubElement(root,"timestamp")
    today = date.today()
    stampe.text = today.isoformat()
    ose = SubElement(root,"os")
    ose.text = os.environ["OS"]
    compe = SubElement(root,"computer")
    compe.text = os.environ["COMPUTERNAME"]
    unamee = SubElement(root,"computer_user")
    unamee.text = os.environ["USERNAME"]

    # page level information
    pgs = SubElement(root,"pages")
    for p in pages:
        # is the toc being published?
        if not get_tocpublish() and (p['parent']==None):
            continue
        pe = SubElement(pgs,"page")
        pe.text = p['id']
        pe.set("href",p['href'])
        pe.set("url",pageURL(p['id']))

    # media image information
    meds = SubElement(root,"media")
    for m in media:
        mdata = media[m]
        mede = SubElement(meds,"image")
        mede.text = os.path.relpath(m,os.path.abspath(get_toc_dir()))
        if "url" in mdata:
            murl = mdata['url']
        else:
            murl = "?"
        mede.set("url",murl)

    # vocabulary added information
    tags = SubElement(root,"tags")
    tags.set("vocabulary",get_vocabulary())
    tlist = get_tag_list()
    for t in tlist:
        tag = SubElement(tags,"term")
        tag.text = t
    
    # write the XML file
    print("Writing output XML file",f)
    tree.write(f)

#
# Function to get categories (WordPress only)
#
def getCategories():
    if debugMode():
        print("getCategories")
    proxy = get_proxy()
    ret=proxy.metaWeblog.getCategories(get_blogid(),get_user(),get_password())
    if debugMode():
        print(ret)
        
    return ret

#
# Function to delete and make a list of any parent
# topic links. Called for processing DITA OT input.
#
def removeParentTopicLinks(e, lst,n):

    if n==1:
        ss=""
    else:
        ss=" "*(n-1)
        
    if debugMode():
        print(ss,"removeParentTopicLinks",e.tag,n,lst)

    alle = e.getchildren()
    for ee in alle:
        rf=True
        if ee.tag=="div":
            cls = ee.get("class")
            if cls!=None and cls=="parentlink":
                if debugMode():
                    print(ss,"found parentlink",ee.tag,cls)
                lst.append(ee)
                e.remove(ee)
                rf=False
                
        if rf:
            removeParentTopicLinks(ee, lst, n+1)

#
# Function to finalize the content of a page
#
def finalizeContent(pstr):
    new_text = pstr
    # make sure it is a string
    if not isinstance(new_text,tp_str):
        new_text = new_text.decode()
    # strip out body tags
    i = new_text.find(">")
    new_text = new_text[i+1:]
    new_text = new_text.replace("</body>","")

    return new_text

#
# Function to count RPC errors
#
def errCnt():
    global rpcerr
    rpcerr=rpcerr+1
    return rpcerr

#
# Function to convert flag to Y or N
#
def flagYN(flag):
    if flag:
        return "Y"
    else:
        return "N"
    
#
# Function to create a URL relative to the remote site base
#
def baseURL(url):
    if debugMode():
        print("baseURL: <"+url+">")
    # calculate the relative base to the URL
    i = url.find('//')
    if i<0:
        print("error in baseURL, input URL is invalid <"+url+">")
        return url
    tmp = url[i+2:]
    j = tmp.find('/')
    baseurl = tmp[j:]
    if debugMode():
        print("baseURL for",url,"is",baseurl)
    return baseurl

#
# Function to find loose pages not in
# the index (toc) page of the xhtml.
#
def findLoosePages(pages,files,indir):
        
    if debugMode():
        print("findLoosePages:",indir)

    # get all the directory information
    entries = os.walk(indir)

    # look for files not already in the lists
    for entry in entries:
        if debugMode():
            print(entry)
        dir = entry[0]
        rdir = os.path.relpath(dir,indir)
        
        efiles = entry[2]
        for file in efiles:
            fpath = rdir+os.sep+file
            fpath = fpath.replace('\\','/')
            # look for an html file not in the toc
            if isHTML(fpath) and (not fpath in files):
              # create a pages and files entry for it
              print(" add file not in toc:",fpath)
              pe = {"node": None, "level":0,"parent":None,"in_index":False}
              pe["href"] = fpath
              pe["tag"] = None
              # read the title from the file
              ff = os.path.normpath(indir + os.sep + fpath)
              tree = ElementTree()
              try:
                  tree.parse(ff)
              except:
                  print("Error parsing",ff)
                  continue
              troot = tree.getroot()
              title = troot.find("head/title")
              if (not title==None) and (not title.text == None):
                  pe["title"] = title.text
              else:
                  pe["title"] = ""
              pages.append(pe)
              pageno = len(pages)-1
              # collect file data
              if not fpath in files:
                 fdata = {'pageno':pageno}
                 files[fpath] = fdata
                      
        
#
# Function to find subpages of a page by recursively scanning
# the index (toc) page of the xhtml.
#
def findSubpages(pages,files,ul,pn,level):
        
    if debugMode():
        print("findSubpages, page",pn,"level",level)

    subpages = []
    parent = pn
    page = pages[pn]
    
    litems = ul.findall("li")
    if debugMode():
        print("page",pn,"has",len(litems),"list items")

    for li in litems:
        kids = li.getchildren()
        for kid in kids:
            ktag = kid.tag
            # a reference to a single page
            if ktag=="a":
                hrefg = kid.get("href")
                # we only want the file being referenced
                hff = hrefg.find("#")
                if hff>-1:
                    href = hrefg[0:hff]
                else:
                    href = hrefg
                pg = {"linknode":kid,"level":level,"parent":pn,"title":fixTitle(kid.text),"tag":ktag,"href":href,"id":None}
                pg["in_index"] = True
                pages.append(pg)
                pageno = len(pages)-1
                # collect file data
                if not href in files:
                    fdata = {'pageno':pageno}
                    files[href] = fdata
                # this page is the current parent page
                parent = pageno
            # a subpage pointing at a list of pages   
            elif ktag=="ul":
                # find the pages at the next lowest level
                findSubpages(pages,files,kid,parent,level+1)
            
            else:
                if debugMode():
                    print("findSubPages, ignoring",ktag)
                
#
# Function to create the initial content string for a page
#
def makeContent(pages,media,p,tdir):
    pf=p['href']
    if debugMode():
        print("makeContent",pf)

    if pf==None:
        return False

    # strip off id references in path
    pp = pf.find("#")
    if pp>-1:
        f = pf[0:pp]
    else:
        f = pf
        
    # can we use extensions?
    extf = get_extensions()

    ff = os.path.normpath(tdir + os.sep + f)
    tree = ElementTree()
    tree.parse(ff)
                
    body = tree.find("body")

    if body==None:
        print("Error: no body in",f)
        return False

    # erase topic title line
    bh1 = body.find("h1")
    if bh1!=None:
        body.remove(bh1)
    
    # get a list of all the keywords in the file
    key_list = []
    head = tree.find("head")
    if head==None:
        print("Error: no head in",f)
        return False
    
    # init field info
    fieldlist = {}
    
    # make a list of all <meta> elements and then find
    # the keywords in DC.subject.
    metas = head.findall("meta")
    for meta in metas:
        mname = meta.get("name")
        
        if mname!=None and mname=="DC.subject":
            DCcontent = meta.get("content")
            if DCcontent!=None:
                content_tags = DCcontent.split(",")
                for ctag in content_tags:
                    ctag = ctag.strip()
                    if not ctag in key_list:
                        key_list.append(ctag)
                        # add tag to global tag list
                        if not ctag in get_tag_list():
                            add_tag(ctag)
                            # if we can, add this tag to the vocabulary
                            if extf and get_tagflag():
                                vcab = get_vocabulary()
                                addVocabularyTerm(vcab,ctag)
                                print(" add",vcab,"term",ctag)
                                
        # look for fields provided in the input
        # this is a local extension
        elif mname!=None and mname.startswith("FIELD."):
            fpos = mname.find(".")
            fieldname = mname[fpos+1:]
            fieldvalue = meta.get("content")
            if debugMode():
              print("field: ",fieldname,fieldvalue)
            fieldlist[fieldname] = fieldvalue
                
                            
    # store the tags (keywords)
    p['keywords'] = key_list

    if len(fieldlist)>0:
        p['fields'] = fieldlist
        
    if debugMode():
        print("key_list",key_list)
        print(get_tag_list())
        
    # get a list of parentlinks and remove them
    if get_sourcetype()=="DITAXHTML":
      plinks = []
      removeParentTopicLinks(body, plinks,1)
 
            
    # if not doing outline processing for DITA content,
    # move DITA parent links to top
    if not get_outline() and get_sourcetype()=="DITAXHTML":
      if len(plinks)>0:
          # move deleted parent links to the top
          for plink in plinks:
              body.insert(0,plink)
      elif get_cms()=="Drupal":
          # for Drupal, if there is no parent link, add one
          parent = p['parent']
          if parent!=None:
              pp = pages[parent]
              if debugMode():
                  print("add parent",parent,pp['title'])
              # manufacture a parent link
              ltext='<div class="parentlink"><strong> Parent topic: </strong><a href="'+pp['href']+'">'+pp['title']+'</a></div>'
              body.insert(0,XML(ltext))
              
    elif get_linkflag() and (get_sourcetype()=="DITAXHTML"):
        
        # also remove related task and concept links, previous and next topics
        divl = body.findall("div")
        for d in divl:
            c = d.get("class")
            if c!=None:
                if ("relinfo" in c) or ("familylinks" in c) or ("related-links" in c):
                    pmap = parentMap(tree)
                    pd = pmap[d]
                    pd.remove(d)
                    print(" removing div of class",c)

        # also remove olchildlink/ulchildlink <li> elements
        lil = body.findall("li")
        for l in lil:
            c = l.get("class")
            if c!=None:
                if ("olchildlink" in c) or ("ulchildlink" in c):
                    pmap = parentMap(tree)
                    pl = pmap[l]
                    pl.remove(l)
                    print(" removing li of class",c)
        
                
        # also remove all links from top TOC page
        if p['parent'] == None:
            flg = True
            while(flg):
                ule = body.find("ul")
                if ule!=None:
                    pmap = parentMap(tree)
                    pul = pmap[ule]
                    pul.remove(ule)
                else:
                    flg = False
                    
    elif get_outline():
        # when doing Drupal outline, delete TOC links from ditamaps
        parent_map = parentMap(tree)
        ullist = tree.find("body/div/ul")
        if ullist!=None:
            if ullist.get("class")=="ullinks":
                pnode = parent_map[ullist]
                pnode.remove(ullist)
                print(" remove page ullinks")
        
    # change the src attribute for any img elements to point to image URL
    images = body.iterfind("*//img")
    for img in images:
        src = img.get("src")
        if not isURL(src):
            if debugMode():
                print("src",src)
            # get the URL where Drupal has stored the image
            murl = getMediaURL(media,f,src)
            img.set("src",murl)

    # delete <a> elements that have no href. they cause formatting
    # problems when the CMS styles the page.
    alist = []
    remove_empty_anchors(body,1,alist)
       
    # turn the XML into a string
    bodystr = tostring(body)

    # save the edited page as a string
    if not isinstance(bodystr,tp_str):
        bodystr = bodystr.decode()
    p["content"] = bodystr

    return True

#
# Function to create dictionary mapping child elements to parents
# since we need a parent to use remove().
#
def parentMap(tree):
    return dict((c, p) for p in tree.getiterator() for c in p)
    
#
# Function to recursively remove any empty anchor elements
#
def remove_empty_anchors(e,n,lst):

    if n==1:
        ss=""
    else:
        ss=" "*(n-1)
        
    if debugMode():
        print(ss,"remove_empty_anchors from:",n,e.tag)

    kids = e.getchildren()
    if len(kids)==0:
        return
                
    for kid in kids:
        if kid.tag == "a":
            hr = kid.get("href")
            if hr==None:
                if debugMode():
                    print(ss,"  remove empty anchor element from",e.tag)
                    print(ss,"  ",tostring(kid).decode()[0:20])
                lst.append([n,e,kid])
        else:
            remove_empty_anchors(kid,n+1,lst)

    # all done traversing, do any necessary deletions
    if n==1:
        ll = len(lst)
        if ll>0:
            if debugMode():
                print(ll,"anchors to remove")
                for xxx in lst:
                    print(xxx[0],xxx[1].tag,xxx[2].tag)
            # sort the list by depth
            sflag = True
            if ll>1:
                while sflag:
                    sflag = False
                    for i in range(ll-1):
                        if lst[i][0]>lst[i+1][0]:
                            ltemp = lst[i]
                            lst[i]=lst[i+1]
                            lst[i+1]=ltemp
                            sflag=True
                        
                lst.reverse()
                
            # remove the deepest elements first
            for aa in lst:
                pp = aa[1] # parent element
                ee = aa[2] # element to be deleted
                nn = aa[0] # depth of element to be deleted
                if debugMode():
                    print(ss,"removing",pp.tag,ee.tag,nn)
                pp.remove(ee)
                
#
# Function to add to the list of referenced
# media (image) files.
#
def mediaList(media,files,f,tdir):
    if debugMode():
        print("mediaList",f,tdir)

    cnt=0 # count of media files found

    # parse the html file
    ff = os.path.normpath(tdir + os.sep + f)
    subtree = ElementTree()
    subtree.parse(ff)
    root = subtree.getroot()
    body = root.find("body")
    
    # get all the img elements
    imgs = body.iterfind("*//img")
                        
    # populate information for all the images
    for img in imgs:
        # compute the image normalized path
        spath=img.get("src")
        if not isURL(spath):
            npath = os.path.normpath(ff+os.sep+".."+os.sep+spath)
            npath = os.path.abspath(npath)
            if debugMode():
                print(" image:",npath)
            if not npath in media:
                # remember this media reference
                media[npath]={"alt":img.get("alt")}
                cnt=cnt+1
                if "media" in files[f]:
                    files[f]["media"].append(npath)
                else:
                    files[f]["media"]=[npath]
        else:
            print("skipping img",spath)

    if debugMode():
        print(cnt,"images found in",f)
        
    return cnt

#
# Function to return the URL for an image
#
def getMediaURL(media,f,src):
    if debugMode():
        print("getmediaURL",f,src)

    # compute the path to the media file
    fdir = os.path.dirname(get_toc_dir()+os.sep+f)
    fpath = os.path.normpath(fdir+os.sep+src)
    mpath = os.path.abspath(fpath)
    
    if debugMode():
        print("  mpath",mpath)
        
    # look up the file in the stored media dictionary
    if mpath in media:
        rc = baseURL(media[mpath]["url"])
        if debugMode():
            print("getMediaURL returns",rc)
        return rc

    # missing media file!
    print("getMediaURL did not find",f)
    rc = "?"

    return rc

#
# Function to make substitutions in title to eliminate characters that
# confuse the CMS.
#
def fixTitle(s):
    if debugMode():
        print("fixTitle",s)

    if s==None:
        ss=" "
    else:
        ss = s
    ss = ss.replace("<","&lt;")
    ss = ss.replace(">","&gt;")

    return ss

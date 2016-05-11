# WParchive
Python scripts that create a PDF archive of the content of a WordPress seb site

This project contains software that can be used to create a static PDF archive of a WordPress web site. Using the scripts provided, you can access the content of such a site after it has been taken down for some reason.

Producing a PDF archive is done in three stages:

1. The deconstructwp.py script is run to retrieve text and images from the live WordPress site using XML-RPC. The input parameters for this script are contained in the file options.xml found in the scripts directory. The output of the script is a directory containing the text of pages/posts from the site and a directory containing all the referenced images. Also produced is a file manifest.xml that serves as input for the 2nd script.
2. Next the manifest2ditawp.py script is run to read the output from the first script and output a set of DITA source files, one for each page or post from the site.
3. Finally, the DITA files can be transformed into an output format, such as PDF, HTML or epub using the DITA Open Toolkit or an equivalent tool.


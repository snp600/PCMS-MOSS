import mosspy

userid = 1

m = mosspy.Moss(userid, "python")

#m.addBaseFile("submissions/1.py")
#m.addBaseFile("submissions/2.py")

# Submission Files
m.addFile("submissions/1.py")
m.addFile("submissions/2.py")
#m.addFilesByWildcard("submissions/2.py")

url = m.send()

print ("Report Url: " + url)

m.saveWebPage(url, "submissions/report.html")
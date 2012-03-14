from zipfile import ZipFile, BadZipfile as BZ
#================================================
def read_zipfile(filepath):
    try:
        tmpfile = ZipFile(filepath, "r")
    except BZ:
        raise BadZipfile
    zipfile_contents = {}
    for info in tmpfile.infolist():
        zipfile_contents[info.filename] = (info.file_size, info.date_time)
    tmpfile.close()
    return zipfile_contents
#================================================
def read_file_in_zipfile(filepath, filename):
    try:
        tmpfile = ZipFile(filepath, "r")
    except BZ:
        raise BadZipfile
    try:
        fileinfo = tmpfile.getinfo(filename)
    except KeyError:
        return False
    if fileinfo.file_size == 0:
        return 0
    file_contents = None
    file_contents = tmpfile.read(filename)
    tmpfile.close()
    return file_contents
#================================================
def get_file_in_zipfile(filepath, filename, targetdir):
    try:
        tmpfile = ZipFile(filepath, "r")
    except BZ:
        raise BadZipfile
    try:
        fileinfo = tmpfile.getinfo(filename)
    except KeyError:
        return False
    if fileinfo.file_size == 0:
        return 0
    targetfile = tmpfile.extract(filename, targetdir)
    tmpfile.close()
    return targetfile
#================================================
path = 'silos/sandbox/pairtree_root/da/ta/se/t1/obj/__26/'
fp1 = path + 'test3.zip'
fp2 = path + 'read_test.zip'
fp3 = path + 'databank_logo.png'

zc1 = read_zipfile(fp1)
zc2 = read_zipfile(fp2)
zc3 = read_zipfile(fp3)

zc1_files = zc1.keys()
zc2_files = zc2.keys()

ans11 = read_file_in_zipfile(fp1, zc1_files[1])  #expected: 0
ans12 = read_file_in_zipfile(fp1, 'test')        #expected: False
ans13 = read_file_in_zipfile(fp1, zc1_files[0])  #expected: file conts

ans21 = read_file_in_zipfile(fp2, zc2_files[0])  #expected: file conts
ans22 = read_file_in_zipfile(fp2, zc2_files[1])  #expected: 0
ans23 = read_file_in_zipfile(fp2, zc2_files[4])  #expected: binary output

ans14 = get_file_in_zipfile(fp1, zc1_files[1], '/tmp') #expected: 0
ans15 = get_file_in_zipfile(fp1, 'test', '/tmp')        #expected: False
ans16 = get_file_in_zipfile(fp1, zc1_files[0], '/tmp')  #expected: '/tmp/admiral-dataset.txt'

ans24 = get_file_in_zipfile(fp2, zc2_files[0], '/tmp')  #expected: '/tmp/read_test/Dir/TestScanFiles32.txt'
ans25 = get_file_in_zipfile(fp2, zc2_files[1], '/tmp')  #expected: 0
ans26 = get_file_in_zipfile(fp2, zc2_files[4], '/tmp')  #expected: '/tmp/read_test/databank_logo.png'
#================================================
#Expected Answers
"""
>>> zc1
{'admiral-dataset.txt': (43, (2010, 11, 29, 16, 30, 52)), 'TestScanFilesSubDir/': (0, (2010, 11, 29, 17, 34, 42)), 'TestScanFilesSubDir/TestScanFiles31.txt': (9, (2010, 10, 4, 15, 39, 54)), 'TestScanFilesSubDir/TestScanFiles32.txt': (9, (2010, 10, 4, 15, 39, 54)), 'TestScanFilesSubDir/manifest.rdf': (511, (2010, 11, 29, 17, 42, 10))}

>>> zc2
{'read_test/Dir/TestScanFiles32.txt': (9, (2010, 10, 4, 15, 39, 54)), 'read_test/Dir/': (0, (2011, 1, 5, 13, 43, 30)), 'read_test/admiral-dataset.txt': (43, (2010, 11, 29, 16, 30, 52)), 'read_test/Dir/manifest.rdf': (511, (2010, 11, 29, 17, 42, 10)), 'read_test/databank_logo.png': (20220, (2010, 12, 6, 15, 11, 40)), 'read_test/': (0, (2011, 1, 5, 13, 44, 40)), 'read_test/Dir/TestScanFiles31.txt': (9, (2010, 10, 4, 15, 39, 54))}

>>> zc1_files
['admiral-dataset.txt', 'TestScanFilesSubDir/', 'TestScanFilesSubDir/TestScanFiles31.txt', 'TestScanFilesSubDir/TestScanFiles32.txt', 'TestScanFilesSubDir/manifest.rdf']

>>> zc2_files
['read_test/Dir/TestScanFiles32.txt', 'read_test/Dir/', 'read_test/admiral-dataset.txt', 'read_test/Dir/manifest.rdf', 'read_test/databank_logo.png', 'read_test/', 'read_test/Dir/TestScanFiles31.txt']

>>> ans11
0

>>> ans12
False

>>> ans13
'This directory contains an ADMIRAL dataset\n'

>>> ans21
'Test file'

>>> ans22
0

>>> ans23
'\x89PNG\.....

>>> ans14
0

>>> ans15
False

>>> ans16
'/tmp/admiral-dataset.txt'

>>> ans24
'/tmp/read_test/Dir/TestScanFiles32.txt'

>>> ans25
0

>>> ans26
'/tmp/read_test/databank_logo.png'
"""
#================================================

import os

def parsePath(path, section):
    '''note: 
    mkdir generate: path##id
    rmdir generate: path##id##tmp
    upload generate: filename##id
    rm generate: filename##id##tmp
    mv generate: filename##id##tmp filename##newid##tmp
    cp generate: filename##newid
    '''
    if section == 'R':
        currPath = '.'
        dirs = path.split('/')
        for directory in dirs:
            if directory == '.' or directory == '':
                continue
            else:
                splitDir =[(filename, filename.split('##')) for filename in os.listdir(currPath)]
                print 'directory for now: %s' % directory
                print 'dirs of %s' % currPath
                print splitDir
                pathToAdd = filter(lambda x: os.path.exists(os.path.join(currPath, x[0])) and (len(x[1]) == 1 or len(x[1]) == 2) and x[1][0] == directory, splitDir)
                print 'pathToAdd is:'
                print pathToAdd
                if len(pathToAdd) == 0:
                    return 'Path invalid'
                else:
                    currPath += ('/' + pathToAdd[0][0])
        return currPath
    
    elif section == 'M':
        currPath = '.'
        dirs = path.split('/')
        for i in range(len(dirs) + 1):
            res = currPath
            for j in range(len(dirs) - i):
                res += ('/' + dirs[j])
            for k in range(len(dirs) - i, len(dirs)):
                res += ('/' + dirs[k] + '##$')
            print 'res is %s now' % res
            if os.path.exists(res):
                return res
        return 'Path invalid'

        
def checkExist(path, fileToCheck):
    splitDir =[(filename, filename.split('##')) for filename in os.listdir(path)]
    checkList = filter(lambda x: len(x[1]) == 2 and x[1][0] == fileToCheck, splitDir)
    if len(checkList) > 0:
        return True
    else:
        return False
    
def checkDir(path):
    splitDir =[(filename, filename.split('##')) for filename in os.listdir(path)]
    checkList = filter(lambda x: len(x[1]) == 2, splitDir)
    if len(checkList) > 0:
        return True
    else:
        return False



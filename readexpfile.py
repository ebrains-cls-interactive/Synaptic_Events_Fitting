import readconffile
filename2=''
def getColumns(inFile, delim="\t", header=True):
    cols = {}
    indexToName = {}
    for lineNum, line in enumerate(inFile):
        if lineNum == 0:
            headings = line.split(delim)
            i = 0
            for heading in headings:
                heading = heading.strip()
                if header:
                    cols[heading] = []
                    indexToName[i] = heading
                else:
                    cols[i] = [heading]
                    indexToName[i] = i
                i += 1
        else:
            cells = line.split(delim)
            i = 0
            for cell in cells:
                cell = cell.strip()
                cols[indexToName[i]] += [cell]
                i += 1
    return cols, indexToName  

def readexpfile(num=0):
    [inputfilename,modfilename,parametersfilename,flagdata,flagcut,nrtraces,
    Vrestf,esynf,nrparamsfit,paramnr,paramname,paraminitval,
    paramsconstraints,nrdepnotfit,depnotfit,nrdepfit,depfit,seedinitvaluef]=readconffile.readconffile()
    times = []
    currents = []
    
    data=open(filename2,'r')
    cols, indexToName = getColumns(data,header=False)
    if (flagdata==0):
        vecc=cols[0]
        timevecprov = [] 
        for elem in vecc:
            if elem:
                timevecprov.append(float(elem))
        vecc2=cols[num]
        vecallprov = []
        for elem in vecc2:
            if elem:
                vecallprov.append(float(elem))
    else:
        vecc=cols[2*num]
        timevecprov = []
        for elem in vecc:
            if elem:
                timevecprov.append(float(elem))
        vecc2=cols[2*num+1]
        vecallprov = []
        for elem in vecc2:
            if elem:
                vecallprov.append(float(elem))
    return (timevecprov,vecallprov)  

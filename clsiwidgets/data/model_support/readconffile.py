filename=""
def readconffile():
    fh=open(filename,"r")
    fh.readline()#name of file containing raw traces
    inputfilename=fh.readline()
    fh.readline()#name of warning file
    modfilename=fh.readline()
    fh.readline()#name of parameters file
    parametersfilename=fh.readline()
    fh.readline()#flagdata==0 data with one time column for all currents; ==1 data with one time column for each current
    flagdata=int(fh.readline())
    fh.readline()#flagcut==0 data not cutted; ==1 data cutted below 20% of max
    flagcut=int(fh.readline())
    fh.readline()#number of traces
    nrtraces=int(fh.readline())
    fh.readline()#PROTOCOL
    fh.readline()#VCLAMP AMP
    Vrestf=int(fh.readline())
    fh.readline()#REVERSAL POTENTIAL
    esynf=float(fh.readline())
    fh.readline()#FITTING PARAMETERS AND INITIAL VALUES
    nrparamsfit=int(fh.readline())
    paramnr=[]
    paramname=[]
    paraminitval=[]
    for _ in range(nrparamsfit):
        line=fh.readline()
        par=line.split()
        x1=int(par[0])
        paramnr.append(x1)
        s=par[1]
        paramname.append(s)
        x2=float(par[2])
        paraminitval.append(x2)
    fh.readline()#CONSTRAINTS
    paramsconstraints=[]
    for _ in range(nrparamsfit):
        line=fh.readline()
        par=line.split()
        paramsconstraints.append([float(par[i]) for i in range(2)])
    fh.readline()#DEPENDENCY RULES FOR PARAMETERS NOT FITTED
    nrdepnotfit=int(fh.readline())
    depnotfit=[]
    for _ in range(nrdepnotfit):
        depnotfit.append(fh.readline())
    fh.readline()#EXCLUSION RULES 
    nrdepfit=int(fh.readline())
    depfit=[]
    for _ in range(nrdepfit):
        depfit.append(fh.readline())
    fh.readline()#seed
    seedinitvaluef=int(fh.readline())
    fh.close()
    return (inputfilename,modfilename,parametersfilename,flagdata,flagcut,nrtraces,Vrestf,esynf,nrparamsfit,paramnr,paramname,paraminitval,paramsconstraints,nrdepnotfit,depnotfit,nrdepfit,depfit,seedinitvaluef)

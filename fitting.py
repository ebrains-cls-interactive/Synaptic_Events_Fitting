import random
import csv
import math
from functools import partial
import time
import sys
import os
import glob
import shutil
import subprocess
#import matplotlib
#matplotlib.use('Agg')
#import matplotlib.pyplot as plt
import readconffile as rcf
import readexpfile as ref

global nefun
global seedinitvalue

def fitting(configuration_file, experimental_file, mod_file, all_traces, singletrace, demo, singletrace_number):  
    '''
        Accepts:
            configuration_file:
                type: text/plain
                description: text file, specifying parameters of the simulation.
            experimental_file:
                type: text/plain
                description: text file, specifying experimental traces.
            mod_file:
                type: video/mpeg
                description: mod file, specifying the model. 
            all_traces:
                type: bool
                description: If True, all traces are fitted 100 times [default=False].
            singletrace:
                type: bool
                description: If True, only one trace is fitted 100 times [default=False].
            demo:
                type: bool
                description: If True, one trace is fitted 10 times [default=False].
            singletrace_number:
                type: double
                description: number of the trace to be fitted [default=3].
        Returns:
            res: text/csv
    '''
    
    #subprocess.call(['nrnivmodl', ])
    
    import neuron
    start_time = time.time()

    singletrace_number = int(singletrace_number)
    rcf.filename=configuration_file
    ref.filename2=experimental_file

    [inputfilename,modfilename,parametersfilename,flagdata,flagcut,nrtraces,Vrestf,esynf,nrparamsfit,paramnr,paramname,paraminitval,paramsconstraints,nrdepnotfit,depnotfit,nrdepfit,depfit,seedinitvaluef]=rcf.readconffile()

    seedinitvalue = seedinitvaluef

    neuron.h.use_mcell_ran4(1)
    neuron.h.mcell_ran4_init(seedinitvalue)

    synapse_rng = neuron.h.Random()
    synapse_rng.MCellRan4(12345)
    synapse_rng.uniform(0, 1)

    trace_number = 0

    randnum = neuron.h.Random()
    randnum.MCellRan4(12345)

    vecparamforfit = fixed(nrparamsfit,paraminitval)

    listofvecs = []
    for fitnr in range(100):
        vecparamforfit = fixed(nrparamsfit,paraminitval)
        vecparamforfit2 = vecparamforfit
        for i in range(nrparamsfit):
            vecparamforfit2[i] = vecparamforfit[i]+randnum.uniform(-vecparamforfit[i], vecparamforfit[i])
        listofvecs.append(vecparamforfit2)

    import fitness
    fitness.filename3=mod_file
    if demo=='True':
        twoargs = [(num, fitnr) for num in range(singletrace_number, singletrace_number+1) for fitnr in range(5)]
    if all_traces=='True':
        twoargs = [(num, fitnr) for num in range(1,nrtraces+1) for fitnr in range(100)]
    if singletrace=='True':
        twoargs = [(num, fitnr) for num in range(singletrace_number, singletrace_number+1) for fitnr in range(20)] 
    pc = neuron.h.ParallelContext()
    pc.runworker()
    info = runsim(twoargs,pc,seedinitvalue,listofvecs,nrparamsfit)
    nums = info[0]
    fitnrs = info[1]
    errorrs = info[2]
    soglias = info[3]
    minvals = info[4]
    vecparamfitteds = info[5]
    sizeofsws = info[6]
    maxofsws = info[7]
    vec5ss = info[8]
    timevecss = info[9]
    cutsinss = info[10]
    vec5realss = info[11]
    with open("test.csv", "a") as myfile2:
        for k in range(len(nums)):
            myfile2.write("%i\t" % nums[k])
            myfile2.write("%s\t" % fitnrs[k])
            myfile2.write("%s\t" % errorrs[k])
            vecps = vecparamfitteds[k]
            for numparams in range(nrparamsfit):
                myfile2.write("%s\t" % vecps[numparams])
            myfile2.write("%s\t" % soglias[k])
            myfile2.write("%s\n" % minvals[k])
    myfile2.close()
    if (singletrace or demo):
        vecerrorssingletrace=[]
        for k in range(len(nums)):
            vecerrorssingletrace.append(errorrs[k])
        if len(vecerrorssingletrace)>0:
            indexplot=[n for n,i in enumerate(vecerrorssingletrace) if i==min(vecerrorssingletrace) ][0]
            print("indexplot ", indexplot)
            print("error ", errorrs[indexplot])
            if (len(nums)==0):
                for k in range(len(timevecss)):
                    vec5pss = vec5ss[k]
                    timevecpss = timevecss[k]
                #plt.plot(timevecpss,vec5pss,'g')
            else:
                sizeofsws2 = sizeofsws[indexplot]
                maxofsws2 = maxofsws[indexplot]
                vec5s2 = vec5ss[indexplot]
                timevecs2 =timevecss[indexplot]
                cutsinss2 = cutsinss[indexplot]
                vec5realss2 = vec5realss[indexplot]
                timevecreal = []
                vec5s2real = []
                for k in range(cutsinss2,cutsinss2+len(vec5realss2)):
                    timevecreal.append(timevecs2[k])
                    vec5s2real.append(vec5s2[k])
                vec5s2final = []
                for k in range(len(vec5s2)):
                    vec5s2final.append(vec5s2[k]-max(vec5s2real))      
                if (sizeofsws2<maxofsws2):
                    for ss in paramname:
                        if 'netstim.start' in ss:
                            startipoz=paramname.index(ss)
                    starti=vecps[startipoz]
                    vecps[startipoz]=starti+timevecs2[cutsinss2]
                    model_current = fitness.run_model(vecps,time_trace=timevecs2);
                    errorverif=0
                    for k in range(cutsinss2,cutsinss2+len(vec5realss2)):
                        errorverif=errorverif+(model_current[k]-vec5s2final[k])*(model_current[k]-vec5s2final[k])
                    errorverif=errorverif/len(vec5s2real)
                    #plt.plot(timevecs2,vec5s2final,'g',timevecs2,model_current,'b')
            imagename='tracefit.png'
            #plt.savefig(imagename, dpi=300)      
    print("done")
    pc.done()
    neuron.h.quit()
    
def fixed(nrparamsfit,paraminitval):
    """Return fixed initialisation"""
    vecinit= []
    for i in range(nrparamsfit):
        vecinit.append(paraminitval[i])
    return vecinit

def optim(twoargss,seedinitvalue,listofvecs,nrparamsfit):
    import neuron
    import fitness
    (num,fitnr)=twoargss
    #print num
    #print fitnr
    #global nefun
    #print "fitnr ", fitnr
    #num=3
    #print "Start Process", os.getpid(), "with args", num, fitnr
    #print "args", num, fitnr
    neuron.h.attr_praxis(1e-4, .5, 0)
    #print seedinitvalue
    neuron.h.attr_praxis(seedinitvalue)
    vecparamforfit2=listofvecs[fitnr]
    #print "initial values ", vecparamforfit2
    vecparamforfit3=[]
    for i in range(int(nrparamsfit)):
        vecparamforfit3.append(math.log(vecparamforfit2[i]))
    vec=neuron.h.Vector(nrparamsfit)
    for i in range(int(nrparamsfit)):
        vec.x[i]=vecparamforfit3[i]
    fitness.nefun=0
    fitness.nquad=0
    neuron.h.stop_praxis(0)
    [sizeofsw,maxofsw,vec5,timevec,cutsin]=fitness.finaltrace(trace_number=num);
    flagsw=0
    soglia=(0.1*min(vec5))**2
    #print "soglia", soglia
    minval=min(vec5)
    [timevecprov,vecallprov]=ref.readexpfile(num=num)
    vecall = []
    for i in range(len(vecallprov)):
        vecall.append(vecallprov[i])
    timevecall = []
    for i in range(len(vecall)):
        timevecall.append(timevecprov[i]-timevecprov[0])
    if (sizeofsw<=maxofsw):
        flagsw=1
        error = neuron.h.fit_praxis(partial(fitness.migliore_eval, trace_number=num, timevec=timevec, vec5=vec5),vec)
        vecparamfitted=[]
        for i in range(int(nrparamsfit)):
            vecparamfitted.append(math.exp(vec.x[i]))
        return (num, fitnr, error, soglia, minval, vecparamfitted, fitness.nefun, sizeofsw, maxofsw, vecall, timevecall, cutsin, vec5)
    else:
        return (num, fitnr, 1e6, soglia, minval, vecparamforfit3, 0, sizeofsw, maxofsw, vecall, timevecall, cutsin, vec5)

def runsim(twoargs,pc,seedinitvalue,listofvecs,nrparamsfit):
    for items in twoargs:
        pc.submit(optim,items,seedinitvalue,listofvecs,nrparamsfit)
    num2s=[]
    fitnr2s=[]
    error2s=[]
    minval2s=[]
    vecparamfitted2s=[]
    soglia2s=[]
    sizeofswrs=[]
    maxofswrs=[]
    vec5rs=[]
    timevecrs=[]
    cutsinrs=[]
    vec5reals=[]
    while (pc.working()):
        num2, fitnr2, error2, soglia2, minval2, vecparamfitted2, nefun2, sizeofswr, maxofswr, vec5r, timevecr, cutsinr, vec5real = pc.pyret()
        print(num2,fitnr2,error2,soglia2,minval2,nefun2)
        if (error2<soglia2):
            num2s.append(num2)
            fitnr2s.append(fitnr2)
            error2s.append(error2)
            soglia2s.append(soglia2)
            minval2s.append(minval2)
        vecparamfitted2s.append(vecparamfitted2)
        sizeofswrs.append(sizeofswr)
        maxofswrs.append(maxofswr)
        vec5rs.append(vec5r)
        timevecrs.append(timevecr)
        cutsinrs.append(cutsinr)
        vec5reals.append(vec5real)
    return (num2s, fitnr2s, error2s, soglia2s, minval2s, vecparamfitted2s, sizeofswrs, maxofswrs, vec5rs, timevecrs, cutsinrs, vec5reals)

if __name__ == "__main__":
    fitting(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7])

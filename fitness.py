import neuron
import math
import copy
import readconffile as rcf
import readexpfile as ref

filename3=''

neuron.h.load_file("nrngui.hoc")
[inputfilename,modfilename,parametersfilename,flagdata,flagcut,nrtraces,Vrestf,esynf,nrparamsfit,paramnr,paramname,paraminitval,paramsconstraints,nrdepnotfit,depnotfit,nrdepfit,depfit,seedinitvaluef]=rcf.readconffile()


def cuttrace( trace_number, sizeofsw ):
    #print "resizing trace: ", trace_number
    #trace_number=0
    #sizeofsw=10
    perccut=10
    flagcut=1
    [timevecprov,vec5]=ref.readexpfile(num=trace_number)
    timevec = []
    for i in range(len(vec5)):
        timevec.append(timevecprov[i])
                        
    # CUT TRACE
    vec5forsliding = copy.copy(vec5)
    
    derivativessliding = []
    idxderivativessliding = []
    for i in range(0,len(vec5)-sizeofsw,sizeofsw):
        vector1ms = []
        for j in range(i,i+sizeofsw+1):
            vector1ms.append(vec5forsliding[j])
        if (vector1ms.index(max(vector1ms))<vector1ms.index(min(vector1ms))):
            derivativessliding.append(max(vector1ms)-min(vector1ms))
            idxderivativessliding.append(i)
    a=0
    maxes = []
    while ((a<=len(derivativessliding)-1) and (len(maxes)<2)):
        if (derivativessliding[a]==max(derivativessliding)):
            if ((max(derivativessliding)/(max(vec5)-min(vec5)))*100>=perccut):
                maxes.append(idxderivativessliding[a])
            derivativessliding[a]=0
        a=a+1
    #print "length maxes: ", len(maxes)
    
    if (len(maxes)==1):
        maxes.append(len(vec5)-1)

    vec5forsliding=[]
    for i in range(maxes[0],maxes[1]+1):
            vec5forsliding.append(vec5[i])

    timevecaftersliding = []
    for i in range(maxes[0],maxes[1]+1):
        timevecaftersliding.append(timevec[i])

    timevec = []
    for i in range(0,len(timevecaftersliding)):
        timevec.append(timevecaftersliding[i]-timevecaftersliding[0])

    vec3 = []
    for i in range(0,len(vec5forsliding)):
        vec3.append(vec5forsliding[i])
    #print "trace ", trace_number , " cutted"
    
    #REMOVE HOLDING CURRENT
    vec5 = []
    if (vec3[0]>=max(vec3)):
        for i in range(0,len(vec3)):
            vec5.append(vec3[i]-vec3[0])
    else:
        for i in range(0,len(vec3)):
            vec5.append(vec3[i]-max(vec3))

    for i in range(0,len(vec5)):
        if (vec5[i]==min(vec5)):
            imin=i
            i=len(vec5)-1

    vecsin = []
    for i in range(0,imin):
        vecsin.append(vec5[i])
    ides=len(vec5)
    
    a=len(vecsin)+1
    while (a<=len(vec5)-1):
        if (vec5[a]>max(vecsin)):
            ides=a
            a=len(vec5)-1
        a=a+1

    vecfin = []
    for i in range(0,ides):
        vecfin.append(vec5[i])

    vecfinfin = []
    for i in range(0,ides):
        vecfinfin.append(vecfin[i]-max(vecfin))

    vec5 = []
    for i in range(0,ides):
        vec5.append(vecfinfin[i])

    timevectemp = []
    for i in range(0,ides):
        timevectemp.append(timevec[i])
    timevec = []
    for i in range(0,ides):
        timevec.append(timevectemp[i])
    #print "removed holding current "
    
    if (flagcut==1):
        timemin=vec5.index(min(vec5)) 
        flag=0
        i=timemin
        while (flag<1 and i<len(vec5)):
            if (vec5[i]>0.2*min(vec5)):
                flag=1
            i=i+1
        i=i-1
        if (i<len(vec5) and timevec[i]>4):
            #print("resizing trace %d to %g ms, %d\n", trace_number, timevec[i], i)
            vec5prov=[]
            for j in range(i):
                vec5prov.append(vec5[j])
            vec5=[]
            for pp in range(len(vec5prov)):
                vec5.append(vec5prov[pp])
            timevecprov=[]
            for j in range(i):
                timevecprov.append(timevec[j])
            timevec=[]
            for pp in range(len(timevecprov)):
                timevec.append(timevecprov[pp])
    vecfinfin = []
    for i in range(0,len(vec5)):
        vecfinfin.append(vec5[i])
    vec5 = []
    for i in range(0,len(vecfinfin)):
        vec5.append(vecfinfin[i])
    timevecfinfin = []
    for i in range(0,len(timevec)):
        timevecfinfin.append(timevec[i])
    timevec = []
    for i in range(0,len(timevecfinfin)):
        timevec.append(timevecfinfin[i]) 
    return [vec5, timevec, maxes[0]];
    

def finaltrace(trace_number=0):
    [timevecprov,vecprov]=ref.readexpfile(num=trace_number)
    exp_current = []
    exp_times = []
    i=0
    while vecprov[i]<1000:
        exp_current.append(vecprov[i])
        exp_times.append(timevecprov[i])
        i=i+1
        if i==len(vecprov): break
        
    vec5 = exp_current
    vec52 = iter(vec5)
    valm = min(vec52)    
    maxofsw = vec5.index(valm)
    #print "maxim sizeofsw ", maxofsw
    
    sizeofsw = int(maxofsw/2)
    #print "sizeofsw ", sizeofsw
    
    perccut=10
    [vec5,timevec,cutsin]=cuttrace(trace_number,sizeofsw);
    
    vec52=iter(vec5)
    valm=min(vec52)
    indvalm=vec5.index(valm)
    while ((indvalm<=20) and (sizeofsw<=maxofsw)):
        sizeofsw=sizeofsw+1
        [vec5,timevec,cutsin]=cuttrace(trace_number,sizeofsw);
        vec52=iter(vec5)
        valm=min(vec52)
        indvalm=vec5.index(valm)
    
    while ((((len(timevec)-indvalm)<=40)) and (sizeofsw<=maxofsw)):
        sizeofsw=sizeofsw+1
        [vec5,timevec,cutsin]=cuttrace(trace_number,sizeofsw);
        vec52=iter(vec5)
        valm=min(vec52)
        indvalm=vec5.index(valm)
    #print "final sizeofsw of trace ", trace_number, "sizeofsw ", sizeofsw
    return [sizeofsw,maxofsw,vec5,timevec, cutsin]

nefun=0
def migliore_eval( vec, timevec, vec5, trace_number=0):
    global nefun
    """Evaluation function of synaptic optimiser"""
    exp_current=vec5
    vecparams=[]
    for i in range(len(vec)):
        vecparams.append(math.exp(vec.x[i]))
    nefun +=1
    #print "nefun ", nefun
    if (nefun>=2000):
        neuron.h.stop_praxis()
    model_current = run_model(
    vecparams,
    time_trace=timevec)
        
    if model_current is None:
        model_error=1e6
    else:
        model_error=0
        for i in range(len(model_current)):
            model_error=model_error+(model_current[i]-exp_current[i])*(model_current[i]-exp_current[i])
        model_error=model_error/len(model_current)
    return model_error
   

def run_model(parameters, time_trace=None):
    """Run the model with the specified set of parameters"""
    import cellprop
    tstop = 100
    e_syn = esynf
    Vrest = Vrestf
    netstim = neuron.h.NetStims(0.5, sec=cellprop.soma)
    netstim.freqhz = 18.0
    netstim.q = 0.0
    netstim.prob = 2.0
    netstim.noise = 1.0
    netstim.number = 1.0
    
    vclamp = neuron.h.VClamp(0.5, sec=cellprop.soma)
    vclamp.dur[0] = tstop
    vclamp.amp[0] = Vrest
    
    with open(filename3) as ff:
        searchlines=ff.readlines()
    for kk, line in enumerate(searchlines):
        if "POINT_PROCESS" in line:
            break
    l2=line.split()
    synapse = neuron.h.__getattribute__(l2[1])(.5)
    synapse.verboseLevel = 0
    synapse.Use = 1.0
    synapse.u0 = 1.0
    synapse.e_GABAA = e_syn
    synapse.setRNG(cellprop.synapse_rng)

    netcon = neuron.h.NetCon(netstim, synapse )
    netcon.delay = 0.0
    netcon.threshold = 0.0

    vclamp_i = neuron.h.Vector()
    timevec = neuron.h.Vector()
    timevec.from_python(time_trace)
  
    #print "nrparamsfit ", nrparamsfit
    neuron.h('''nrparamsfit=0''')
    neuron.h.nrparamsfit=nrparamsfit
    neuron.h('''objref paramnamenrn[nrparamsfit]''')
    for i in range(nrparamsfit):
        neuron.h.paramnamenrn[i]=neuron.h.String()
        neuron.h.paramnamenrn[i].s=paramname[i]   
    neuron.h('''objref parametersnrn''')
    neuron.h('''parametersnrn =new Vector()''')
    neuron.h.parametersnrn.from_python(parameters)
    for i in range(nrparamsfit):
        #print i
        #cmd=paramname[i]+"="+str(parameters[i])
        #print cmd
        #exec cmd
        #print neuron.h.paramnamenrn[i].s
        #print neuron.h.parametersnrn.x[i]
        neuron.h('strdef cmdstr')
        neuron.h('a=0')
        neuron.h.a=i
        neuron.h.execute('sprint(cmdstr,"%s = %g", paramnamenrn[a].s, parametersnrn.x[a])')
        #print neuron.h.cmdstr
        #neuron.h(neuron.h.cmdstr)
        exec(neuron.h.cmdstr)
    #print "geph", synapse.geph
    for i in range(nrdepnotfit):
        cmd=depnotfit[i]
        exec(cmd)
    #print "nhalf", synapse.nhalf

    neuron.h.tstop = tstop
    
    exc=0
    for i in range(nrdepfit):
        cmd=depfit[i]
        if eval(cmd):
            exc=exc or 1
    
    paramnr=0
    for row in paramsconstraints:
        low=row[0]
        high=row[1]
        if (parameters[paramnr]<low or parameters[paramnr]>high):
            exc=exc or 1      
        paramnr=paramnr+1
    
    vclamp_i.record(synapse._ref_i, timevec)
    if (exc==1):
        return None
    else:
        try:
            neuron.h.run()
        except RuntimeError:
            return None
    del netcon
    vclamp_i.mul(1000.0)
    #print cellprop.soma.g_pas
    return vclamp_i.to_python() 

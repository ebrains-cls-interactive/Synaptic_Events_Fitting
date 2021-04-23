import neuron
import readconffile as rcf

neuron.h.use_mcell_ran4(1)
neuron.h.cvode_active(0)
[inputfilename,modfilename,parametersfilename,flagdata,flagcut,nrtraces,Vrestf,esynf,nrparamsfit,paramnr,paramname,paraminitval,paramsconstraints,nrdepnotfit,depnotfit,nrdepfit,depfit,seedinitvaluef]=rcf.readconffile()

tstop = 100
seedinitvalue = seedinitvaluef
Vrest = Vrestf

# Set some fixed parameters of the model
Rm = 28000
RmSoma = Rm
Cm = 1
CmSoma = Cm
RaSoma = 150
neuron.h.celsius = 35.0
neuron.h("proc init() {\n \
                nstep=0\n \
                t=0\n \
                forall {\n \
                    v=%f\n \
                }\n \
                finitialize(%f)\n \
                fcurrent()\n \
                cvode.re_init()\n \
                cvode.event(%f)\n \
                cvode.event(0)\n \
            }\n" % (Vrest, Vrest, tstop))

soma = neuron.h.Section()
soma.L = 10
soma.diam = 10
soma.nseg = 1

soma.insert('pas')
soma.e_pas = Vrest
soma.g_pas = 1 / float(RmSoma)
soma.Ra = RaSoma
soma.cm = CmSoma

neuron.h.mcell_ran4_init(seedinitvalue)

synapse_rng = neuron.h.Random()
synapse_rng.MCellRan4(12345)
synapse_rng.uniform(0, 1)

import os 

def mkjob_by_task(jobname,dirname,cluster,nproc,modules):
    #jobname='half-k{0}'.format(icalc+1)
    #mkjob_by_task(jobname=jobname,
    #    dirname=dirname,
    #    cluster='nokomis',
    #    nproc = flow.nproc,
    #    modules = modules
    
    # Write taskfile1:
    newfile = os.path.join(dirname,"taskfile1")
    f = open (newfile,"w")
    for iproc in range(1,nproc+1):
        f.write("cd 02-WFN/{}; bash run.sh\n".format(iproc))

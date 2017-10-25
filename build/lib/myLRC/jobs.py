import os
from os.path import join as pjoin
import subprocess
from numpy import floor

def get_jobname(dirname):
    """Create an appropriate job name based on the path"""
    home = os.path.realpath(os.environ['HOME'])
    curdir = os.path.realpath(os.path.curdir)
    relpath = os.path.relpath(curdir, home)
    path = pjoin(relpath, dirname)

    # Find the project name
    spath = path.split(os.path.sep)
    projectname = spath[spath.index('Projects')+1]

    # Make an abbreviation for the project
    project_abb = ''
    for alpha in projectname:
        if alpha.isupper():
            project_abb += alpha

    # Find id number for the directory
    id_string = ''
    rest = path.lstrip(os.path.sep)
    while rest:
        rest, last = os.path.split(rest)
        num1 = last.split('-')[0]
        num2 = last.split('-')[-1]
        if num1.isdigit():
            id_string = '-' + num1 + id_string
        elif num2.isdigit():
            id_string = '-' + num2 + id_string

    # Make the job name
    jobname = project_abb + id_string

    return jobname



def make_job(dirname, nproc, nhours, rsync_filter=None, **kwargs):
    """Write the job.sh file."""
    outdir = kwargs.setdefault('outdir', pjoin(dirname, 'Jobs'))
    subprocess.call(['mkdir', '-p', outdir])
    kwargs['outdir'] = os.path.realpath(outdir)

    job = get_job_single(dirname, nproc=nproc, nhours=nhours, **kwargs)
    with open(pjoin(dirname,'job.sh'), 'write') as f:
        f.write(job)

    if rsync_filter:
        with open(pjoin(dirname, '.rsync-filter'), 'write') as f:
            f.write(rsync_filter)


def get_job_single(dirname, modules=[], other_lines=[], environment={}, **kwargs):

    head = "#!/usr/bin/env bash"

    kwargs.setdefault('outdir', os.path.realpath(pjoin(dirname, 'Jobs')))

    if kwargs.get('omp'):
        environment['OMP_NUM_THREADS'] = kwargs['omp']

    preemble = get_slurm_job_preemble(**kwargs)
    env = get_environment(environment)
    modules_part = get_modules_part(modules)
    other = '\n'.join(other_lines)
    exec_part = get_job_exec_part_single(dirname, **kwargs)

    S = '\n'.join([head, preemble, env, modules_part, other, exec_part]) + '\n'

    return S

def get_environment(environment):
    S = ''
    for key, val in environment.iteritems():
        if isinstance(val, str):
            sval = "'{}'".format(val)
        else:
            sval = str(val)
        S += 'export {}={}\n'.format(key, sval)
    return S


def get_modules_part(modules):
    S = ''
    for module in modules:
        S += 'module load ' + str(module) + '\n'
    return S


def get_slurm_job_preemble(
        jobname='job',
        outdir=None,
        queue='normal',
        nodes=1,
        nproc=16,
        nhours=1,
        allocation=None,
        node_type='haswell',
        qos=None,
        **kwargs):

        # Alias for allocation
        if 'account' in kwargs:
            allocation = kwargs['account']

        tag = '#SBATCH '

        S = ''
        if jobname:
            S += tag + ' -J ' + str(jobname) + '\n'

        if outdir:
            stdout = pjoin(outdir, jobname + '.%j.out')
            S += tag + ' -o ' + str(stdout) + '\n'

        if queue:
            S += tag + ' -p ' + str(queue) + '\n'

        if qos:
            S += tag + ' --qos=' + str(qos) + '\n'

        if node_type:
            S += tag + ' -C ' + str(node_type) + '\n'

        if nodes:
            S += tag + ' -N ' + str(nodes) + '\n'

        if nproc:
            S += tag + ' -n ' + str(nproc) + '\n'

        if nhours:
            nmins = int(60 * (nhours - floor(nhours)))
            nhours = int(nhours)
            S += tag + ' -t {:0=2}:{:0=2}:00\n'.format(nhours,nmins)

        if allocation:
            S += tag + ' -A ' + str(allocation) + '\n'

        return S

def get_job_exec_part_single(dirname, runscript='run.sh', **kwargs):

    home = os.path.realpath(os.environ['HOME'])
    curdir = os.path.realpath(os.path.curdir)
    relpath = os.path.relpath(curdir, home)

    S = """
    # Paths
    RELPATH={relpath}
    ORIGINAL_DIR=$HOME/$RELPATH
    SCRATCH_DIR=$SCRATCH/$RELPATH
    SUBDIR={dirname}
    
    # Make scratch dir and copy files there
    mkdir -p $SCRATCH_DIR/$SUBDIR
    ln -nfs $SCRATCH_DIR $ORIGINAL_DIR/scratch-$NERSC_HOST
    rsync -avh $ORIGINAL_DIR/$SUBDIR/ $SCRATCH_DIR/$SUBDIR --exclude='Jobs'
    
    # Execution
    cd $SCRATCH_DIR/$SUBDIR
    bash {runscript}
    
    # Copy relevant data back from scratch
    cd $SCRATCH_DIR
    rsync -avhF  $SCRATCH_DIR/$SUBDIR/ $ORIGINAL_DIR/$SUBDIR
    
    """.format(relpath=relpath, dirname=dirname, runscript=runscript)

    SS = '\n'.join([line.lstrip() for line in S.splitlines()]) + '\n'

    return SS

def make_submit(dirnames, fname='submit.sh'):
    """
    Create a script named 'submit.sh' which submit a 'job.sh' scripts
    in each directory of a list.
    """

    directories = '"\n' + '\n'.join(dirnames) + '\n"'

    back = os.path.relpath('.', dirnames[0])

    content = """#!/usr/bin/env bash

DIRS={directories}
for DIR in $DIRS; do
    cd $DIR
    sbatch job.sh
    cd {back}
done

""".format(directories=directories, back=back)

    with open(fname, 'write') as f:
        f.write(content)



#def get_job_multi(dirnames, nproc, nhours, outdir=None, modules=[], other_lines=[]):
#
#    home = os.path.realpath(os.environ['HOME'])
#    curdir = os.path.realpath(os.path.curdir)
#    relpath = os.path.relpath(curdir, home)
#    back = os.path.relpath('.', dirnames[0])
#
#    jobname = get_jobname(dirnames[0])
#
#    directories = '"\n' + '\n'.join(dirnames) + '\n"'
#
#    eo = ''
#    if outdir:
#        job_out_dir = os.path.join(curdir, outdir)
#        eo = """
##PBS -e {job_out_dir}/{jobname}.e
##PBS -o {job_out_dir}/{jobname}.o
#        """.format(job_out_dir=job_out_dir, jobname=jobname)
#
#    pbs_preamble = """
##PBS -q regular
##PBS -N {jobname}
##PBS -l mppwidth={nproc}
##PBS -l walltime={nhours:0=2}:00:00
##PBS -m n
#{eo}
#    """.format(jobname=jobname, eo=eo.strip(), nproc=nproc, nhours=nhours)
#
#    other = '\n'.join(other_lines)
#
#    loading = ''
#    if modules:
#        for mod in modules:
#            loading += 'module load {}\n'.format(mod)
#
#    main = """
## Paths
#RELPATH={relpath}
#ORIGINAL_DIR=$HOME/$RELPATH
#SCRATCH_DIR=$SCRATCH/$RELPATH
#
## Make scratch dir and copy files there
#mkdir -p $SCRATCH_DIR
#ln -nfs $SCRATCH_DIR $ORIGINAL_DIR/scratch
#DIRS={directories}
#for DIR in $DIRS; do
#    rsync -avh $ORIGINAL_DIR/$DIR $SCRATCH_DIR/ --exclude='Jobs'
#done
#
## Execution
#cd $SCRATCH_DIR
#for DIR in $DIRS; do
#    echo $DIR
#    cd $DIR
#    . run.sh
#    cd {back}
#    # Copy relevent data back from scratch
#    rsync -avhF  $SCRATCH_DIR/$DIR $ORIGINAL_DIR
#done
#    """.format(relpath=relpath, directories=directories, back=back)
#
#    content = '\n\n'.join([pbs_preamble, other, loading, main])
#
#    return content


#def make_job_debug(dirname, nproc, nhours='dummy', rsync_filter=None, **kwargs):
#    """Write the job.sh file."""
#    subprocess.call(['mkdir', '-p', pjoin(dirname, 'Jobs')])
#
#    job = get_job_debug(dirname, nproc, outdir=pjoin(dirname, 'Jobs'), **kwargs)
#    with open(pjoin(dirname,'job.sh'), 'write') as f:
#        f.write(job)
#
#    if rsync_filter:
#        with open(pjoin(dirname, '.rsync-filter'), 'write') as f:
#            f.write(rsync_filter)
#
#
#def get_job_debug(dirname, nproc, outdir=None, modules=[], other_lines=[]):
#
#    home = os.path.realpath(os.environ['HOME'])
#    curdir = os.path.realpath(os.path.curdir)
#    relpath = os.path.relpath(curdir, home)
#    topsub = dirname.split(os.path.sep)[0]
#
#    back = os.path.relpath('.', dirname)
#
#    head = "#!/usr/bin/env bash"
#
#    id_string = ''
#    rest = pjoin(relpath, dirname)
#    while rest:
#        rest, last = os.path.split(rest)
#        num = last.split('-')[0]
#        if num.isdigit():
#            id_string = '-' + num + id_string
#    jobname = 'TDM' + id_string
#
#    eo = ''
#    if outdir:
#        job_out_dir = os.path.join(curdir, outdir)
#        eo = """
##PBS -e {job_out_dir}/{jobname}.e
##PBS -o {job_out_dir}/{jobname}.o
#        """.format(job_out_dir=job_out_dir, jobname=jobname)
#
#    pbs_preamble = """
##PBS -q debug
##PBS -N {jobname}
##PBS -l mppwidth={nproc}
##PBS -l walltime=00:30:00
##PBS -m n
#{eo}
#    """.format(jobname=jobname, eo=eo.strip(), nproc=nproc)
#
#    other = '\n'.join(other_lines)
#
#    loading = ''
#    if modules:
#        for mod in modules:
#            loading += 'module load {}\n'.format(mod)
#
#    main = get_job_exec_part_single(dirname)
#
#    content = '\n\n'.join([head, pbs_preamble, other, loading, main])
#
#    return content



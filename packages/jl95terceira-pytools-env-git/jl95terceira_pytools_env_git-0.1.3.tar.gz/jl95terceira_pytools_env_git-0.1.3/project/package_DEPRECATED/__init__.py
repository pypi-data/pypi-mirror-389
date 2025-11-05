import os.path

from jl95terceira.pytools.envlib import var

GIT_HOME         = var(name       ='git.home', 
                       description='the home of Git')
GIT              = var(name       ='git', 
                       description='the path to Git (\'git.exe\')',
                       default    =os.path.join(GIT_HOME.get(), 'bin', 'git') if GIT_HOME.check() else 'git')
GIT_REMOTE       = var(name       ='git.remote', 
                       description='the alias of git remote that is commonly used (usually \'origin\')',
                       default    ='origin')


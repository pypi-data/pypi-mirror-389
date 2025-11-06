######################################################################################################
#                                 Auto-generated Metaflow stub file                                  #
# MF version: 2.19.4.1+obcheckpoint(0.2.8);ob(v1)                                                    #
# Generated on 2025-11-05T18:18:28.351558                                                            #
######################################################################################################

from __future__ import annotations

import metaflow
import typing
if typing.TYPE_CHECKING:
    import metaflow.plugins.pypi.conda_environment

from .conda_environment import CondaEnvironment as CondaEnvironment

class PyPIEnvironment(metaflow.plugins.pypi.conda_environment.CondaEnvironment, metaclass=type):
    ...


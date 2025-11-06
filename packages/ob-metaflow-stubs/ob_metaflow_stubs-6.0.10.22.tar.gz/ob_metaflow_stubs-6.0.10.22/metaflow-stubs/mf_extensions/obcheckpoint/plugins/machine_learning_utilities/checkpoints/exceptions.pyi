######################################################################################################
#                                 Auto-generated Metaflow stub file                                  #
# MF version: 2.19.4.1+obcheckpoint(0.2.8);ob(v1)                                                    #
# Generated on 2025-11-05T18:18:28.322600                                                            #
######################################################################################################

from __future__ import annotations

import metaflow
import typing
if typing.TYPE_CHECKING:
    import metaflow.exception

from ......exception import MetaflowException as MetaflowException

class CheckpointNotAvailableException(metaflow.exception.MetaflowException, metaclass=type):
    def __init__(self, message):
        ...
    ...

class CheckpointException(metaflow.exception.MetaflowException, metaclass=type):
    def __init__(self, message):
        ...
    ...


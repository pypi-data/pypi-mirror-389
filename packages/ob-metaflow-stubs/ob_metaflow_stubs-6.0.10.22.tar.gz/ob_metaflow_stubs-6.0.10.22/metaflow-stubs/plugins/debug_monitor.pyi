######################################################################################################
#                                 Auto-generated Metaflow stub file                                  #
# MF version: 2.19.4.1+obcheckpoint(0.2.8);ob(v1)                                                    #
# Generated on 2025-11-05T18:18:28.319992                                                            #
######################################################################################################

from __future__ import annotations

import metaflow
import typing
if typing.TYPE_CHECKING:
    import metaflow.monitor


class DebugMonitor(metaflow.monitor.NullMonitor, metaclass=type):
    @classmethod
    def get_worker(cls):
        ...
    ...

class DebugMonitorSidecar(object, metaclass=type):
    def __init__(self):
        ...
    def process_message(self, msg):
        ...
    ...


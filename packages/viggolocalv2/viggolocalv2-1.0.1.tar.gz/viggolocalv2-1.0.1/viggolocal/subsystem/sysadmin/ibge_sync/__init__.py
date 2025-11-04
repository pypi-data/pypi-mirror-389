from viggocore.common import subsystem
from viggolocal.subsystem.sysadmin.ibge_sync \
  import resource, manager

subsystem = subsystem.Subsystem(resource=resource.IbgeSync,
                                manager=manager.Manager)

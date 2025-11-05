from viggocorev2.common import subsystem
from viggoparceirov2.subsystem.parceiro import (
    resource, manager, controller, router)

subsystem = subsystem.Subsystem(resource=resource.Parceiro,
                                manager=manager.Manager,
                                controller=controller.Controller,
                                router=router.Router)

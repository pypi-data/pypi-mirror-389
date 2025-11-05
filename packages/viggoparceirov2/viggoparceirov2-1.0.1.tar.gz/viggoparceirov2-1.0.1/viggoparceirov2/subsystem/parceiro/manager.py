from viggocorev2.common import exception
from viggocorev2.common.subsystem import manager
from viggoparceirov2.subsystem.parceiro.functions import (
    entity_create, entity_update, get_usuarios_disponiveis)


class Manager(manager.Manager):

    def __init__(self, driver):
        super(Manager, self).__init__(driver)
        self.create = entity_create.Create(self)
        self.update = entity_update.Update(self)
        self.get_usuarios_disponiveis = (
            get_usuarios_disponiveis.GetUsuariosDisponiveis(self))

    def validar_rg_inc_est(self, **kwargs):
        rg_insc_est = kwargs.get('rg_insc_est', None)
        if rg_insc_est is not None and len(rg_insc_est.strip()) == 0:
            rg_insc_est = None
        return rg_insc_est

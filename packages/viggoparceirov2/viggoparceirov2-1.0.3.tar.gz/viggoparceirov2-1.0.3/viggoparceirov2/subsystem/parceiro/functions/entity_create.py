from viggocorev2.common.subsystem import operation


class Create(operation.Create):

    def pre(self, **kwargs):
        kwargs['rg_insc_est'] = self.manager.validar_rg_inc_est(**kwargs)
        return super().pre(**kwargs)

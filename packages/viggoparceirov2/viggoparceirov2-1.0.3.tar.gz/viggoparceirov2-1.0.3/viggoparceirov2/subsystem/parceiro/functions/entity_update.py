from viggocorev2.common.subsystem import operation


class Update(operation.Update):

    def do(self, session, **kwargs):
        kwargs['rg_insc_est'] = self.manager.validar_rg_inc_est(**kwargs)
        return super().do(session, **kwargs)

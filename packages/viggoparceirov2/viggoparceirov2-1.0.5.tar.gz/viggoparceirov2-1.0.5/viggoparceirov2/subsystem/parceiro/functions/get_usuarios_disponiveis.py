
from sqlalchemy import or_
from viggocorev2.common.subsystem import operation
from viggocorev2.subsystem.user.resource import User
from viggocorev2.common.subsystem.pagination import Pagination
from viggoparceirov2.subsystem.parceiro.resource import Parceiro


class GetUsuariosDisponiveis(operation.List):

    def do(self, session, **kwargs):
        user_id = kwargs.pop('user_id', None)

        query = session.query(User)\
            .join(Parceiro, Parceiro.user_id == User.id, isouter=True)\
            .filter(or_(Parceiro.user_id == None,  # noqa: E711
                        User.id == user_id))
        query = self.manager.apply_filters(query, User, **kwargs)

        dict_compare = {"parceiro.": Parceiro}
        query = self.manager.apply_filters_includes(
            query, dict_compare, **kwargs)
        query = query.distinct()

        total_rows = None
        if self.manager.with_pagination(**kwargs):
            total_rows = query.count()

        pagination = Pagination.get_pagination(User, **kwargs)
        if pagination.order_by is not None:
            pagination.order_by = '\"user\".id'
        query = self.driver.apply_pagination(query, pagination)
        result = query.all()

        return (result, total_rows)

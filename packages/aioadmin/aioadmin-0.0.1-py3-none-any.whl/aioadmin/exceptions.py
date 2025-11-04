class AioAdminException(Exception):
    pass

class TargetAlreadyExistsError(AioAdminException):
    pass

class ForeignKeyConstraintError(AioAdminException):
    pass


class ConciergeException(Exception):
    def __init__(self, code='', message=''):
        """
        :param code: A short string that can be checked against, such as
            'PermissionDenied'
        :param message: A longer string that describes the problem and action
            that should be taken.
        """
        self.code = code or 'UnexpectedError'
        self.message = message or ('The Concierge Server encountered an '
                                   'error, please contact your system '
                                   'administrator.')

    def __str__(self):
        return '{}: {}'.format(self.code, self.message)

    def __repr__(self):
        return str(self)


class LoginRequired(ConciergeException):

    def __init__(self, message=''):
        super(LoginRequired, self).__init__(self)
        self.code = 'LoginRequired'
        self.message = ('A login is required due to expired or '
                        'non-existant credentials')

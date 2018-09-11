class BaseError(Exception):
    def __init__(self, msg='Error'):
        super(BaseError, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return '%s' % self.msg


class SizeError(BaseError):
    def __init__(self, msg='超出文件系统大小限制'):
        super(SizeError, self).__init__(msg)


class ExtensionError(BaseError):
    def __init__(self, msg='文件格式错误'):
        super(ExtensionError, self).__init__(msg)


class DuplicationError(BaseError):
    def __init__(self, msg='有重复'):
        super(DuplicationError, self).__init__(msg)

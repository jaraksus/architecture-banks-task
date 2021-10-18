class Status(object):
    def __init__(self, error=None):
        self.error = error

    @staticmethod
    def Ok():
        return Status()
    
    @staticmethod
    def Error(error_msg: str):
        return Status(error_msg)

    def IsOk(self) -> bool:
        return self.error is None

    def GetError(self) -> str:
        return self.error

class ValueHolder(Status):
    def __init__(self, value=None, error=None):
        Status.__init__(self, error=error)

        self.value = value
    
    @staticmethod
    def Ok(value):
        return ValueHolder(value=value)
    
    @staticmethod
    def Error(error_msg: str):
        return ValueHolder(error=error_msg)

    def Get(self):
        return self.value

    def GetOrRaise(self, message=""):
        if self.error is None:
            return self.value
        raise RuntimeError(message + self.error)

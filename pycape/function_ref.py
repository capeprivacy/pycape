class FunctionRef:
    def __init__(self, function_id, function_hash=None):
        self._function_id = function_id
        self._function_hash = function_hash

    def get_id(self):
        return self._function_id

    def get_hash(self):
        return self._function_hash

    def set_hash(self, function_hash):
        self._function_hash = function_hash

from typing import Callable, Any


class binder:
    def __init__(self, *args, **kwargs):
        self.bind(*args, **kwargs)
    
    def bind(self, *args, **kwargs):
        self.arguments = args
        self.keyword_arguments = kwargs
    
    def update(self, *args, **kwargs):
        num_args = len(args)
        if num_args > 0:
            if num_args > len(self.arguments):
                self.arguments = args
            else:
                self.arguments = args + self.arguments[num_args:]
        if len(kwargs) > 0:
            self.keyword_arguments.update(kwargs)
    
    def invoke(self, callable: Callable[..., Any]) -> Any:
        return callable(*self.arguments, **self.keyword_arguments)
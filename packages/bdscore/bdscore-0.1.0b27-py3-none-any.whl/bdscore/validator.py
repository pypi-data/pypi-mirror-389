from enum import Enum
from functools import wraps
from inspect import Parameter, signature


def validate():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sig = signature(func)
            params = {}
            for i, parameter in enumerate(sig.parameters):
                if parameter in {'self', 'kwargs'}:
                    continue

                if parameter in kwargs:
                    value = kwargs[parameter]
                else:
                    value = args[i] if i < len(args) else \
                            sig.parameters[parameter].default if sig.parameters[parameter].default is not Parameter.empty else \
                            None
                    if type(sig.parameters[parameter].annotation) is str and 'None' not in sig.parameters[parameter].annotation and value is None:
                        raise ValueError("O parâmetro '" + parameter + "' é obrigatório.")

                if isinstance(value, Enum):
                    value = value.value

                if value is not None:
                    params[parameter] = value

            kwargs['params'] = params
            return func(*args, **kwargs)
        return wrapper
    return decorator

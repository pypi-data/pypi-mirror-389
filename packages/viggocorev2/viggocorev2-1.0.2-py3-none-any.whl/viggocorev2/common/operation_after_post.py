from viggocorev2.common import exception


operation_after_post_registry = dict()


def do_after_post(manager, operation):
    '''
    Decorator for register action after post based on manager operation

    Parameters:
        manager(cls): The Manager class reference
        operation(cls): The Operation class reference

    Returns:
        do_after_post(manager, operation)(fn): The original function
    '''

    def wrapper(fn):
        key = (manager, operation)
        if operation_after_post_registry.get(key):
            raise exception.ViggoCoreException(
                f'A operação {manager}.{operation} já estava registrada.')

        operation_after_post_registry[key] = fn
        return fn

    return wrapper

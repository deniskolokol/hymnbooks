import inspect

def call_stack(func):
    """
    Use it for testing as a decorator:

    from hymnbooks.apps import call_stack

    @call_stack
    def def_name(*args, **kwargs):
        do stuff...
    """
    def callf(*args,**kwargs):
        for i_s in inspect.stack():
            info = i_s[1:]
            print '%s (%s) %s\n%s' % (info[0], info[2], info[1], info[3][0])

        r = func(*args,**kwargs)
        return r

    return callf

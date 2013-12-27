import inspect

def call_stack(func):

    def callf(*args,**kwargs):
        for i_s in inspect.stack():
            info = i_s[1:]
            print '%s (%s) %s\n%s' % (info[0], info[2], info[1], info[3][0])

        r = func(*args,**kwargs)
        return r

    return callf

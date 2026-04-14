class Visitable(object):
    class Visitor(object):
        def visit_Visitable(self, obj, *args, **kwargs):
            return NotImplemented

    @classmethod
    def visit_method_name(cls):
        return "visit_%s" % cls.__name__

    @classmethod
    def get_visit_method(cls, vis, default=None):
        return getattr(vis, cls.visit_method_name(), default)

    def accept(self, vis, *args, **kwargs):
        meth = None
        for c in reversed(self.__class__.mro()):
            if issubclass(c, Visitable):
                meth = c.get_visit_method(vis, meth)
        if meth:
            return meth(self, *args, **kwargs)
        else:
            return NotImplemented

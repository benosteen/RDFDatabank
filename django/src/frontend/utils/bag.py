# The oft-coded 'dict with property access for keys' - required for the context object
# used in the Pylons Mako code.
# TODO: Migrate from 'c' context object use in Mako to plain dict of values eg {'user:...}
# rather than dumping it all in a single object and passing that ({'c':c})

# This particular example is based on http://benlast.livejournal.com/12301.html but there are many like it

class Context(object):
    def __init__(self, **kw):
        self.__b = Bag()
        
    def __getitem__(self, key):
        return self.__b.__getitem__(key)
    
    def __setitem__(self, key, value):
        self.__b.__setitem__(key, value)
    
    def has_key(self, key):
        return self.__b.has_key(key)
    
    def keys(self):
        return self.__b.keys()
    
    def iterkeys(self):
        return self.__b.iterkeys()
    
    def __iter__(self):
        return self.__b.__iter__()
        
    def __str__(self):
        return self.__b.__str__()
    
    def __getattr__(self, key):
        if self.__b.has_key(key):
            return getattr(self.__b, key)
        else:
            return None

class Bag(object):
    def __init__(self, **kw):
        """Initialise, and set attributes from all keyword arguments."""
        self.__allow_access_to_unprotected_subobjects__=1
        self.__members=[]
        for k in kw.keys():
            setattr(self,k,kw[k])
            self.__remember(k)

    def __remember(self, k):
        """Add k to the list of explicitly set values."""
        if not k in self.__members:
            self.__members.append(k)

    def __getitem__(self, key):
        """Equivalent of dict access by key."""
        try:
            att = getattr(self, key)
            return att
        except AttributeError:
            # mimic pylons context
            return None


    def __setitem__(self, key, value):
        setattr(self, key, value)
        self.__remember(key)


    def has_key(self, key):
        return hasattr(self, key)


    def keys(self):
        return self.__members


    def iterkeys(self):
        return self.__members


    def __iter__(self):
        return iter(self.__members)


    def __str__(self):
        """Describe only those attributes explicitly set."""
        s = ""
        for x in self.__members:
            v = getattr(self, x)
            if s: s+=", "
            s += "%s: %s" % (x, `v`)
        return s

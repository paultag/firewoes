import hashlib
from firehose_noslots import _string_type

def strhash(string):
    """
    Returns the cryptographic hash of a string.
    This allows to easily change the hash algorithm.
    """
    return hashlib.sha1(string).hexdigest()

def get_attrs(obj):
    """
    For a Firehose object, returs a list of tuples (attribute_name, attribute)
    for each of its nodes
    """
    return [(attr.name, getattr(obj, attr.name)) for attr in obj.attrs]

def idify(obj, debug=False):
    """
    Performs a bottom-up browsing of a Firehose tree, to add to each
    object its id, which is its cryptographic hash.
    Acts recursively.
    Returns a tuple: (object_with_id, object_id(=object_hash))
    """
    if debug:
        print("ENTERING " + str(obj)[:60])
    
    if obj is None:
        return (None, strhash(""))
    
    elif type(obj) in [int, float, str, _string_type]:
        return (obj, strhash(str(obj)))
    
    elif isinstance(obj, list):
        result = [idify(item) for item in obj]
        return result
    
    else:
        objhash = ""
        for (attr_name, attr) in get_attrs(obj):
            res = idify(attr)
            if debug:
                print("SETATTR %s // %s" % (str(obj)[:40], attr_name))
            
            if isinstance(res, list):
                # we get the objects:
                items_without_hashes = [item[0] for item in res]
                # we add their hashes:
                for item in res:
                    objhash += item[1]
                
                # and we update the attribute:
                setattr(obj, attr_name, items_without_hashes)
            else:
                # we add the hash:
                objhash += res[1]
                
                # and update the attribute:
                setattr(obj, attr_name, res[0])
        
        # final hash is the id:
        obj.id = strhash(objhash)
        
        return (obj, obj.id)

def uniquify(session, obj, debug=False):
    """
    Renders a Firehose tree unique, regarding an SQLAlchemy session.
    Inspired by http://www.sqlalchemy.org/trac/wiki/UsageRecipes/UniqueObject
    """
    if debug:
        print("UNIQUIFY: %s" % str(obj)[:60])
    
    # we kep objetcs in cache for better performances
    cache = getattr(session, '_unique_cache', None)
    if cache is None:
        session._unique_cache = cache = {}
    
    key = (obj.__class__, obj.id)
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            res = (session.query(obj.__class__)
                   .filter(obj.__class__.id == obj.id).first())
            if not res:
                # the object doesn't exist in the db,
                # we check recursively its attributes and add it
                res = obj
                
                # recursion
                for (attr_name, attr) in get_attrs(res):
                    if isinstance(attr, list):
                        # if it's a list we do this for each item
                        setattr(res,
                                attr_name,
                                [uniquify(session, item) for item in attr])
                            
                    elif (type(attr) not in (int, float, str, _string_type)
                          and attr is not None):
                        setattr(res, attr_name, uniquify(session, attr))
                
                # we finally add it
                session.add(res)
        # update the cache
        cache[key] = res
        
        return res

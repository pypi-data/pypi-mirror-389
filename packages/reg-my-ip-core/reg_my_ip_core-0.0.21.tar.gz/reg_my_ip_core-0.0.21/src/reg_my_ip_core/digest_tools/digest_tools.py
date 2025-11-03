
import hashlib
def md5_hash(d):
    digest = hashlib.md5()
    digest.update(d.encode('utf-8'))
    md5=digest.hexdigest()
    return md5
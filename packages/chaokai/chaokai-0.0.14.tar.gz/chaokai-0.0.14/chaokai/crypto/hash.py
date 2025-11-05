import hashlib


def sha1(str_data, salt=''):
    value = str_data + salt
    data_bytes = value.encode('utf-8')
    sha1_hash = hashlib.sha1(data_bytes).hexdigest()
    return sha1_hash


def md5(str_data, salt=''):
    value = str_data + salt
    data_bytes = value.encode('utf-8')
    md5_hash = hashlib.md5(data_bytes).hexdigest()
    return md5_hash


def sha256(str_data, salt=''):
    value = str_data + salt
    data_bytes = value.encode('utf-8')
    sha256_hash = hashlib.sha256(data_bytes).hexdigest()
    return sha256_hash


if __name__ == '__main__':
    r = sha1('haha', salt='abc')
    print(r)
    r = md5('haha', salt='abc')
    print(r)
    r = sha256('haha', salt='abc')
    print(r)

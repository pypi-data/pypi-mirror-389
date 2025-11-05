# -*- coding: utf-8 -*-
# from Cryptodome.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Cryptodome.Cipher import PKCS1_OAEP

from Cryptodome.PublicKey import RSA
import base64


def create_rsa_pair(bits=2048):
    '''
    创建rsa公钥私钥对
    :return: public_key, private_key
    '''
    f = RSA.generate(bits=bits)
    private_key = f.exportKey("PEM").decode()  # 生成私钥
    public_key = f.publickey().exportKey().decode()  # 生成公钥

    return public_key, private_key


def encrypt(public_key, message):
    """
    使用公钥加密
    :param public_key: 公钥字符串
    :param message:
    :return:
    """
    rsakey = RSA.importKey(public_key)
    # cipher = Cipher_pkcs1_v1_5.new(rsakey)  # 创建用于执行pkcs1_v1_5加密或解密的密码
    cipher = PKCS1_OAEP.new(rsakey)  # 创建用于PKCS1_OAEP填充方式
    cipher_text = base64.b64encode(cipher.encrypt(message.encode('utf-8')))
    enstr = cipher_text.decode('utf-8')
    return enstr


def decrypt(private_key, encrypt_str):
    """
    使用私钥解密
    :param private_key: 私钥字符串
    :param encrypt_str: 需要解密的字符串
    :return:
    """
    encrypt_text = encrypt_str.encode('utf-8')
    rsakey = RSA.importKey(private_key)
    # cipher = Cipher_pkcs1_v1_5.new(rsakey)  # 创建用于执行pkcs1_v1_5加密或解密的密码
    # text = cipher.decrypt(base64.b64decode(encrypt_text), "解密失败")

    cipher = PKCS1_OAEP.new(rsakey)  # 创建用于PKCS1_OAEP填充方式
    text = cipher.decrypt(base64.b64decode(encrypt_text))

    text = text.decode()
    return text




if __name__ == '__main__':

    public_key, private_key = create_rsa_pair()
    print(public_key)
    print(private_key)

    # 加密
    encrypt_str = encrypt(public_key, '哈哈哈')
    print(encrypt_str)

    # 解密
    message = decrypt(private_key, encrypt_str)
    print(message)

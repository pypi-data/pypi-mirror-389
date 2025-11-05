# -*- coding: utf-8 -*-
import secrets
import string

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes
import base64


def create_aes_key(length=16, contain_punctuation=True):
    """
    生成key key需8的倍数
    :return:
    """
    # 是否包含标点符号,默认是大小写+数字
    if contain_punctuation:
        characters = string.ascii_letters + string.digits + string.punctuation
    else:
        characters = string.ascii_letters + string.digits

    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string


class AES_ECB:
    def __init__(self, key):
        # 初始化密钥
        self.key = key
        # 初始化数据块大小
        self.length = AES.block_size
        # 初始化AES,ECB模式的实例
        self.aes = AES.new(self.key.encode("utf-8"), AES.MODE_ECB)
        # 截断函数，去除填充的字符
        self.unpad = lambda date: date[0:-ord(date[-1])]

    def fill_method(self, aes_str):
        """
        pkcs7补全-加密字符串也需要16的倍数，这里用PKCS-7规则补齐
        :param aes_str:
        :return:
        """
        pad_pkcs7 = pad(aes_str.encode('utf-8'), AES.block_size, style='pkcs7')

        return pad_pkcs7

    def encrypt(self, message):
        """
        AES加密
        :param encrData: 要加密的字符串
        :return:
        """
        # 加密函数,使用pkcs7补全
        res = self.aes.encrypt(self.fill_method(message))
        # 转换为base64
        msg = str(base64.b64encode(res), encoding="utf-8")

        return msg

    def decrypt(self, decrData):
        """
        AES解密
        :param decrData: 要解密的字符串
        :return:
        """
        # base64解码
        res = base64.decodebytes(decrData.encode("utf-8"))
        # 解密函数
        msg = self.aes.decrypt(res).decode("utf-8")

        return self.unpad(msg)


class AES_CBC:
    def __init__(self, key):
        """
        初始化 AES-CBC 加密器
        :param key: 密钥（16/24/32 字节的字节串，或对应长度的 UTF-8 字符串）
        """
        if isinstance(key, str):
            key = key.encode("utf-8")  # 字符串密钥转为字节
        self.key = key
        self.block_size = AES.block_size  # 固定 16 字节

    def encrypt(self, plaintext):
        """
        AES-CBC 加密
        :param plaintext: 明文（字符串或字节）
        :return: Base64 编码的 IV + 密文
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        # 生成随机 IV（必须 16 字节）
        iv = get_random_bytes(self.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # PKCS#7 填充 + 加密
        ciphertext = cipher.encrypt(pad(plaintext, self.block_size))

        # 返回 IV + 密文的 Base64（IV 需传给解密方）
        return base64.b64encode(iv + ciphertext).decode("utf-8")

    def decrypt(self, ciphertext):
        """
        AES-CBC 解密
        :param ciphertext: Base64 编码的 IV + 密文
        :return: 解密后的字符串
        """
        data = base64.b64decode(ciphertext.encode("utf-8"))
        iv = data[:self.block_size]  # 提取前 16 字节 IV
        ciphertext = data[self.block_size:]  # 剩余部分是密文

        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), self.block_size)

        return plaintext.decode("utf-8")


# 示例用法
if __name__ == "__main__":
    key = create_aes_key()
    print('key是:', key)
    print('*' * 33)

    # 初始化AES_CBC模式
    aes_cbc = AES_CBC(key)
    # 加密
    encrypted_cbc = aes_cbc.encrypt("Hello, CBC模式更安全！")
    print("加密结果:", encrypted_cbc)
    # 解密
    decrypted_cbc = aes_cbc.decrypt(encrypted_cbc)
    print("解密结果:", decrypted_cbc)

    print('*' * 33)

    # 初始化AES_ECB模式
    aes_ecb = AES_ECB(key)
    # 加密
    encrypted_ecb = aes_ecb.encrypt("Hello, ECB模式不建议不安全！")
    print("加密结果:", encrypted_ecb)
    # 解密
    decrypted_ecb = aes_ecb.decrypt(encrypted_ecb)
    print("解密结果:", decrypted_ecb)

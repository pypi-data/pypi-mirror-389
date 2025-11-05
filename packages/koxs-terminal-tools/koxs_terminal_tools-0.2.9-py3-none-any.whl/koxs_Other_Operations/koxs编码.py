"""
crypto_utils.py - 多功能加密工具模块
支持多种加密算法：AES, RSA, DES, 3DES, ChaCha20, 以及哈希函数和数字签名
"""

import os
import base64
import hashlib
from Crypto.Cipher import AES, DES, DES3, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import chacha20

class CryptoUtils:
    """加密工具类"""
    
    # 哈希函数
    @staticmethod
    def md5_hash(data):
        """计算 MD5 哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.md5(data).hexdigest()
    
    @staticmethod
    def sha256_hash(data):
        """计算 SHA-256 哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def sha512_hash(data):
        """计算 SHA-512 哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha512(data).hexdigest()
    
    # AES 加密
    @staticmethod
    def aes_encrypt(plaintext, key=None, mode='CBC'):
        """
        AES 加密
        :param plaintext: 明文（字符串或字节）
        :param key: 密钥（16, 24 或 32 字节），如果为 None 则自动生成
        :param mode: 加密模式 ('CBC', 'ECB', 'CFB', 'OFB')
        :return: (密文, 密钥, iv) 元组
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        if key is None:
            key = get_random_bytes(32)  # 默认使用 256 位密钥
        
        # 根据密钥长度确定 AES 模式
        if len(key) == 16:
            aes_mode = AES.MODE_CBC
        elif len(key) == 24:
            aes_mode = AES.MODE_CBC
        elif len(key) == 32:
            aes_mode = AES.MODE_CBC
        else:
            raise ValueError("密钥长度必须是 16, 24 或 32 字节")
        
        # 设置加密模式
        if mode.upper() == 'CBC':
            iv = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
        elif mode.upper() == 'ECB':
            iv = None
            cipher = AES.new(key, AES.MODE_ECB)
        elif mode.upper() == 'CFB':
            iv = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_CFB, iv)
        elif mode.upper() == 'OFB':
            iv = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_OFB, iv)
        else:
            raise ValueError("不支持的加密模式")
        
        # 加密（CBC 模式需要填充）
        if mode.upper() == 'CBC' or mode.upper() == 'ECB':
            ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
        else:
            ciphertext = cipher.encrypt(plaintext)
        
        return ciphertext, key, iv
    
    @staticmethod
    def aes_decrypt(ciphertext, key, iv=None, mode='CBC'):
        """
        AES 解密
        :param ciphertext: 密文
        :param key: 密钥
        :param iv: 初始化向量
        :param mode: 加密模式
        :return: 解密后的明文
        """
        # 设置解密模式
        if mode.upper() == 'CBC':
            cipher = AES.new(key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        elif mode.upper() == 'ECB':
            cipher = AES.new(key, AES.MODE_ECB)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        elif mode.upper() == 'CFB':
            cipher = AES.new(key, AES.MODE_CFB, iv)
            plaintext = cipher.decrypt(ciphertext)
        elif mode.upper() == 'OFB':
            cipher = AES.new(key, AES.MODE_OFB, iv)
            plaintext = cipher.decrypt(ciphertext)
        else:
            raise ValueError("不支持的加密模式")
        
        return plaintext.decode('utf-8')
    
    # RSA 加密
    @staticmethod
    def generate_rsa_keys(key_size=2048):
        """生成 RSA 密钥对"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def rsa_encrypt(plaintext, public_key):
        """RSA 加密"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext
    
    @staticmethod
    def rsa_decrypt(ciphertext, private_key):
        """RSA 解密"""
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('utf-8')
    
    # DES 加密
    @staticmethod
    def des_encrypt(plaintext, key=None):
        """DES 加密"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        if key is None:
            key = get_random_bytes(8)
        elif len(key) != 8:
            raise ValueError("DES 密钥必须是 8 字节")
        
        iv = get_random_bytes(8)
        cipher = DES.new(key, DES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(plaintext, DES.block_size))
        return ciphertext, key, iv
    
    @staticmethod
    def des_decrypt(ciphertext, key, iv):
        """DES 解密"""
        cipher = DES.new(key, DES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), DES.block_size)
        return plaintext.decode('utf-8')
    
    # 3DES 加密
    @staticmethod
    def des3_encrypt(plaintext, key=None):
        """3DES 加密"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        if key is None:
            key = get_random_bytes(24)  # 3DES 需要 24 字节密钥
        elif len(key) not in [16, 24]:
            raise ValueError("3DES 密钥必须是 16 或 24 字节")
        
        iv = get_random_bytes(8)
        cipher = DES3.new(key, DES3.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(plaintext, DES3.block_size))
        return ciphertext, key, iv
    
    @staticmethod
    def des3_decrypt(ciphertext, key, iv):
        """3DES 解密"""
        cipher = DES3.new(key, DES3.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), DES3.block_size)
        return plaintext.decode('utf-8')
    
    # ChaCha20 加密
    @staticmethod
    def chacha20_encrypt(plaintext, key=None, nonce=None):
        """ChaCha20 加密"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        if key is None:
            key = get_random_bytes(32)
        if nonce is None:
            nonce = get_random_bytes(12)
        
        cipher = chacha20.ChaCha20(key, nonce)
        ciphertext = cipher.encrypt(plaintext)
        return ciphertext, key, nonce
    
    @staticmethod
    def chacha20_decrypt(ciphertext, key, nonce):
        """ChaCha20 解密"""
        cipher = chacha20.ChaCha20(key, nonce)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext.decode('utf-8')
    
    # 数字签名
    @staticmethod
    def sign_data(data, private_key):
        """使用私钥对数据进行签名"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    @staticmethod
    def verify_signature(data, signature, public_key):
        """使用公钥验证签名"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    # 实用工具函数
    @staticmethod
    def bytes_to_base64(data):
        """将字节数据转换为 Base64 字符串"""
        return base64.b64encode(data).decode('utf-8')
    
    @staticmethod
    def base64_to_bytes(data):
        """将 Base64 字符串转换为字节数据"""
        return base64.b64decode(data)
    
    @staticmethod
    def generate_random_key(length=32):
        """生成随机密钥"""
        return get_random_bytes(length)


# 使用示例和测试
if __name__ == "__main__":
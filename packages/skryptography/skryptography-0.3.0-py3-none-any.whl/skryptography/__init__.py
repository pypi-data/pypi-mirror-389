from pycipher import Caesar, Affine, Vigenere, Autokey, Playfair
from sympy import mod_inverse
import numpy as np
from Crypto.Cipher import DES
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.Padding import pad, unpad
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
from elgamal.elgamal import Elgamal

class AdditiveCipher:
    def __init__(self, key: int) -> None:
        self.c = Caesar(key)

    def encode(self, msg: str) -> str:
        return self.c.encipher(msg)
    
    def decode(self, msg: str) -> str:
        return self.c.decipher(msg)

class MultiplicativeCipher:
    def __init__(self, key: int) -> None:
        self.key = key

    def encode(self, msg: str) -> str:
        return ''.join(chr((ord(c)-97)*self.key%26+97) for c in msg.lower())
    
    def decode(self, enc: str) -> str:
        return ''.join(chr((ord(c)-97)*mod_inverse(self.key,26)%26+97) for c in enc.lower())
    
class AffineCipher:
    def __init__(self, key1: int, key2: int) -> None:
        self.c = Affine(key1, key2)

    def encode(self, msg: str) -> str:
        return self.c.encipher(msg)
    
    def decode(self, msg: str) -> str:
        return self.c.decipher(msg)
    
class VigenereCipher:
    def __init__(self, key: str) -> None:
        self.c = Vigenere(key)

    def encode(self, msg: str) -> str:
        return self.c.encipher(msg)
    
    def decode(self, msg: str) -> str:
        return self.c.decipher(msg)
    
class AutoKeyCipher:
    def __init__(self, key: str) -> None:
        self.c = Autokey(key)

    def encode(self, msg: str) -> str:
        return self.c.encipher(msg)
    
    def decode(self, msg: str) -> str:
        return self.c.decipher(msg)
    
class PlayfairCipher:
    def __init__(self, key1: str) -> None:
        key = key1 + ''.join([c for c in 'ABCDEFGHIKLMNOPQRSTUVWXYZ' if c not in key1])
        self.c = Playfair(key)

    def encode(self, msg: str) -> str:
        return self.c.encipher(msg)
    
    def decode(self, msg: str) -> str:
        return self.c.decipher(msg)

def mod_inv_matrix(matrix, modulus):
    det = int(round(np.linalg.det(matrix)))  # Determinant
    det_inv = pow(det, -1, modulus)  # Modular inverse of determinant
    matrix_mod_inv = (det_inv * np.round(det * np.linalg.inv(matrix)).astype(int)) % modulus
    return matrix_mod_inv.astype(int)

class HillCipher:
    def __init__(self, key1: list) -> None:
        self.key = np.array(key1)

    @staticmethod
    def pad_text(text: str, block_size: int):
        while len(text) % block_size != 0:
            text += 'X'
        return text

    def encode(self, text: str):
        n = self.key.shape[0]
        text = self.pad_text(text.upper(), self.key.shape[0])
        text = text[:len(text)//n * n]
        text_vec = np.array([ord(c) - 65 for c in text]).reshape(-1, n)
        cipher_vec = (text_vec @ self.key) % 26
        return ''.join(chr(c + 65) for c in cipher_vec.flatten())
    
    def decode(self, ciphertext: str):
        n = self.key.shape[0]
        ciphertext = ciphertext[:len(ciphertext)//n * n].upper()
        cipher_vec = np.array([ord(c) - 65 for c in ciphertext]).reshape(-1, n)
        key_inv = mod_inv_matrix(self.key, 26)
        plain_vec = (cipher_vec @ key_inv) % 26
        return ''.join(chr(c + 65) for c in plain_vec.flatten())
    
class DESCipher:

    MODE_ECB = DES.MODE_ECB

    def __init__(self, key: str, mode: int) -> None:
        self.c = DES.new(key.encode('utf-8'), mode)

    def encode(self, msg: str):
        return self.c.encrypt(pad(msg.encode('utf-8'), 8))
    
    def decode(self, msg) -> str:
        return unpad(self.c.decrypt(msg), 8).decode('utf-8')
    
class AESCipher:

    def __init__(self, key: str) -> None:
        self.c = AES.new(bytes.fromhex(key), AES.MODE_ECB)

    def encode(self, msg: str):
        return self.c.encrypt(pad(msg.encode('utf-8'), 16))
    
    def decode(self, msg) -> str:
        return unpad(self.c.decrypt(msg), 16).decode('utf-8')

class RSACipher:
    def __init__(self) -> None:
        ...

    def generate_keys(self, n, e):
        self.key = RSA.generate(n, e=e)
        print("RSA: Keys generated successfully")
    
    def encode(self, msg: str, recv: 'RSACipher'):
        return PKCS1_OAEP.new(recv.key.publickey()).encrypt(msg.encode('utf-8'))
    
    def decode(self, msg) -> str:
        return PKCS1_OAEP.new(self.key).decrypt(msg).decode('utf-8')

class ECCCipher:
    def generate_keys(self):
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        print("ECC: Keys generated successfully")
        return self.public_key, self.private_key

    def encode(self, plaintext: str, receiver: 'ECCCipher'):
        # Derive shared secret
        shared_key = self.private_key.exchange(ec.ECDH(), receiver.public_key)

        # Derive symmetric AES key
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
        ).derive(shared_key)

        # Encrypt using AES-GCM
        iv = os.urandom(12)
        encryptor = Cipher(algorithms.AES(derived_key), modes.GCM(iv)).encryptor()
        ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()

        return iv, ciphertext, encryptor.tag
    
    def decode(self, sender: 'ECCCipher', msg) -> str:
        iv, ciphertext, tag = msg
        shared_key = self.private_key.exchange(ec.ECDH(), sender.public_key)

        # Derive AES key same as encryption
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
        ).derive(shared_key)

        decryptor = Cipher(algorithms.AES(derived_key), modes.GCM(iv, tag)).decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode('utf-8')

class ElgamalCipher:
    def __init__(self) -> None:
        ...

    def generate_keys(self, key_len):
        pb, pv = Elgamal.newkeys(key_len)
        self.pg = pb
        self.pv = pv
        print("Elgamal: Keys generated successfully")

    def encode(self, msg: str, recv: 'ElgamalCipher'):
        return Elgamal.encrypt(msg.encode('utf-8'), recv.pb) # type: ignore
    
    def decode(self, ct, sender: 'ElgamalCipher') -> str:
        return Elgamal.decrypt(ct, self.pv).decode('utf-8')
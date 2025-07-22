# developer: varun pillai
# Description: Reverse engineered the code to authenticate to Tableau Server. 

import copy
import json
import Crypto
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64decode
import binascii

# Encrypt with RSA public key (it's important to use PKCS11)
def assymmetric_encrypt(val, public_key):
     modulusDecoded = int(public_key["n"], 16)
     exponentDecoded = int(public_key["e"], 16)
     keyPub = RSA.construct((modulusDecoded, exponentDecoded))
     # Generate a cypher using the PKCS1.5 standard
     cipher = PKCS1_v1_5.new(keyPub)
     return binascii.b2a_hex(cipher.encrypt(val.encode('utf-8'))).decode("utf-8")
import rsa


def encrypt(txt):
    with open("public.pem", "rb") as f:
        public_key = rsa.PublicKey.load_pkcs1(f.read())
    return rsa.encrypt(txt.encode('utf-8'), public_key).hex()


def decrypt(txt):
    with open("private.pem", "rb") as f:
        private_key = rsa.PrivateKey.load_pkcs1(f.read())
    return rsa.decrypt(bytes.fromhex(txt), private_key).decode()


def compare(compared, hashed):
    return compared == decrypt(hashed)
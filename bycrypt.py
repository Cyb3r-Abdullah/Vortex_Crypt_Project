import bcrypt
print(bcrypt.hashpw(b"hello", bcrypt.gensalt()).decode())

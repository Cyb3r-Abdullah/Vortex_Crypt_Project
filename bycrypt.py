import bcrypt

def generate_profile_hash():
    password = input("Enter your new VORTEX-CRYPT master key: ")
    if not password:
        print("Error: Password cannot be empty.")
        return

    # Generate salt and hash
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    
    print("\n" + "="*50)
    print("COPY THIS HASH INTO profile.json:")
    print(hashed.decode())
    print("="*50)

if __name__ == "__main__":
    generate_profile_hash()

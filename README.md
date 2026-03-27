


# VORTEX-CRYPT🌀
VORTEX-CRYPT is a high-performance Python security suite designed for modern file encryption and data management. Built with a sleek, dark-themed interface, it provides a centralized "Target Injection Zone" to protect sensitive files using industry-standard cryptographic protocols.
A high-performance batch encryption engine designed for **Data-at-Rest Protection** and **Anti-Forensic Security**.

## 🛡️ Security Architecture
- **Encryption Standard:** Fernet (AES-128 in CBC mode) for authenticated data confidentiality.
- **Key Derivation:** PBKDF2 with 100,000 iterations to resist brute-force attacks.
- **Identity Protection:** Bcrypt hashing with random salting for secure user authentication.
- **Anti-Forensic Module:** Custom Secure Shredding logic that overwrites file bytes with `os.urandom` entropy before deletion.

## 🚀 Features
- **Target Injection Zone:** Drag-and-drop support for files and folders.
- **System Audit:** Real-time logging of all cryptographic operations.
- **Multi-Threaded:** Smooth UI performance during heavy batch processing.

## 🛠️ Installation
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python "Encryption 2.0.py"`

Important: Do not store your plain-text password in profile.json. Use the provided bcrypt_gen.py to create a secure hash and store that instead for the first time to access admin.

*Disclaimer: This tool is for educational purposes. Always manage your cryptographic salts securely in production.*

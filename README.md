VORTEX-CRYPT v1.0: Phantom Edition
VORTEX-CRYPT is a high-performance Python security suite designed for modern file encryption and data management. Featuring a sleek, "Midnight-Purple" interface, it provides a centralized Target Injection Zone to protect sensitive files using industry-standard cryptographic protocols.

Key Features
Military-Grade Encryption: Uses the Fernet (AES-128) library for authenticated encryption, ensuring data remains inaccessible without the correct session key.

Bcrypt Access Control: Implements bcrypt for password hashing. By salting and stretching passwords, it provides robust protection against brute-force and rainbow table attacks.

Target Injection Zone: A modern UI supporting Drag & Drop for rapid file and folder queuing.

Secure Shredding: Features a 3-pass random overwrite "Secure Delete" function to prevent forensic data recovery.

System Audit Log: Maintains a real-time session log of all operations, which can be exported for security auditing.

Technical Stack
Language: Python 3.12

Security: cryptography, bcrypt

UI Framework: customtkinter, TkinterDnD2

Setup & Installation
Clone the Repository:

Bash
git clone https://github.com/yourusername/Vortex-Crypt.git
cd Vortex-Crypt
Install Dependencies:

Bash
pip install customtkinter cryptography bcrypt tkinterdnd2
Generate Your Master Key:
VORTEX-CRYPT does not store plain-text passwords. To set your access key:

Run the included bcrypt_gen.py script.

Enter your desired password to generate a secure hash.

Copy the hash into the password_hash field within profile.json.

Usage
Authenticate: Launch the app and enter your Master Key.

Add Targets: Drag and drop files or folders directly into the UI.

Process: Click Encrypt All or Decrypt All. Original files are securely shredded after encryption to ensure no traces remain.

Disclaimer: This tool is for educational and personal security purposes. Always back up your master key; encrypted data cannot be recovered without it.

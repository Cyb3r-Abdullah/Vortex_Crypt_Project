VORTEX-CRYPT v1.0: Phantom Edition
VORTEX-CRYPT is a high-performance Python security suite designed for modern file encryption and data management. Featuring a sleek, "Midnight-Purple" dark interface, it provides a centralized Target Injection Zone to protect sensitive files using industry-standard cryptographic protocols.

Core Features
AES-128 Authenticated Encryption: Utilizes the Fernet library to ensure data remains inaccessible without the correct derived session key.

Bcrypt Access Control: Implements bcrypt for password hashing. By salting and stretching passwords, it provides robust protection against brute-force and rainbow table attacks.

Target Injection Zone: A modern UI supporting Drag & Drop for rapid file and folder queuing.

Secure Shredding: Features a 3-pass random overwrite "Secure Delete" function to prevent forensic data recovery.

System Audit Log: Maintains a real-time session log of all operations, exportable for security auditing.

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
Configure Your Master Key:
VORTEX-CRYPT does not store plain-text passwords. You must generate a bcrypt hash for your profile.json file. Run the included hash generator:

Python
# Run this in a Python shell to get your hash
import bcrypt
pwd = "your_password".encode()
print(bcrypt.hashpw(pwd, bcrypt.gensalt()).decode())
Copy the output into the password_hash field within profile.json.

Usage
Launch: Run python main.py and authenticate using your Master Key.

Encrypt: Drag files into the Target Injection Zone and click Encrypt All. Original files will be securely shredded.

Decrypt: Add .crypt files to the queue and click Decrypt All.

Disclaimer: This tool is for educational and personal security purposes. Always keep a backup of your master key; encrypted data cannot be recovered without it.

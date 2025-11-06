🔐 InvCrypt CLI – Community Edition v1.0.12

Developed by Invicra Technologies AB

InvCrypt is a quantum-safe command-line encryption tool built on Invicra’s proprietary DITG (Distributed Inverted Transformation Graphs) and FTG (Field Transformation Geometry) cryptographic frameworks. It is designed to resist both classical and quantum-based attacks, providing a secure, fully offline encryption environment.

This Community Edition is a free, fully functional version distributed without exposing protected cryptographic modules. It is 100% compatible with future commercial editions and intended for research, education, and non-commercial use.

⚠️ Security Notice
This edition is intended for research, testing, and educational purposes only. It provides functional, quantum-safe local encryption but is not certified for production or for protecting classified data. Invicra Technologies AB assumes no responsibility for data loss, corruption, or misuse resulting from forgotten seeds or improper file handling. For enterprise or commercial licensing, please contact: contact@invicra.com

🧩 Overview
• Quantum-safe local file encryption and decryption
• Seed-based key generation (no key files required)
• Built-in hash functions: shake256, shake256x, blake3x
• Extended metrics and integrity verification
• Automated round-trip test (--testrun)
• Cross-platform (Windows, macOS, Linux)
• Fully functional without exposing protected modules

⚙️ Installation
From a local wheel file: pip install dist/invcrypt-1.0.11-py3-none-any.whl
From PyPI (public release): pip install invcrypt

🚀 Quickstart (Windows Binary)
You can run InvCrypt without installing Python.

Download the latest Community build from Releases on GitHub.

Unzip the file (e.g. invcrypt_community_win64_v1.0.11.zip).

In your terminal:
set PATH=%PATH%;%CD%\invcrypt
invcrypt.exe --info
invcrypt.exe file.txt --seed demo
No installation or dependencies required.

🐳 Run InvCrypt via Docker
Use InvCrypt Community Edition directly from DockerHub — no installation required.
Encrypt: docker run --rm -v ${PWD}:/data ivarolsson1415/invcrypt:latest /data/file.txt -o /data/file.txt.invx --seed "mypassword"
Decrypt: docker run --rm -v ${PWD}:/data ivarolsson1415/invcrypt:latest /data/file.txt.invx -o /data/file.txt --seed "mypassword"
DockerHub: https://hub.docker.com/r/ivarolsson1415/invcrypt

GitHub Repository: https://github.com/ivarolsson1415/invcrypt-community

🔧 Usage Examples
Encrypt a file: invcrypt file.txt --seed mypass
Decrypt a file: invcrypt file.txt.invx --seed mypass
Prompt for password: invcrypt file.txt -p
Full encrypt/decrypt test: invcrypt --testrun file.txt --seed testseed
Display help and options: invcrypt --info

🧠 Seed Warning
Your seed (password) is the only key required to encrypt and decrypt files. If it is lost, your data cannot be recovered. InvCrypt does not store, transmit, or recover seeds under any circumstances.

🧮 Available Hash Functions
shake256: 512 classical bits, 256 quantum bits, Stable
shake256x: 1024 classical bits, 512 quantum bits, Stable
blake3x: 1024 classical bits, 512 quantum bits, Fast

🔒 Security Architecture
InvCrypt is built upon Invicra’s proprietary mathematical frameworks:
DITG – Distributed Inverted Transformation Graphs
FTG – Field Transformation Geometry
Protected modules (matrix, crypto_core, hashing, utils) are distributed as compiled .pyc files and cannot be reverse-engineered.

🧱 System Requirements
Python 3.12 or later
Operating Systems: Windows, macOS, Linux
Dependencies: tqdm, colorama

📁 Project Structure
invcrypt/
├── cli_args.py
├── config.py
├── constants.py
├── info.py
├── loader.py
├── main.py
├── metrics.py
└── pycache/ (protected modules)

☁️ Example: Encrypt & Upload to S3
This example shows how to use InvCrypt CLI to encrypt a file and upload it to Amazon S3.
pip install boto3
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=...
export AWS_S3_BUCKET=your-bucket
export INVCRYPT_SEED=your-seed
python examples/s3_encrypt.py
Note: The Community Edition uses a simplified seed-based key system for demonstration only. Production deployments require Pro or Business versions.

🧩 Verify Your Build (Developers)
After building the binary (pyinstaller invcrypt.spec):
set PATH=%PATH%;%CD%\dist\invcrypt
invcrypt.exe --info
invcrypt.exe --hashlist
invcrypt.exe file.txt --seed demo
You should see a generated file.txt.invx confirming the CLI works.

📄 License
Invicra Community License 2025
This software may be used freely for personal, academic, or non-commercial testing. Commercial or enterprise deployment requires a separate license from Invicra Technologies AB.

🏢 About Invicra Technologies AB
Invicra Technologies develops next-generation post-quantum cryptographic systems based on proprietary mathematical frameworks (DITG, FTG, IUHMF). The company focuses on data security, AI safety, and quantum-era encryption.
Contact: contact@invicra.com

Website: (launching 2025)

© 2025 Invicra Technologies AB — All rights reserved.
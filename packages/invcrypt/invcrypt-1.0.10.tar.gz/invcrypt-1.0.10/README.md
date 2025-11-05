InvCrypt CLI – Community Edition v1.0.9

Developed by Invicra Technologies AB

InvCrypt is a quantum-safe command-line encryption tool built on Invicra’s proprietary DITG and FTG cryptographic frameworks.
It is designed to resist both classical and quantum-based attacks, providing a secure, fully offline encryption environment.

This Community Edition is a free, fully functional version distributed without exposing the protected cryptographic modules.
It is 100% compatible with future commercial editions and intended for research, education, and non-commercial use.

Security Notice

This edition is provided for research and educational purposes.
It provides functional, quantum-safe local encryption but is not certified for production environments or for protecting classified data.

Invicra Technologies AB assumes no responsibility for data loss or misuse resulting from forgotten seeds or improper file handling.
For enterprise or commercial licensing, please contact contact@invicra.com
.

Overview

Quantum-safe local file encryption and decryption

Seed-based key generation (no key files required)

Built-in hash functions: shake256, shake256x, blake3x

Extended metrics and integrity verification

Automated round-trip test (--testrun)

Cross-platform support (Windows, macOS, Linux)

Fully functional without exposing source code

Installation
From a local wheel file
pip install dist/invcrypt-1.0.9-py3-none-any.whl

From PyPI (public release)
pip install invcrypt

Usage Examples
Encrypt a file
invcrypt file.txt --seed mypass

Decrypt a file
invcrypt file.txt.invx --seed mypass

Prompt for password
invcrypt file.txt -p

Full encrypt/decrypt test
invcrypt --testrun file.txt --seed testseed

Display help and options
invcrypt --info

Seed Warning

Your seed (password) is the only key required to encrypt and decrypt files.
If it is lost, your data cannot be recovered.
InvCrypt does not store, transmit, or recover seeds under any circumstances.

Available Hash Functions
Name	Classical Bits	Quantum Bits	Performance
shake256	512	256	Stable
shake256x	1024	512	Stable
blake3x	1024	512	Fast
Security Architecture

InvCrypt is built upon Invicra’s proprietary mathematical frameworks:

DITG – Distributed Inverted Transformation Graphs

FTG – Field Transformation Geometry

Protected modules (matrix, crypto_core, hashing, utils) are distributed as compiled .pyc files and cannot be reverse-engineered.

System Requirements

Python: 3.12 or later

Operating Systems: Windows, macOS, Linux

Dependencies: tqdm, colorama

Project Structure
invcrypt/
 ├── cli_args.py
 ├── config.py
 ├── constants.py
 ├── info.py
 ├── loader.py
 ├── main.py
 ├── metrics.py
 └── __pycache__/   (protected modules)

License

Invicra Community License 2025

This software may be used freely for personal, academic, or non-commercial testing.
Commercial or enterprise deployment requires a separate license from Invicra Technologies AB.

About Invicra Technologies AB

Invicra Technologies develops next-generation post-quantum cryptographic systems based on proprietary mathematical frameworks (DITG, FTG, IUHMF).
The company focuses on data security, AI safety, and quantum-era encryption.

Contact: contact@invicra.com

Website: (launching 2025)
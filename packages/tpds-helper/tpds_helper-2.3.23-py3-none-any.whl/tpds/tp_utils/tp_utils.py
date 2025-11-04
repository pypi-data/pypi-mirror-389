# -*- coding: utf-8 -*-
# 2019 to present - Copyright Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR
# PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT, SPECIAL,
# PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE OF ANY
# KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP
# HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE FORESEEABLE. TO THE
# FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN
# ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
# THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.

import struct
import subprocess
from collections import namedtuple
from zipfile import ZipFile

import cryptography
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.utils import int_to_bytes


def run_subprocess_cmd(cmd, sys_shell=False, sys_newlines=True):
    """
    Runs a command on ternimal/command prompt. Uses subprocess module.

    Inputs:
        cmd                     Command to be processed
        sys_shell               If True, the command will be executed through
                                the shell.
        sys_newlines            If True, stdout and stderr are opened
                                as text files, all
                                line terninations are seen as '\n'
                                by the python program

    Outputs:
        Returns a namedtuple of ['returncode', 'stdout', 'stderr']

        returncode              Returns error code from terminal
        stdout                  All standard outputs are accumulated here.
        srderr                  All error and warning outputs

    Examples:
        To run "python test.py -f sheet.csv"
        subProcessOut = syshelper.run_subprocess_cmd(
            [sys.executable, "test.py", "-f", "sheet.csv"])
        print(subProcessOut.stdout)
        print(subProcessOut.stderr)
        print(subProcessOut.returncode)
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=sys_newlines,
        shell=sys_shell,
    )
    stdout, stderr = proc.communicate()
    subProcessOut = namedtuple("subProcessOut", ["returncode", "stdout", "stderr"])
    return subProcessOut(proc.returncode, stdout, stderr)


def pretty_print_hex(a, li=16, indent=""):
    """
    Format a list/bytes/bytearray object into a formatted ascii hex string
    """
    lines = []
    a = bytearray(a)
    for x in range(0, len(a), li):
        lines.append(indent + " ".join(["{:02X}".format(y) for y in a[x : x + li]]))
    return "\n".join(lines)


def get_c_hex_bytes(value):
    """
    Convert the given input into hex bytes
    Inputs:
            value          value input which converted into hex bytes
    Outputs:
            hex_bytes      converted hex bytes
    """
    hex_bytes = ""
    for x in range(0, len(value), 16):
        hex_bytes += "".join(["0x%02X, " % y for y in value[x : x + 16]]) + "\n"
    return hex_bytes


def pretty_xml_hex_array(data, indent="            ", bytes_per_line=32):
    """
    Convert the data into print format for provisioning XML

    Args:
        data (str): original data to be formatted
        indent (str, optional): Indentation to add for alignment.
                        Defaults to '            '.
        bytes_per_line (int, optional): Number of bytes per line*2.
                        Defaults to 32.

    Returns:
        [str]: Formatted data to insert in XML
    """
    lines = []
    for i in range(0, len(data), bytes_per_line):
        line_data = "".join([f"{v}" for v in data[i : i + bytes_per_line]])
        line_data = " ".join(line_data[i : i + 2] for i in range(0, len(line_data), 2))
        lines.append(indent + line_data)
    return "\n".join(lines)


def sign_on_host(digest, private_key):
    """
    Sign the digest using private key
    Inputs:
          digest         digest to be signed
          private_key    private key sign the digest
    Outputs:
          signature      signature of the digest
    """
    if len(digest) is not int(32):
        raise ValueError("Digest must be 32 bytes")

    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise ValueError("Invalid private key received")

    signature = private_key.sign(digest, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
    (r, s) = utils.decode_dss_signature(signature)
    signature = int_to_bytes(r, 32) + int_to_bytes(s, 32)

    return signature


def extract_zip_archive(zip_archive, dest_folder=""):
    """
    Extracts the files from zip_archive to store in dest_folder

    Args:
        zip_archive (Path): Zip file path to extract
        dest_folder (str, optional): Destination folder to save the files
                                        . Defaults to ''.
    """
    with ZipFile(zip_archive) as zf:
        zf.extractall(dest_folder)


def add_to_zip_archive(zip_archive, files=[]):
    """
    Adds files from list provided to zip_archive

    Args:
        zip_archive ([type]): Zip file path to add the files
        files (list, optional): list of files to add to Zip. Defaults to [].
    """
    with ZipFile(zip_archive, "w") as zf:
        for file in files:
            zf.write(file)


def calculate_wpc_digests(root_bytes, mfg_bytes, puc_bytes):
    """
    Calculates WPC Chain digest based on root, mfg and puc bytes

    Input(s):
        root_bytes ([bytes])
        mfg_bytes ([bytes])
        puc_bytes ([bytes])
    Output:
        signature      Chain digest of WPC certificates
    """
    hash_backend = cryptography.hazmat.backends.default_backend()

    root_hash = hashes.Hash(hashes.SHA256(), backend=hash_backend)
    root_hash.update(root_bytes)
    root_digest = root_hash.finalize()[:32]

    length = 2 + len(root_digest) + len(mfg_bytes) + len(puc_bytes)
    cert_chain = b""
    cert_chain += struct.pack(">H", length)
    cert_chain += root_digest + mfg_bytes + puc_bytes
    chain_hash = hashes.Hash(hashes.SHA256(), backend=hash_backend)
    chain_hash.update(cert_chain)
    chain_digest = chain_hash.finalize()[:32]

    return {"root_digest": root_digest, "chain_digest": chain_digest}


__all__ = [
    "run_subprocess_cmd",
    "pretty_print_hex",
    "get_c_hex_bytes",
    "pretty_xml_hex_array",
    "sign_on_host",
    "extract_zip_archive",
    "add_to_zip_archive",
    "calculate_wpc_digests",
]

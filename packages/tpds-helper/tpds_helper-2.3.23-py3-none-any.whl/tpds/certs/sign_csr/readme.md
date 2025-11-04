# Instructions to generate the Signer certificates from CSRs

This package contains the required scripts and files to perform sign operation of the CSRs provided by Microchip.

These are python scripts and hence required to have Python 3.7 or higher version installed in the user system.

1. This package contains requirements.txt file which can be used to install the required python packages. Run the following command to install the packages.

```
    python -m pip install requirements.txt
```

2. Once the packages are installed, run the following command to understand the arguments to be passed.

```
    python sign_csr.py --help
```

3. Extract the CSRs zip file provided by Microchip Provisioning Services. Use this path as --in-path

4. Create a folder to store the generated signer certificates. Use this path as --out-path

5. Provide the signer CA key to sign the CSRs as --cakey.

   Following is the example command for reference

   ```
       python sign_csr.py --in-path test_csrs --out-path test_csrs_out --cakey signer_ca.key
   ```

6. This should generate signers signed by signer_ca in --out-path folder. Zip this folder and share to Microchip Provisioning Services along with Provisioning package generated on TPDS Configurator.

This concludes the Signers generation process from CSRs.

from enum import Enum


class KeyAlgorithms(str, Enum):
    ECC_P256 = "ECC_P256"
    ECC_P224 = "ECC_P224"
    ECC_P384 = "ECC_P384"
    RSA_1024 = "RSA_1024"
    RSA_2048 = "RSA_2048"
    RSA_3072 = "RSA_3072"
    HMAC_SHA256 = "HMAC_SHA256"
    ECC_SECP256_K1 = "ECC_SECP256K1"
    ECC_BRAINPOOL_P256_R1 = "ECC_Brainpool_P256R1"
    AES128 = "AES128"

# (c) Copyright (c) 2018-2023 Microchip Technology Inc. and its subsidiaries.
#
# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.
#
# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A
# PARTICULAR PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT,
# SPECIAL, PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE
# OF ANY KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF
# MICROCHIP HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE
# FORESEEABLE. TO THE FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL
# LIABILITY ON ALL CLAIMS IN ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED
# THE AMOUNT OF FEES, IF ANY, THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR
# THIS SOFTWARE.
import json
import os
from typing import Optional

from fastapi import File, UploadFile, Body
from fastapi.routing import APIRouter
from pydantic import BaseModel
from tpds.settings import TrustPlatformSettings
from tpds.helper import log
from tpds.device_manifest.manifest import Manifest
from tpds.device_manifest.generate_manifest_data import get_secure_element_data
from tpds.cert_tools.cert import Cert

homePath = TrustPlatformSettings().get_base_folder()
router = APIRouter()


class ResponseModel(BaseModel):
    status: bool = False
    message = ""


@router.post("/decode/")
async def manifest_decode(
    manifest_file: UploadFile = File(...), certificate_file: Optional[UploadFile] = File(None)
):
    try:
        manifest = json.load(manifest_file.file)

        certificate_list = []
        cert = Cert()
        if certificate_file:
            # custom certificate
            contents = await certificate_file.read()
            cert.set_certificate(contents)
            certificate_list.append(cert.certificate)
        else:
            # MCHP signer certificates
            path = os.path.join(os.path.dirname(__file__), "MCHP_manifest_signer")
            for cert_file in os.listdir(path):
                cert.set_certificate(os.path.join(path, cert_file))
                certificate_list.append(cert.certificate)

        result = None
        for certificate in certificate_list:
            try:
                result = Manifest.decode_manifest(manifest, certificate)
                break  # Since the verification is complete, breaking the loop
            except Exception as e:
                log(f"Manifest decoding is failed with: {e}")

        if result is None:
            return {
                "message": "Verification is failed",
                "data": "Verification of SignedSecureElement objects failed. Check Manifest Signer Certificate and try again.",
            }
        return {"message": "Success", "data": json.dumps(result)}

    except Exception as exp:
        return {"message": "Error", "data": f"Manifest decoding is failed with: {exp}"}


@router.post("/generate")
def manifest_generate(user_inputs=Body()):
    response = ResponseModel()
    unsupported_deviecs = ["CEC1734", "CEC1736", "PIC32CKSG01", "PIC32CMLS60", "PIC32CXSG41", "PIC32CZCA90"]
    cwd = os.getcwd()
    manifest_dir = os.path.join(homePath, "device_manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    os.chdir(manifest_dir)
    try:
        device = user_inputs.get("device", None)
        interface = user_inputs.get("interface", None)
        address = user_inputs.get("address", None)
        assert device, "Please Select Device For Manifest Generation"
        assert device not in unsupported_deviecs, f"Manifest Generation is not Supported for {device.upper()}"
        se = get_secure_element_data(
            device=device,
            interface=interface,
            address=address,
        )
        se.update({"PartNumber": f"{device}-Proto"})
        sn = se.get("UniqueID")
        manifest = Manifest()
        manifest.generate_manifest_json(se)
        manifest.encode_manifest(uniqueId=sn)
        manifest_file = f"{device.upper()}_{sn}.json"
        manifest.write_signed_se_into_file(manifest_file)
        response.status = True
        response.message = f"Generated Manifest Saved in {os.path.abspath(manifest_file)}"
    except Exception as e:
        response.status = False
        response.message = f"Manifest Generation Failed with error: {e}"
    finally:
        os.chdir(cwd)
    return response

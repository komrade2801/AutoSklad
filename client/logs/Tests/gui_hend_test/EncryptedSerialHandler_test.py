# На устройстве A
from BarcodeScanner.EncryptedSerialHandler import EncryptedSerialHandler

handler_a = EncryptedSerialHandler("COM30")
handler_a.send_encrypted(
    command_code=0x01,
    data=b"Sensitive data"
)

# На устройстве B (должен использовать те же ключи!)
handler_b = EncryptedSerialHandler("COM29",
    encryption_key=handler_a.fernet._signing_key,
    hmac_key=handler_a.hmac_key
)

response = handler_b.receive_encrypted()
print(f"Received: {response}")

import pyotp
def gen_secret():
    secret_key = pyotp.random_base32()
    return secret_key

def secret_now(secret):
    totp = pyotp.TOTP(secret)
    return totp.now()


def verify_consecutive_totp(secret, user_code, window=1):
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(user_code, valid_window=window)
    return is_valid
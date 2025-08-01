from itsdangerous import URLSafeTimedSerializer
salt = 'otpverify'
def entoken(data):
    serializer = URLSafeTimedSerializer('parthiv@29')
    return serializer.dumps(data,salt=salt)

def dntoken(data):
    serializer = URLSafeTimedSerializer('parthiv@29')
    return serializer.loads(data,salt=salt)
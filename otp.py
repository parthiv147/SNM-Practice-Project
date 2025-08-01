import random
def generate_otp():
    otp=''
    u_1=[chr(i) for i in range(ord('A'),ord('Z')+1)]  
    u_2=[chr(i) for i in range(ord('a'),ord('z')+1)]
    for i in range(2):
        otp+=random.choice(u_1)
        otp+=random.choice(u_2)
        otp+=str(random.randint(0,9))
    return otp

    
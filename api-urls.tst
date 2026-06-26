http://127.0.0.1:8000/auth/login/
{
    "username":"gauravdhale",
    "password":"GRD@test09"
}

http://127.0.0.1:8000/auth/roles/
{
    "name":"Superadmin"
}
http://127.0.0.1:8000/auth/roles/2/
{
    "access_pages":[1,2]
}

http://127.0.0.1:8000/auth/pages/
{
    "name":"Dashboard"
}

http://127.0.0.1:8000/auth/register/
{
    "email":"gkaple15@gmail.com",
    "password":1234,
    "confirm_password":1234,
    "role":1
}

http://127.0.0.1:8000/auth/verify-email/

{
    "email":"gkaple150@gmail.com"
}
http://127.0.0.1:8000/auth/send-otp/
{
    "email":"gkaple150@gmail.com"
}
http://127.0.0.1:8000/auth/verify-otp/
{
    "email":"gkaple150@gmail.com",
    "otp":632148
}
http://127.0.0.1:8000/auth/forgot-password/
{
    "email":"gkaple150@gmail.com",
    "new_password":123456,
    "confirm_password":123456
}

http://127.0.0.1:8000/auth/forgot-password/
{
    "email":"gkaple15@gmail.com",
    "new_password":"123456",
    "confirm_password":"123456"
}


tell developer following instructions
1. copy paste the app authenticate into his project entirely
2. run migrate command
3. copy paste lines (from line no. 114) of settings.py of my project to his project
4. add important credentials to env


#### totp flow 

1. GET : http://127.0.0.1:8000/auth/totp/setup/  (fetced by logged in user only)

Response : 
{"secret":"PWCO3A5P5LBGJ4JR5REUX6CSAGH7KGGK","qr_uri":"otpauth://totp/ClaimsPortal:gauravdhale7404?secret=PWCO3A5P5LBGJ4JR5REUX6CSAGH7KGGK&issuer=ClaimsPortal","qr_image":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAeoAAAHqAQAAAADjFjCXAAAEM0lEQVR4nO2dS26kShBFTzyQaghSL8BLgR30klq9JO8AluIFWEqGLYHuG+SHz6wL3rNLRAzKUHCUhRSKzLiRhE2csPGfMzQ47rjjjjvuuOOOO34tbsnqeJS+a8F6FoOpLkf51v660R2/Kd5JkgJoaGYY28U0sJgGwHqAsa1kPZUkSXv85OiO3wyv09+phe4d6D5qLH6EBcafnwhmBEu82aCarxnd8Xvi9eHcuneARjBaJYOHGH9+1oJKMF06uuOOAzC+zWgA6AIAi6UL7f8wuuO3whsp+hpTHdd1Zu1idJJgesh6lphDSJqP+MnRHb8lPpqZWQt0oZL9+niILlSK6euvAHQfDwGLrWnuN/nxjr8aHtd1u7LYYvFjfJvThAszGtuKuOC7bnTH74xbD1g/mRGThjjhLqZhqrG+6HUlJlp/3eiO3w0nym8KkNZwVEqJRCNJyslFvCCJTnNS+IaXfnbHvwonab6Nkq91a6oQo97MxgkHqph1RF91r3P8NN7MwPRIAa+IJhqaGQ0sRhfA+sZzWMdPWQpa8aTKUS/Oq1UMbimbbXLRTHGa9Vjn+LO28aHof81Mcq5ALtBmJ0xMU25+6Wd3/Kvwsq6bo1SX1nVxDj1EuBkpVJJC5bHO8Wtw/X5LvrZxs4FVV3nIeoga3uWjO34jPMc6SIFsKAJJupo9rAslr2hmz2EdP2NpXReySkLWRrKGUkTjZrctwGdYx5+2stNpMTE9ZN37j/iFxjYoXQCMBohb69btTi/97I5/FZ7rsBMYzR8jfQRgMsT0Q0YToHuvMZpP21ZiX/rZHf8qvFTEUh0s6SWBTb4ar24LtPgM6/gZyypxqX6p6HWrfFdE433C4V7n+HN2qE1sHY41wyihT6uu517n+Ek8KyJmb5KZ1Wyk4i6Q9hf3uUCR/PR7/HjHXwzfKCe5DnYoUECszbKX6lyvc/x5yypxJQ0bWa7aeuIAafddlOoCnk04fsbW6n86DeTtJvsS7OHUY53jJ/FNNIvW/DHrpzrWXC2u5uKplLsAXDa643fDN3tOjrKcQr7nsKG9REePdY4/Z9tsorgUJVUtyUX2Scg3u9c5/qztahMlfc1SndZddUNTjgrmXuf4GTxWX7f762KfHWths+dzbJd4n/VXju74vfD9XmI4yidRqttVKXIQ9Fjn+LOmvSXnarQpy+bTVWHxipjj5/G1V+fGuo+H9NtqIDYFSF07c7Ony0Z3/KZ4pywBD9NDdB81m7VetzYAaGZ/b8Lxs/ixV6fBYqmTDsSGnRoNYjuxdFTPumR0x++JF70O1sJrqvSXbBbIhdeca/i6zvFL8UoayluIUDpk27Gb7H8yuuM3wHfv/q8bhUOqzaa4FvJRIjzWOX7KcgkMYNPTZN3LnitiQ7Pt/eR6nePP2+6Nr782/+91jjvuuOOOO+64498F/xc6UN0FP3l7VAAAAABJRU5ErkJggg=="}

Scan the above embedded image QR code from authenticator app and setup on your device 

2. POST : http://127.0.0.1:8000/auth/totp/enable/ (enable the 2FA)

payload : 
{
    totp_code" : 594037
}
Response : {"message":"TOTP enabled successfully."}


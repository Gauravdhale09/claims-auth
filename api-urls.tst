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

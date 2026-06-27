from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.core import signing
import pyotp
import qrcode
import base64
import io
import random

from .models import PortalUser, PortalRoles, PortalPages, EmailOTP
from .ser import (
    PortalUserSerializer, PortalUserShowSerializer, RegisterSaveSerializer,
    PortalRolesSerializer, PortalPagesSerializer, EmailSerializer, OTPVerifySerializer
)
from utils import send_mail

MSG_ID_REQUIRED = "ID is required"


def _send_2fa_enabled_email(user):
    if not user.email:
        return
    subject = "Two-Factor Authentication Enabled"
    message = (
        f"Dear {user.username},\n\n"
        f"Two-Factor Authentication (2FA) has been successfully enabled on your Claims Portal account.\n\n"
        f"What this means:\n"
        f"  - Every login will now require a one-time code in addition to your password.\n"
        f"  - This adds an extra layer of security to protect your account.\n\n"
        f"If you did not make this change, please contact the administrator immediately and change your password.\n\n"
        f"Best regards,\n"
        f"Claims Portal Team"
    )
    send_mail(subject=subject, message=message, recipients=user.email)


def _send_2fa_disabled_email(user):
    if not user.email:
        return
    subject = "Two-Factor Authentication Disabled"
    message = (
        f"Dear {user.username},\n\n"
        f"Two-Factor Authentication (2FA) has been disabled on your Claims Portal account.\n\n"
        f"Your account is now protected by your password alone.\n\n"
        f"If you did not make this change, your account may be compromised. "
        f"Please contact the administrator immediately and change your password.\n\n"
        f"Best regards,\n"
        f"Claims Portal Team"
    )
    send_mail(subject=subject, message=message, recipients=user.email)
MSG_PERMISSION_DENIED = "Permission denied."


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superadmin


class PortalUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        query = PortalUser.objects.filter(is_superuser=False)
        if pk is not None:
            user = query.filter(id=pk).first() if isinstance(pk, int) else query.filter(username=pk.lower()).first()
            if not user:
                return Response({"message": "Portal User not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"data": PortalUserShowSerializer(user).data}, status=status.HTTP_200_OK)
        if not request.user.is_superadmin:
            return Response({"message": MSG_PERMISSION_DENIED}, status=status.HTTP_403_FORBIDDEN)
        users = query.order_by("created_at")
        return Response({"data": PortalUserShowSerializer(users, many=True).data}, status=status.HTTP_200_OK)

    def put(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_superadmin:
            return Response({"message": MSG_PERMISSION_DENIED}, status=status.HTTP_403_FORBIDDEN)
        user = PortalUser.objects.filter(id=pk).first()
        if not user:
            return Response({"message": "Portal User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PortalUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            return Response({"message": "Portal User updated successfully", "data": PortalUserShowSerializer(updated_user).data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_superadmin:
            return Response({"message": MSG_PERMISSION_DENIED}, status=status.HTTP_403_FORBIDDEN)
        user = PortalUser.objects.filter(id=pk).first()
        if not user:
            return Response({"message": "Portal User not found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({"message": "Portal User deleted successfully"}, status=status.HTTP_200_OK)


def _issue_jwt(request, user):
    login(request, user)
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": "User logged in successfully.",
        "refresh_token": str(refresh),
        "access_token": str(refresh.access_token),
        "logged_user": PortalUserShowSerializer(user).data
    }, status=status.HTTP_200_OK)

from django.db.models import Q
class UserLoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"message": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        

        user = PortalUser.objects.filter(
            Q(username=username) | Q(email=username)
        ).first()
        if user and user.check_password(password):
            if not user.status:
                return Response({"message": "Authentication error: You are no longer an active user."}, status=status.HTTP_400_BAD_REQUEST)
            if user.totp_enabled:
                totp_token = signing.dumps({"user_id": user.id}, salt="totp-login")
                return Response({"requires_totp": True, "totp_token": totp_token}, status=status.HTTP_200_OK)
            return _issue_jwt(request, user)
        return Response({"message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, *args, **kwargs):
        roles = PortalRolesSerializer(PortalRoles.objects.all(), many=True)
        return Response({"roles": roles.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = RegisterSaveSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully", "data": PortalUserShowSerializer(user).data}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PortalRolesView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            role = PortalRoles.objects.filter(id=pk).first()
            if not role:
                return Response({"message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"data": PortalRolesSerializer(role).data}, status=status.HTTP_200_OK)
        roles = PortalRoles.objects.all()
        return Response({"data": PortalRolesSerializer(roles, many=True).data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({"message": "Role name is required"}, status=status.HTTP_400_BAD_REQUEST)
        if PortalRoles.objects.filter(name__iexact=name).exists():
            return Response({"message": "Role already exists"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PortalRolesSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response({"message": "Role created successfully", "data": PortalRolesSerializer(role).data}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        role = PortalRoles.objects.filter(id=pk).first()
        if not role:
            return Response({"message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        name = request.data.get('name')
        if name is not None:
            name = name.strip()
            if not name:
                return Response({"message": "Role name is required"}, status=status.HTTP_400_BAD_REQUEST)
            if PortalRoles.objects.filter(name__iexact=name).exclude(id=pk).exists():
                return Response({"message": "Role already exists"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PortalRolesSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            updated_role = serializer.save()
            return Response({"message": "Role updated successfully", "data": PortalRolesSerializer(updated_role).data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        role = PortalRoles.objects.filter(id=pk).first()
        if not role:
            return Response({"message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        if role.name.lower() == 'superadmin':
            return Response({"message": "Cannot delete the superadmin role"}, status=status.HTTP_400_BAD_REQUEST)
        role.delete()
        return Response({"message": "Role deleted successfully"}, status=status.HTTP_200_OK)


class PortalPagesView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            page = PortalPages.objects.filter(id=pk).first()
            if not page:
                return Response({"message": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"data": PortalPagesSerializer(page).data}, status=status.HTTP_200_OK)
        pages = PortalPages.objects.all()
        return Response({"data": PortalPagesSerializer(pages, many=True).data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = PortalPagesSerializer(data=request.data)
        if serializer.is_valid():
            page = serializer.save()
            return Response({"message": "Page created successfully", "data": PortalPagesSerializer(page).data}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        page = PortalPages.objects.filter(id=pk).first()
        if not page:
            return Response({"message": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PortalPagesSerializer(page, data=request.data, partial=True)
        if serializer.is_valid():
            updated_page = serializer.save()
            return Response({"message": "Page updated successfully", "data": PortalPagesSerializer(updated_page).data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        page = PortalPages.objects.filter(id=pk).first()
        if not page:
            return Response({"message": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
        page.delete()
        return Response({"message": "Page deleted successfully"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    old = request.data.get('old_password')
    
    new = request.data.get('new_password')
    confirm = request.data.get('confirm_password')
    if not old or not new or not confirm:
        return Response({"message": "old_password, new_password and confirm_password are required."}, status=status.HTTP_400_BAD_REQUEST)
    old, new, confirm = str(old), str(new), str(confirm)
    print(old,new,confirm)
    if new != confirm:
        return Response({"message": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)
    if not user.check_password(old):
        return Response({"message": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user.password = make_password(new)
        user.save()
        send_mail(
            subject="Password Changed Successfully",
            message=f"Hello {user.username},\n\nYour password has been changed successfully.\n\nIf you did not initiate this change, please contact support immediately.",
            recipients=user.email
        )
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"message": "Unable to update password."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def verify_email(request):
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        if PortalUser.objects.filter(email=email).exists():
            return Response({"message": "Email exists"}, status=status.HTTP_200_OK)
        return Response({"message": "Email does not exist"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def send_otp(request):
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        user = PortalUser.objects.filter(email=email).first()
        if not user:
            return Response({"message": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
        otp = str(random.randint(100000, 999999))
        print("otp=",otp)
        EmailOTP.objects.update_or_create(user=user, defaults={"otp": otp, "is_verified": False})
        send_mail(subject="Your OTP Code", message=f"Your OTP is {otp}", recipients=email)
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def verify_otp(request):
    serializer = OTPVerifySerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        try:
            user = PortalUser.objects.get(email=email)
            email_otp = EmailOTP.objects.get(user=user)
            if email_otp.otp == otp:
                email_otp.is_verified = True
                email_otp.save()
                return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        except (PortalUser.DoesNotExist, EmailOTP.DoesNotExist):
            return Response({"message": "User or OTP not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def forgot_password(request):
    serializer = EmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data['email']
    user = PortalUser.objects.filter(email=email).first()
    if not user:
        return Response({"message": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
    otp_record = EmailOTP.objects.filter(user=user, is_verified=True).first()
    if not otp_record:
        return Response({"message": "OTP verification required before resetting password."}, status=status.HTTP_400_BAD_REQUEST)
    new = request.data.get('new_password')
    confirm = request.data.get('confirm_password')
    if not new or not confirm:
        return Response({"message": "new_password and confirm_password are required."}, status=status.HTTP_400_BAD_REQUEST)
    new, confirm = str(new), str(confirm)
    if new != confirm:
        return Response({"message": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user.password = make_password(new)
        user.save()
        otp_record.is_verified = False
        otp_record.save()
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"message": "Unable to update password."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def check_username_availability(request, username):
    if PortalUser.objects.filter(username=username).exists():
        return Response({"message": False}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": True}, status=status.HTTP_200_OK)


class TOTPSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.totp_secret:
            user.totp_secret = pyotp.random_base32()
            user.save(update_fields=["totp_secret"])
        totp = pyotp.TOTP(user.totp_secret)
        qr_uri = totp.provisioning_uri(name=user.username, issuer_name="ClaimsPortal")

        img = qrcode.make(qr_uri)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            "secret": user.totp_secret,
            "qr_uri": qr_uri,
            "qr_image": f"data:image/png;base64,{qr_base64}",
        }, status=status.HTTP_200_OK)


class TOTPEnableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        totp_code = request.data.get("totp_code")
        if not totp_code:
            return Response({"message": "totp_code is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.totp_secret:
            return Response({"message": "TOTP setup not initiated. Call GET /totp/setup/ first."}, status=status.HTTP_400_BAD_REQUEST)
        if not pyotp.TOTP(user.totp_secret).verify(str(totp_code), valid_window=1):
            return Response({"message": "Invalid TOTP code."}, status=status.HTTP_400_BAD_REQUEST)
        user.totp_enabled = True
        user.save(update_fields=["totp_enabled"])
        _send_2fa_enabled_email(user)
        return Response({"message": "TOTP enabled successfully."}, status=status.HTTP_200_OK)
    


class TOTPDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        totp_code = request.data.get("totp_code")
        if not totp_code:
            return Response({"message": "totp_code is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.totp_enabled or not user.totp_secret:
            return Response({"message": "TOTP is not enabled."}, status=status.HTTP_400_BAD_REQUEST)
        if not pyotp.TOTP(user.totp_secret).verify(str(totp_code), valid_window=1):
            return Response({"message": "Invalid TOTP code."}, status=status.HTTP_400_BAD_REQUEST)
        user.totp_enabled = False
        user.totp_secret = None
        user.save(update_fields=["totp_enabled", "totp_secret"])
        _send_2fa_disabled_email(user)
        return Response({"message": "TOTP disabled successfully."}, status=status.HTTP_200_OK)


class TOTPLoginVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        totp_token = request.data.get("totp_token")
        totp_code = request.data.get("totp_code")
        if not totp_token or not totp_code:
            return Response({"message": "totp_token and totp_code are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = signing.loads(totp_token, salt="totp-login", max_age=300)
        except signing.SignatureExpired:
            return Response({"message": "TOTP session expired. Please log in again."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
            return Response({"message": "Invalid TOTP token."}, status=status.HTTP_400_BAD_REQUEST)
        user = PortalUser.objects.filter(id=payload.get("user_id")).first()
        if not user or not user.totp_secret:
            return Response({"message": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
        if not pyotp.TOTP(user.totp_secret).verify(str(totp_code), valid_window=1):
            return Response({"message": "Invalid TOTP code."}, status=status.HTTP_401_UNAUTHORIZED)
        return _issue_jwt(request, user)

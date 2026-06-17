from django.db import models
from django.contrib.auth.models import AbstractUser


class PortalPages(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'PortalPages'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().lower()
        super().save(*args, **kwargs)


class PortalRoles(models.Model):
    name = models.CharField(max_length=255, unique=True)
    access_pages = models.ManyToManyField(PortalPages, blank=True)

    class Meta:
        db_table = 'PortalRoles'

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PortalUser(AbstractUser):
    role = models.ForeignKey(PortalRoles, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.BooleanField(default=True)
    temp_password = models.CharField(max_length=10,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Portal User"
        verbose_name_plural = "Portal Users"
        db_table = 'PortalUser'
        ordering = ['username']

    @property
    def is_superadmin(self):
        return self.is_superuser or (self.role is not None and self.role.name.lower() == 'superadmin')

    def __str__(self):
        return self.username


class EmailOTP(models.Model):
    user = models.OneToOneField(PortalUser, on_delete=models.CASCADE, related_name="email_otp")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"

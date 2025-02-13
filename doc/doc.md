# Models Documentation for PHB Platform

This document explains the complete models.py file used in our PHB healthcare platform. It covers the custom user model, supporting institution models (Hospital, GPPractice, GeneralPractitioner), a dedicated MedicalRecord model, and signals for automating certain behaviors. Each section is explained in simple terms.

> # 1. Custom User Manager

Code
```python
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)
```

Explanation
- Purpose:
The custom user manager handles how new users are created.
- Key Points:
- create_user:
- Checks that an email is provided.
- Normalizes the email (making the domain lowercase).
- Creates a new user with the given email and additional fields.
- Hashes the password for security.
- create_superuser:
- Ensures that the superuser has admin privileges (is_staff and is_superuser set to True).
- Calls create_user to avoid repeating code.

> # 2. Supporting Models

These models represent institutions in the healthcare system.

 2.1 Hospital

Code
```python
class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name
```

Explanation
- Hospital:
Stores details about hospitals, including name, address, contact phone, and website.
- The is_verified flag indicates if a hospital has been approved by a super admin.
- The __str__ method returns the hospital’s name for easy display.

> # 2.2 GPPractice

Code
```python   
class GPPractice(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name='gp_practices'
    )

    def __str__(self):
        return self.name
```

Explanation
- GPPractice:
Represents a general practitioner (GP) practice.
- It can be associated with a hospital.
- Uses a foreign key so that if the hospital is removed, the practice is not automatically deleted.

> # 2.3 GeneralPractitioner

Code
```python       
class GeneralPractitioner(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    practice = models.ForeignKey(
        GPPractice, on_delete=models.SET_NULL, null=True, blank=True, related_name='general_practitioners'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
```

Explanation
- GeneralPractitioner:
Stores information about individual doctors.
- Contains personal names and a unique license number.
- Linked to a GPPractice via a foreign key.

> # 3. CustomUser Model

Code
```python
class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to.",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="customuser_set",
        blank=True,
        help_text="Specific permissions for this user.",
        related_query_name="customuser",
    )

    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    nin = models.CharField(max_length=11, unique=True, null=True, blank=True)
    
    consent_terms = models.BooleanField(default=False)
    consent_hipaa = models.BooleanField(default=False)
    consent_data_processing = models.BooleanField(default=False)

    hpn = models.CharField(max_length=30, unique=True, editable=False, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    password_reset_token = models.CharField(max_length=64, null=True, blank=True)
    social_provider = models.CharField(max_length=20, blank=True, null=True)
    social_id = models.CharField(max_length=255, blank=True, null=True)
    
    primary_hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True
    )
    current_gp_practice = models.ForeignKey(
        GPPractice, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_patients'
    )
    current_gp = models.ForeignKey(
        GeneralPractitioner, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_patients'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    email = models.EmailField(unique=True)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if not self.hpn:
            state_code = self.city[:3].upper() if self.city else "UNK"
            unique_number = str(uuid.uuid4().int)[:10]
            self.hpn = f"{state_code} {unique_number[:3]} {unique_number[3:6]} {unique_number[6:]}"
        super().save(*args, **kwargs)
```

Explanation
- Inheritance:
Inherits from Django’s AbstractUser so it automatically has fields like password and email.
- Custom Fields:
- Personal Information: date_of_birth, country, city, phone, and nin (National Identity Number).
- Consents: Three Boolean fields (consent_terms, consent_hipaa, consent_data_processing) store user agreement data.
- HPN (Health Point Number): Auto-generated unique identifier that is not editable.
- Verification & Social Info: Fields to track verification and social login information.
- Associations:
Links to Hospital, GPPractice, and GeneralPractitioner through foreign keys.
- Custom Manager:
Uses CustomUserManager for user creation.
- Authentication Settings:
Uses email as the username (USERNAME_FIELD = 'email') and requires first and last names.
- Save Method:
Automatically sets the username to email (if missing) and generates an HPN if not already set.

> # 4. MedicalRecord Model

Code
```python   
class MedicalRecord(models.Model):
    hpn = models.CharField(max_length=30, unique=True)
    user = models.OneToOneField(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_record'
    )
    is_anonymous = models.BooleanField(default=False)

    blood_type = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        null=True, blank=True
    )
    allergies = models.TextField(null=True, blank=True)
    chronic_conditions = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)
    is_high_risk = models.BooleanField(default=False)
    last_visit_date = models.DateTimeField(null=True, blank=True)

    def anonymize_record(self):
        """Anonymize the record when the user is deleted."""
        self.is_anonymous = True
        self.user = None
        self.save()

    def __str__(self):
        return f"Medical Record for HPN: {self.hpn}"
```

Explanation
- HPN as Identifier:
The MedicalRecord is linked via the unique HPN, which is generated for each user.
- User Association:
Optionally linked to the CustomUser (can be set to null to anonymize data).
- Medical Fields:
Contains health-related information such as blood type, allergies, and chronic conditions.
- Anonymization:
The anonymize_record() method marks the record as anonymous and disassociates it from the user if the user is deleted.

> # 5. Signals

Code
```python
@receiver(post_save, sender=CustomUser)
def create_medical_record(sender, instance, created, **kwargs):
    if created:
        # Automatically create a MedicalRecord linked to the user's HPN when a new user is created
        MedicalRecord.objects.create(hpn=instance.hpn, user=instance)

@receiver(pre_delete, sender=CustomUser)
def anonymize_medical_record(sender, instance, **kwargs):
    try:
        record = instance.medical_record
        record.anonymize_record()
    except MedicalRecord.DoesNotExist:
        pass
```

Explanation
- Post-save Signal:
After a new user is created, this signal automatically creates a corresponding MedicalRecord, linking it by the user’s HPN.
- Pre-delete Signal:
Before a user is deleted, this signal anonymizes their MedicalRecord (disassociates the user and marks the record as anonymous) so that the data remains available for research or audit purposes.

Summary
- Custom User Manager & Model:
Handles user creation with email as the username, auto-generates an HPN, and stores personal and consent data.
- Supporting Models:
Represent hospitals, GP practices, and general practitioners.
- MedicalRecord Model:
Separates medical data from user authentication data, linked by the HPN.
- Signals:
Automate the creation of medical records and the anonymization process on user deletion.

This documentation should serve as a comprehensive note on how our data models work within the PHB platform, ensuring clarity even for non-technical stakeholders.

Feel free to adjust or expand on this document as your project evolves. Happy coding, and great work keeping detailed documentation!
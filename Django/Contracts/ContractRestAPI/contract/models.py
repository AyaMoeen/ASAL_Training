from django.db import models
#from django.contrib.auth.models import User

from django.contrib.auth.models import AbstractUser

class Profile(AbstractUser): 
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('contractor', 'Contractor'),
    ]

    profession: models.CharField = models.CharField(max_length=100)
    balance:models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    type_profile:models.CharField = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Contract(models.Model):
    Choice = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('terminated', 'Terminated'),
    ]
    client: 'models.ForeignKey[Profile]' = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='client_contracts')
    contractor: 'models.ForeignKey[Profile]' = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='contractor_contracts')
    terms: models.TextField = models.TextField()
    status: models.CharField = models.CharField(max_length=20, choices=Choice)
    
    class Meta:
        permissions = [
            ("can_view_contract", "Can view the contract"),
        ]
    
    def __str__(self):
        return f"Contract between {self.client} and {self.contractor}"
    
class Job(models.Model):
    contract: 'models.ForeignKey[Contract]' = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='jobs')
    description: models.TextField = models.TextField()
    price: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date: models.DateField = models.DateField()
    paid: models.BooleanField = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Job: {self.description} for {self.contract}"


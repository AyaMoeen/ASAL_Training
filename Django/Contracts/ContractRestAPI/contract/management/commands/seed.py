from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from contract.models import Profile, Contract, Job
import random
from datetime import date, timedelta

class Command(BaseCommand):
    help = "Seeds the database with initial data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        Profile.objects.all().delete()
        Contract.objects.all().delete()
        Job.objects.all().delete()

        profiles = []
        for i in range(10):
            username = f"user{i}"
            email = f"user{i}@example.com"
            password = "password"
            profile = Profile(
                username=username,
                email=email,
                first_name=f"FirstName{i}",
                last_name=f"LastName{i}",
                profession=f"Profession{i}",
                balance=random.uniform(0, 1000),
                type_profile=random.choice(Profile.ROLE_CHOICES)[0]
            )
            profile.set_password(password) 
            profiles.append(profile)

        Profile.objects.bulk_create(profiles)  
        
        contracts = []
        jobs = []
        clients = [p for p in Profile.objects.filter(type_profile='client')]
        contractors = [p for p in Profile.objects.filter(type_profile='contractor')]

        for i in range(5):
            client = random.choice(clients)
            contractor = random.choice([p for p in contractors if p != client])
            contract = Contract(
                client=client,
                contractor=contractor,
                terms=f"Terms for contract {i}",
                status=random.choice(Contract.Choice)[0]
            )
            contracts.append(contract)

            permission = Permission.objects.get(codename='can_view_contract')
            client.user_permissions.add(permission)
            contractor.user_permissions.add(permission)

        Contract.objects.bulk_create(contracts)  

        for contract in Contract.objects.all():  
            for j in range(2):
                jobs.append(Job(
                    contract=contract,
                    description=f"Job description {j} for contract {contract.id}",
                    price=random.uniform(100, 500),
                    payment_date=date.today() + timedelta(days=random.randint(1, 30)),
                    paid=random.choice([True, False])
                ))

        Job.objects.bulk_create(jobs) 

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))

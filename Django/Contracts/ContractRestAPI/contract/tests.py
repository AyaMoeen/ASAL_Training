from .models import Job, Contract, Profile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime
from decimal import Decimal

def create_profile(username, password='123456', type_profile='client', balance=Decimal('100.00'), profession='Engineer'):
    profile = Profile.objects.create_user(
        username=username,
        password=password,
        type_profile=type_profile,
        balance=balance,
        profession=profession
    )
    return profile



def create_contract(user, contractor_profile, status):
    return Contract.objects.create(
            client=user,
            contractor=contractor_profile,  
            status=status,
        )

def create_job(contract, price=Decimal('200'), paid=False, payment_date=None):
    if payment_date is None:
        payment_date = datetime.now()
    return Job.objects.create(
            contract=contract,
            paid=paid,
            price=price,
            payment_date=payment_date,
        )

class ModelTestSetup(APITestCase):
    def setUp(self):
        self.user = create_profile(username='aya', type_profile='client')
        self.contractor_profile = create_profile(username='ahmed', type_profile='contractor')
        self.contract = create_contract(
            self.user,
            self.contractor_profile,
            "in_progress"
        )
        self.job = create_job(self.contract)
        self.job2 = create_job(contract=self.contract, price=Decimal('500'), paid=True, payment_date='2024-06-01')


class AuthUserViewTest(ModelTestSetup):
    def test_register_user(self):
        url = reverse('contract:signup')
        data = {
            "username": "ayamoin",
            "password": "123456",
            "email": "ayamoin@gmail.com",
            "profession": "Developer",  
            "type_profile": "client"  
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User created successfully")

    def test_login_user(self):
        create_profile(username='ayosh', password='123456')
        url = reverse('contract:login')
        data = {
            "username": "ayosh",
            "password": "123456"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        
    def test_login_user_unauthorized(self):
        url = reverse('contract:login')
        data = {
            "username": "user",
            "password": "pass"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ProfileViewTest(ModelTestSetup):

    def test_get_profile(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('contract:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
class ContractListViewTest(ModelTestSetup):
          
    def test_get_in_progress_contracts(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('contract:contracts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(contract["status"] == "in_progress" for contract in response.data))
        
class DepositViewTest(ModelTestSetup):

    def test_deposit_valid_amount(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('contract:balance-deposit', args=[self.user.id])
        
        data = {"amount": "50.00"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()  
        self.assertEqual(self.user.balance, Decimal('150.00'))

    def test_deposit_exceeds_limit(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('contract:balance-deposit', args=[self.user.id])
        
        data = {"amount": "200.00"} 
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Deposit exceeds maximum allowed amount")

  
        
class JobViewTest(ModelTestSetup):

    def test_get_unpaid_jobs(self):
        self.client.force_authenticate(user=self.contractor_profile)
        url = reverse('contract:unpaid-jobs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)        
         
    def test_balance_isufficient(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('contract:job-pay', args=[self.job.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.job.refresh_from_db()
        self.assertFalse(self.job.paid)
    
    def test_pay_successful(self):
        self.user.balance = Decimal('300')
        self.user.save()
        self.client.force_authenticate(user=self.user)
        url = reverse('contract:job-pay', args=[self.job.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertTrue(self.job.paid)
       
     
    def test_best_profession(self):
        start_date = '2024-01-01'
        end_date = '2024-11-3'

        contractor_profile_1 = create_profile(
            username="aega", 
            password='123456',
            type_profile='contractor',
            profession='Engineer'  
        )
        contractor_profile_2 = create_profile(
            username="ahmad", 
            password='456456',
            type_profile='contractor',
            profession='nurse'  
        )

        create_job(
            contract=create_contract(self.user, contractor_profile_1, 'completed'), 
            price=Decimal('300'), 
            paid=True, 
            payment_date='2024-05-01'
        )
        create_job(
            contract=create_contract(self.user, contractor_profile_2, 'completed'), 
            price=Decimal('100'), 
            paid=True, 
            payment_date='2024-06-01'
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('contract:best-profession')
        response = self.client.get(f"{url}?start={start_date}&end={end_date}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profession'], 'Engineer') 
        self.assertEqual(response.data['total_earnings'], Decimal('800'))

         
    def test_best_clients_view(self):
        self.client.force_authenticate(user=self.user)

        start_date = '2024-01-01'
        end_date = '2024-10-31'

        url = reverse('contract:best-clients') 
        response = self.client.get(f"{url}?start={start_date}&end={end_date}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  
        self.assertEqual(response.data[0]['paid'], Decimal('500'))    
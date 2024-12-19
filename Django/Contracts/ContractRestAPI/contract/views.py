
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, Profileserializer, ContractSerializer, JobSerializer
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, AllowAny
from .models import Profile, Contract, Job
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Q, Sum, F
from .google_sheet import log_payment, log_deposit

class IndexView(APIView):
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    queryset = Profile.objects.none() 
    def get(self, request):
        return Response({"message": "Hello, world. You're at the polls index."})

class ProfileView(generics.RetrieveAPIView):
    """
    GET /profile - Returns the profile of the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = Profile.objects.get(username=request.user.username)
            serializer = Profileserializer(profile)
            return Response(serializer.data, status=200)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

class ContractDetailView(generics.RetrieveAPIView):
    """
    GET /contracts/{contract_id} - Returns a specific contract for the authenticated user.
    """
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = self.request.user  
        return Contract.objects.filter(
            Q(client=user_profile) | Q(contractor=user_profile)
        )

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm("contract.can_view_contract"):
            return Response({"error": "Not authorized to view this contract"}, status=status.HTTP_403_FORBIDDEN)

        return super().get(request, *args, **kwargs)

class ContractListView(generics.ListAPIView):
    """
    GET /contracts - Returns a list of contracts for the authenticated user.
    """
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = get_object_or_404(Profile, id=self.request.user.id)
        status_filter = self.request.query_params.get('status', None)

        queryset = Contract.objects.filter(
            Q(client=user_profile) | Q(contractor=user_profile)
        )
        allowed_statuses = dict(Contract.Choice).keys() 
        if status_filter == 'all':
            return queryset
        elif status_filter in allowed_statuses:
            return queryset.filter(status=status_filter)
        elif status_filter is None:
            return queryset.filter(status__in=['new', 'in_progress']) 
        else:
            raise ValueError(f"Invalid status filter: {status_filter}. Allowed values are: {', '.join(allowed_statuses)}")

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#class ContractListView(generics.ListAPIView):
#    """
#    GET /contracts - Returns a list of contracts for the authenticated user.
#    """
#    serializer_class = ContractSerializer
#    permission_classes = [IsAuthenticated]
#
#    def get_queryset(self):
#        user_profile = get_object_or_404(Profile, id=self.request.user.id)
#        status_filter = self.request.query_params.get('status', None)
#    
#        queryset = Contract.objects.filter(
#            Q(client=user_profile) | Q(contractor=user_profile)
#        )
#        allowed_statuses = dict(Contract.Choice).keys()  # Get the valid status choices
#
#        if status_filter == 'all':
#            return queryset
#        elif status_filter in allowed_statuses:
#            return queryset.filter(status=status_filter)
#        else:
#            # Return a 400 Bad Request response for invalid status
#            raise ValueError(f"Invalid status filter: {status_filter}. Allowed values are: {', '.join(allowed_statuses)}")
        #if status_filter == 'all':
        #    return queryset
        #elif status_filter:
        #    return queryset.filter(status=status_filter)
        #else:
        #    return queryset.filter(status__in=['new', 'in_progress'])
    
class JobListView(generics.ListAPIView):
    """
    GET /jobs - Returns a list of jobs for the authenticated user.
    """
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = get_object_or_404(Profile, id=self.request.user.id)
        return Job.objects.filter(contract__client=user_profile) | Job.objects.filter(contract__contractor=user_profile)


class UnpaidJobsView(generics.ListAPIView):
    """
    GET /jobs/unpaid - Returns a list of unpaid jobs for the authenticated user.
    """
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = get_object_or_404(Profile, id=self.request.user.id)
        return Job.objects.filter(paid=False, contract__status='in_progress').filter(
            Q(contract__client=user_profile) | Q(contract__contractor=user_profile)
        )

class JobPayView(APIView):
    """
    POST /jobs/{job_id}/pay - Allows a client to pay for a job that has been completed.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id, contract__client__username=request.user.username, paid=False)
            client = job.contract.client
            contractor = job.contract.contractor

            if client.balance < job.price:
                return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
            
            client.balance = F('balance') - job.price
            contractor.balance = F('balance') + job.price

            client.save()
            contractor.save()
            job.paid = True
            job.payment_date = timezone.now().date()
            job.save()
            log_payment(f"{client.first_name} {client.last_name}", float(job.price), job.id)

            return Response({"message": "Job paid successfully"}, status=status.HTTP_200_OK)
        
        except Job.DoesNotExist:
            return Response({"error": "Job not found or already paid"}, status=status.HTTP_404_NOT_FOUND)


class DepositView(APIView):
    """
    POST /deposit - Allows a client to deposit money into their balance.
    """
    permission_classes = [IsAuthenticated]
    DEPOSIT_RATIO = Decimal('0.25')

    def post(self, request, userId):
        try:
            profile = Profile.objects.get(id=userId, type_profile='client')
            deposit_amount = Decimal(request.data.get("amount", 0))

            total_jobs_cost = Job.objects.filter(
                contract__client=profile, paid=False
            ).aggregate(total=Sum('price'))['total'] or 0
            
            max_deposit = Decimal(total_jobs_cost) * self.DEPOSIT_RATIO

            if deposit_amount > max_deposit:
                return Response({"error": "Deposit exceeds maximum allowed amount"}, status=status.HTTP_400_BAD_REQUEST)

            profile.balance = F('balance') + deposit_amount
            profile.save()
            log_deposit(f"{profile.first_name} {profile.last_name}", float(deposit_amount))
            return Response({"message": "Deposit successful"}, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

class ValidateDateView(APIView):
    """
    GET /validate-date - Validates a given date.
    """
    permission_classes = [IsAuthenticated]

    def validate_date(self, date_str):
        """ validate date format. """
        try:
            return timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

class BestProfessionView(ValidateDateView):
    """
    GET /best-profession - Returns the profession with the highest total paid amount within a given date range.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')

        if not start_date or not end_date:
            return Response({"error": "Both 'start' and 'end' query parameters are required."}, status=400)
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)
        
        best_profession = (
            Job.objects.filter(
                paid=True,
                payment_date__range=[start_date, end_date]
            )
            .select_related('contract__contractor')
            .values(profession=F('contract__contractor__profession'))  
            .annotate(total_earnings=Sum('price'))  
            .order_by('-total_earnings') 
            .first() 
        )

        return Response(best_profession)

class BestClientsView(ValidateDateView):
    """
    GET /best-clients - Returns the clients with the highest total paid amount within a given date range.
    """
    permission_classes = [IsAuthenticated]
    DEFAULT_LIMIT = 3
    
    def get(self, request):
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)
        limit = int(request.query_params.get('limit', self.DEFAULT_LIMIT))

        best_clients = (
            Job.objects.filter(
                paid=True,
                payment_date__range=[start_date, end_date]
            )
            .select_related('contract__client')  
            .values('id', fullName=F('contract__client__username')) 
            .annotate(paid=Sum('price'))
            .order_by('-paid')[:limit]
        )

        return Response(best_clients)  
  
class RegisterView(APIView):
    """
    POST /register - Registers a new user and creates a profile for them.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save() 
            return Response({"message": "User created successfully"}, status=201)
        else:
            return Response(serializer.errors, status=400) 
        
class LoginView(APIView):
    """
    POST /login - Authenticates a user and returns an authentication token.
    """
    permission_classes = [AllowAny]  

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

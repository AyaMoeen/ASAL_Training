from django.urls import path
from . import views
app_name = "contract"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("signup/", views.RegisterView.as_view(), name="signup"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("contracts/", views.ContractListView.as_view(), name="contracts"),
    path("contracts/<int:pk>/", views.ContractDetailView.as_view(), name="contract-detail"),
    path("jobs/", views.JobListView.as_view(), name="job-list"),
    path("jobs/unpaid/", views.UnpaidJobsView.as_view(), name="unpaid-jobs"),
    path("jobs/<int:job_id>/pay/", views.JobPayView.as_view(), name="job-pay"),
    path("balances/deposit/<int:userId>/", views.DepositView.as_view(), name="balance-deposit"),
    path("jobs/best-profession/", views.BestProfessionView.as_view(), name="best-profession"),
    path("jobs/best-clients/", views.BestClientsView.as_view(), name="best-clients"),
]


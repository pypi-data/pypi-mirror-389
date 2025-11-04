from django.urls import path
from .views import EmbeddedSignupCallbackView, BusinessCallbackView, OnboardingStatusView

urlpatterns = [
    path('callback/', EmbeddedSignupCallbackView.as_view(), name='embedded_signup_callback'),
    path('business-callback/', BusinessCallbackView.as_view(), name='business_callback'),
    path('onboarding-status/<str:phone_number_id>/', OnboardingStatusView.as_view(), name='onboarding_status'),
]

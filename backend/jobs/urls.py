from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'feed', views.JobFeedViewSet)
router.register(r'attempts', views.JobAttemptViewSet)

urlpatterns = [
    # Job management
    path('', include(router.urls)),
    
    # Job actions
    path('<uuid:job_id>/accept/', views.AcceptJobView.as_view(), name='accept_job'),
    path('<uuid:job_id>/submit/', views.SubmitJobView.as_view(), name='submit_job'),
    path('<uuid:job_id>/cancel/', views.CancelJobView.as_view(), name='cancel_job'),
    
    # Job feed and filtering
    path('feed/search/', views.JobSearchView.as_view(), name='job_search'),
    path('feed/filter/', views.JobFilterView.as_view(), name='job_filter'),
    path('feed/recommended/', views.RecommendedJobsView.as_view(), name='recommended_jobs'),
    
    # Job attempts and verification
    path('attempts/<uuid:attempt_id>/appeal/', views.AppealJobAttemptView.as_view(), name='appeal_attempt'),
    path('attempts/<uuid:attempt_id>/resubmit/', views.ResubmitJobAttemptView.as_view(), name='resubmit_attempt'),
    
    # Job statistics
    path('stats/', views.JobStatsView.as_view(), name='job_stats'),
    path('stats/user/', views.UserJobStatsView.as_view(), name='user_job_stats'),
    
    # Bulk operations
    path('bulk/accept/', views.BulkAcceptJobsView.as_view(), name='bulk_accept_jobs'),
    path('bulk/cancel/', views.BulkCancelJobsView.as_view(), name='bulk_cancel_jobs'),
]

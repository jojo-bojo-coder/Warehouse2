from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
import club_dashboard.views as club_views

urlpatterns = [
    path('', views.administrator_dashboard_index, name="administrator_dashboard_index"),
    path('viewStudents', club_views.viewStudents, name="viewStudents"),
    path('export-students-excel/', club_views.export_students_excel, name='export_students_excel'),
    path('addStudent', club_views.addStudent, name="addStudent"),
    path('editStudent/<int:id>', club_views.editStudent, name="editStudent"),
    path('deleteStudent/<int:id>', club_views.deleteStudent, name="deleteStudent"),

    # Coaches Management
    path('viewCoachs', club_views.viewCoachs, name="viewCoachs"),
    path('export_coaches_excel/', club_views.export_coaches_excel, name='export_coaches_excel'),
   # path('addCoach', club_views.addCoach, name="addCoach"),
   # path('editCoach/<int:id>', club_views.editCoach, name="editCoach"),
   # path('deleteCoach/<int:id>', club_views.deleteCoach, name="deleteCoach"),

    # Blog Management
    path('articles/', club_views.viewArticles, name="viewArticles"),
    path('articles/add/', club_views.addArticle, name="addArticle"),
    path('articles/edit/<int:id>/', club_views.editArticle, name="editArticle"),
    path('articles/delete/<int:id>/', club_views.DeleteArticle, name="DeleteArticle"),

    path('mark-notifications-read/', club_views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/', club_views.viewClubNotifications, name='viewClubNotifications'),  # ✅ Ensure correct name
    path('reviews/', club_views.reviews_list, name='reviews_list'),

    path('club/orders/', club_views.club_orders, name='club_orders'),
    path('club/orders/<int:order_id>/update/', club_views.update_order_status, name='update_order_status'),
    path('club/orders/<int:order_id>/details/', club_views.order_details_api, name='order_details_api'),


    path('profile/administrator/', views.view_administrator_profile, name='view_administrator_profile'),
    path('profile/administrator/edit/', views.edit_administrator_profile, name='edit_administrator_profile'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
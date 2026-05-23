from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from dashboard import views as dashboard_views

urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(
            next_page="login"
        ),
        name="logout",
    ),

    path("", dashboard_views.dashboard_home, name="dashboard_home"),

    path("", include("core.urls")),
    path("accounting/", include("accounting.urls")),
    path("vendors/", include("vendors.urls")),
    path("stock/", include("stock.urls")),
    path("customers/", include("customers.urls")),
    path("workspaces/", include("workspaces.urls")),

    path("accounting-ops/", include("accounting_ops.urls")),
]
from django.conf.urls import url
import re

import views

urlpatterns = [
  url(r'^query$', views.query),
]

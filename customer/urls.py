from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'^customerlist/$', customerList, name='customerlist'),
    url(r'^customerdetail/$', customerDetail, name='customerdetail'),
    # url(r'^customerhistory/$', customerHistory, name='customerhistory'),
    url(r'^stockholding/$', stockHolding, name='stockholding'),
    url(r'^stockshorted/$', stockShorted, name='stockshorted'),
    url(r'^activity/$', customerActivity, name='activity'),
    url(r'^buy/$', buy, name='buy'),
    url(r'^short/$', short, name='short'),
    url(r'^cover/$', cover, name='cover'),
    url(r'^sell/$', sell, name='sell'),
    url(r'^buyinfo/$', buyinfo, name='buyinfo'),
    url(r'^sellinfo/$', sellinfo, name='sellinfo'),
    url(r'^shortinfo/$', shortinfo, name='shortinfo'),
    url(r'^coverinfo/$', sellinfo, name='coverinfo'),
    url(r'^create/$', createCustomer, name='create'),
    url(r'^takeloan/$', takeloan, name='takeloan'),
    url(r'^repayloan/$', repayloan, name='repayloan'),

]
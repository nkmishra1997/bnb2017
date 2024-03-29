from django.contrib.auth import login
from allauth.socialaccount.models import SocialAccount
from stockmarket.models import *
from customer.models import *

from django.utils import *

from django.http import HttpResponse, JsonResponse
from django.shortcuts import *
from django.views.decorators.http import require_POST

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.views.decorators.csrf import csrf_exempt

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView
from django.core import serializers

import json
import datetime

@api_view(["GET"])
def customerList(request, format = None):
	unsorted_tuples = Customer.objects.all()
	tuples = sorted(unsorted_tuples, key= lambda t: t.worth())
	response_data = []
	for customer in tuples:
		response_data.append({
			# ''
			'name': customer.user.first_name + ' ' + customer.user.last_name,
			'worth': customer.worth()
		})
	response_data.reverse()
	return JsonResponse(response_data, safe=False)
	# customer_serialized = serializers.serialize('json', tuples)
	# return HttpResponse(customer_serialized, content_type="application/json")

@api_view(["GET"])
def customerDetail(request, format = None):
	customer = get_object_or_404(Customer, user=request.user)
	response_data ={}
	response_data['fbid'] = SocialAccount.objects.get(user = customer.user).uid
	response_data['name'] = customer.user.first_name + ' ' + customer.user.last_name
	response_data['account_balance'] = customer.account_balance
	response_data['loan_balance'] = Loan.objects.filter(customer=customer).first().amount
	response_data['worth'] = customer.worth()
	response_data['portfolio'] = []
	companies = Company.objects.all()
	for company in companies:
		response_data['portfolio'].append({
			'company_id': company.id,
			'company_symbol': company.symbol,
			'stockholding': StockHolding.objects.get(company=company, customer=customer).quantity,
			'stockshorted': StockShorted.objects.get(company=company, customer=customer).quantity
		})
	return JsonResponse(response_data)

@api_view(["GET"])
def stockHolding(request, format = None):
	tuples = StockHolding.objects.filter(customer__user = request.user).all()
	serialized = serializers.serialize('json', tuples)
	return HttpResponse(serialized, content_type="application/json")

@api_view(["GET"])
def stockShorted(request, format = None):
	# shorted_quantity=get_object_or_404(StockHolding, user=request.user, company__pk=request.GET.get('id')).quantity
	tuples = StockShorted.objects.filter(customer__user = request.user).all()
	serialized = serializers.serialize('json', tuples)
	return HttpResponse(serialized, content_type="application/json")
	# return HttpResponse(str(shorted_quntity))

@api_view(["GET"])
def customerActivity(request, format=None):
	tuples = CustomerActivity.objects.filter(customer__user = request.user).all()
	serialized = serializers.serialize('json', tuples)
	return HttpResponse(serialized, content_type="application/json")

@api_view(["GET"])
def buyinfo(request, format=None):
	availabe_balance = get_object_or_404(Customer, user=request.user).account_balance
	price = get_object_or_404(Company, id=request.GET.get('id')).stock_price
	quantity = get_object_or_404(Company, id=request.GET.get('id')).available_quantity
	max_quant = availabe_balance//price
	return JsonResponse({'quantity': min(max_quant,quantity)})

@api_view(["GET"])
def shortinfo(request, format=None):
	return JsonResponse({'quantity': 100})

@api_view(["GET"])
def coverinfo(request, format=None):
	quantity = get_object_or_404 (StockShorted , company__pk=request.GET.get('id'), customer__user=request.user).quantity
	return JsonResponse({'quantity': quantity})

@api_view(["GET"])
def sellinfo(request, format=None):
	quantity = get_object_or_404 (StockHolding , company__pk=request.GET.get('id'), customer__user=request.user).quantity
	return JsonResponse({'quantity': quantity})

@api_view(["POST"])
def buy(request, format=None):
	customer = get_object_or_404(Customer, user=request.user)
	company = get_object_or_404(Company, pk=request.POST.get('id'))
	quantity = int(request.POST.get('quantity'))
	if quantity is None:
		return JsonResponse({"success":False})
	if 0 < quantity <= min(customer.account_balance//company.stock_price, company.available_quantity):
		stockHolding = get_object_or_404(StockHolding, company=company, customer=customer)
		stockHolding.quantity += quantity
		customer.account_balance -= company.stock_price * quantity
		company.available_quantity -= quantity
		customerActivity = CustomerActivity(customer=customer, action='BUY', timestamp=timezone.now(), quantity=quantity, price=company.stock_price)
		customerActivity.save()
		customer.save()
		company.save()
		stockHolding.save()
		return JsonResponse({"success":True})
	return JsonResponse({"success":False})

@api_view(["POST"])
def sell(request, format=None):
	customer = get_object_or_404(Customer, user=request.user)
	company = get_object_or_404(Company, pk=request.POST.get('id'))
	quantity = int(request.POST.get('quantity'))
	stockHolding = get_object_or_404(StockHolding, company=company, customer=customer)
	if quantity is None:
		return JsonResponse({"success":False})
	if 0 < quantity <= stockHolding.quantity:
		stockHolding.quantity -= quantity
		customer.account_balance += company.stock_price * quantity
		company.available_quantity += quantity
		customerActivity = CustomerActivity(customer=customer, action='SELL', timestamp=timezone.now(), quantity=quantity, price=company.stock_price)
		customerActivity.save()
		customer.save()
		company.save()
		stockHolding.save()
		return JsonResponse({"success":True})
	return JsonResponse({"success":False})

@api_view(["POST"])
def short(request, format=None):
	customer = get_object_or_404(Customer, user=request.user)
	company = get_object_or_404(Company, pk=request.POST.get('id'))
	quantity = int(request.POST.get('quantity'))
	if quantity is None:
		return JsonResponse({"success":False})
	if 0 < quantity <= company.available_quantity:
		stockShorted = get_object_or_404(StockShorted, company=company, customer=customer)
		stockShorted.quantity += quantity
		customer.account_balance += company.stock_price * quantity
		# company.available_quantity -= quantity
		customerActivity = CustomerActivity(customer=customer, action='SHORT', timestamp=timezone.now(), quantity=quantity, price=company.stock_price)
		customerActivity.save()
		customer.save()
		company.save()
		stockShorted.save()
		return JsonResponse({"success":True})
	return JsonResponse({"success":False})

@api_view(["POST"])
def cover(request, format=None):
	customer = get_object_or_404(Customer, user=request.user)
	company = get_object_or_404(Company, pk=request.POST.get('id'))
	stockShorted = get_object_or_404(StockShorted, company=company, customer=customer)
	quantity = int(request.POST.get('quantity'))
	if quantity is None:
		return JsonResponse({"success":False})
	if 0 < quantity <= stockShorted.quantity:
		stockShorted.quantity -= quantity
		customer.account_balance -= company.stock_price * quantity
		# company.available_quantity -= quantity
		customerActivity = CustomerActivity(customer=customer, action='COVER', timestamp=timezone.now(), quantity=quantity, price=company.stock_price)
		customerActivity.save()
		customer.save()
		company.save()
		stockShorted.save()
		return JsonResponse({"success":True})
	return JsonResponse({"success":False})

@api_view(["POST"])
def takeloan(request, format=None):
	customer = get_object_or_404(Customer, user=request.user)
	loan= get_object_or_404(Loan, customer=customer)
	if loan.amount==0:
		loan.amount = 10000
		customer.account_balance += 10000 
		loan.save()
		customer.save()
		return JsonResponse({"success":True})
	return JsonResponse({"success":False})

@api_view(["POST"])
def repayloan(request, format=None):
	loan= get_object_or_404(Loan, customer__user=request.user)
	customer = get_object_or_404(Customer, user=request.user)
	if loan.amount > 0 and loan.amount <= customer.account_balance:
		loan.amount = 0
		customer.account_balance -= 10000
		loan.repay_time=datetime.datetime.now()
		loan.save()
		customer.save()
		return JsonResponse({"success":True})
	return JsonResponse({"success":False})

def createCustomer(request, format = None):	
	if not request.user.is_authenticated:	
		user = SocialAccount.objects.get(uid = request.GET.get("fbid")).user
		login(request, user)
	else:
		user = request.user
	try:
		customer = Customer.objects.get(user = user)
	except Customer.DoesNotExist:
		customer = Customer(user = user, account_balance = 25000)
		companies = Company.objects.all()
		customer.save()
		loan = Loan(customer=customer, amount=0)
		loan.save()
		for company in companies:
			sh = StockHolding(company=company, customer=customer, quantity=0)
			ss = StockShorted(company=company, customer=customer, quantity=0)
			sh.save()
			ss.save()
	return HttpResponseRedirect('/')

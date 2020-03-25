from django.shortcuts import render, redirect
from .models import Product, Contact, Orders, OrderUpdate
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

from .forms import CreateUserForm, CustomerForm
from .decorators import unauthenticated_user, allowed_users, admin_only
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum
from django.http import HttpResponse
MERCHANT_KEY = '_cNH09mTKV7Qa7SI'

@unauthenticated_user   
def registerPage(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')

            group = Group.objects.get(name='customer')
            user.groups.add(group)

            messages.success(request, 'Account was created for ' + username)

            return redirect('login')

    context = {'form': form}
    return render(request, 'shop/register.html', context)
    

@unauthenticated_user   
def loginPage(request):
    if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('/')
        
            else:
                messages.info(request, 'Username OR password is incorrect')
            
    context = {}
    return render(request, 'shop/login.html', context)
   
    

def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
@admin_only
def index(request):
    #products = Product.objects.all()
    #print(products)
    #n = len(products)
    #nSlides = (n//4 + ceil((n/4)-(n//4))) #calculation of the number of slides
    #params = {'no_of_slides': nSlides, 'range': range(1, nSlides), 'product': products} 
#I am going to make a list, where it contains the sliders list, so basically i will have a list of list for which that list will represent a slider for it will contain the category of each products
#the list of lists will be called allProds( it contains all products)

#its just the category which are different, that's why there are two lists, 
# but the number of slides will remain the same!
    #allProds = [[products, range(1, nSlides), nSlides], 
    #          [products, range(1, nSlides), nSlides]]
    allProds = []
    catprods = Product.objects.values('category', 'id')
    #this method will returns a list of a given object's own enumerable property values, 
    #in the same order as that provided by a for...in loop
    # 'category', 'id' are object whose enumerable own property values are to be returned.
    cats = {item['category'] for item in catprods}
    #I have created a setter just above which has a set comprehension in other word,
    #has a list/set comprihension where i will fetch item category for items in catprods in the method above.
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4)) #calculation of the number of slides
        allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds':allProds}
    #In the parameters, first of all, i am going to add the number of slides, 
    #nSlides function and the function range for range of slides it will contain,
     #then i am going to pass the template for products
    return render(request, 'shop/index.html', params)

def userPage(request):
    context = {}
    return render(request, 'shop/index.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def accountSettings(request):
    customer = request.user.customer
    form = CustomerForm(instance=customer)

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()

    context = {'form':form}
    return render(request, 'shop/account_settings.html', context)


def searchMatch(query, item):
    '''return true only if the query matches the required items!'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False


def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]

        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds':allProds, "msg": ""}
    if len(allProds) == 0 or len(query) < 4:
        params = {'msg': "Please make sure to enter the right searches!"}
    return render(request, 'shop/search.html', params)

def about(request):
    return render(request, 'shop/about.html')

def privacy(request):
    return render(request, 'shop/privacy.html')

def faq(request):
    return render(request, 'shop/faq.html')


def contact(request):
    thank = False
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank = True
    return render(request, 'shop/contact.html', {'thank': thank})

@login_required(login_url='login')
def tracker(request):
    if request.method=="POST": #if that request is a post, it will execute the orderId, email else it will return blank.
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try: #The try block here lets me test that block of code for errors, so if the if statement for order is greater than zero, it will update the response else it will return blank.
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps({"status":"success", "updates": updates, "itemsJson": order[0].items_json}, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e: #The except block here let me handled the error! 
            return HttpResponse('{"status":"error"}')

    return render(request, 'shop/tracker.html')




@login_required(login_url='login')
def productView(request, myid):

    # retrieve the product using the id = myid
    product = Product.objects.filter(id=myid)
    return render(request, 'shop/prodView.html', {'product':product[0]})

@login_required(login_url='login')
def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone, amount=amount)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed") #I want to make it such that whenever someone place an order, it should appear like the orders have been place
        update.save()
        thank = True
        id = order.order_id
        # return render(request, 'shop/checkout.html', {'thank':thank, 'id': id})
        # Request paytm to transfer the amount to your account after payment by user
        param_dict = {

                'MID':'IsoNWP77745394082690',
                'ORDER_ID': str(order.order_id),
                'TXN_AMOUNT': str(amount),
                'CUST_ID': email,
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'WEBSTAGING',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',

        }
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'shop/paytm.html', {'param_dict': param_dict})

    return render(request, 'shop/checkout.html')

@login_required(login_url='login')
@csrf_exempt
def handlerequest(request):
    # paytm will send you post request here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})

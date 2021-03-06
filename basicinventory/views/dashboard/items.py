from django.shortcuts import render, redirect
from django.db import IntegrityError
from django.urls import reverse
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages
from basicinventory.models.item import Item
from basicinventory.models.warehouse import Warehouse
from basicinventory.forms.item import ItemForm


def item_add(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            warehouse = None
            data = form.cleaned_data
            if data.get('warehouse_id'):
                warehouse_id = data.pop('warehouse_id')
                try:
                    warehouse = Warehouse.objects.get(pk=warehouse_id)
                except Warehouse.DoesNotExist:
                    print('Error in getting warehouse')
                    return redirect('item_add')
            item = Item(**data, warehouse=warehouse)

            try:
                item.save()
            except IntegrityError:
                messages.warning(
                    request, 'Similar item exists with item code and warehouse')
                return redirect('item_list')

            messages.success(request, 'Item added successfully')
            return redirect('item_list')
        else:
            print(form.errors)
            print('Invalid form')
            return redirect('item_add')

    warehouses = Warehouse.operational_objects.all()
    form = ItemForm()

    context = {
        'warehouses': warehouses,
        'url_name': 'item_add',
        'form': form
    }
    return render(request, 'dashboard/items/add.html', context)


def item_list(request):
    items = Item.objects.all().order_by('-created_at')

    # pagination
    page_size = settings.MAX_PAGE_SIZE
    paginator = Paginator(items, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'url_name': 'item_list',
    }
    return render(request, 'dashboard/items/list.html', context)


def item_detail(request, item_id):
    try:
        item = Item.objects.get(pk=item_id)

        context = {
            'item': item
        }
        return render(request, 'dashboard/items/detail.html', context)
    except Item.DoesNotExist:
        messages.error(request, 'Unable to fetch item details')
        return redirect('item_list')


def item_edit(request, item_id):
    try:
        item = Item.objects.get(pk=item_id)

        if request.method == 'POST':
            form = ItemForm(request.POST, instance=item)
            if form.is_valid():
                warehouse = None
                data = form.cleaned_data
                if data.get('warehouse_id'):
                    warehouse_id = data.pop('warehouse_id')
                    try:
                        warehouse = Warehouse.objects.get(pk=warehouse_id)
                    except Warehouse.DoesNotExist:
                        messages.error(request, 'Unable to get warehouse')
                        return redirect('item_edit', item_id=item_id)
                item = form.save()
                item.warehouse = warehouse
                item.save()

                messages.success(request, f'Item code - {item.code} edited')

                redirect_url = request.GET.get(
                    'redirect_url',
                    reverse('item_list')
                )

                return redirect(redirect_url)
            else:
                messages.error(request, 'Unable to submit form')
                return redirect('item_edit', item_id=item_id)

        warehouses = Warehouse.operational_objects.all()

        context = {
            'item': item,
            'warehouses': warehouses,
            'redirect_url': request.GET.get('redirect_url', reverse('item_list'))
        }
        return render(request, 'dashboard/items/edit.html', context)
    except Item.DoesNotExist:
        return redirect('item_list')


def item_delete(request, item_id):
    try:
        item = Item.objects.get(pk=item_id)
        item.delete()
        redirect_url = request.GET.get('redirect_url', None)

        messages.success(request, 'Item deleted')

        if redirect_url:
            return redirect(redirect_url)
        else:
            return redirect('item_list')
    except:
        return redirect('item_list')

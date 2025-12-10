from foodapp.models import MenuItem
for item in MenuItem.objects.all():
    print(item.name, item.price)

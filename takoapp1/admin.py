from django.contrib import admin
from .models import Order, CartItem, Cart, Product

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # 'display_items' is the custom function we create below
    list_display = ('id', 'customer_name', 'status', 'display_items', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'id')

    # ✅ This function pulls the ManyToMany items and turns them into a readable string
    def display_items(self, obj):
        return ", ".join([str(item) for item in obj.items.all()])
    
    display_items.short_description = 'Ordered Items'

# Register others normally
admin.site.register(CartItem)
admin.site.register(Cart)
admin.site.register(Product)


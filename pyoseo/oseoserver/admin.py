from django.contrib import admin
import models

class OrderAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('approved', 'order_type', 'status', 'status_changed_on',
                       'completed_on', 'user', 'reference', 'priority',
                       'packaging',)
        }),
        ('Further info',{
            'classes': ('collapse',),
            'fields': ('remark', 'additional_status_info',
                       'mission_specific_status_info')
        }),
    )
    list_display = ('id', 'order_type', 'status', 'status_changed_on',)
    readonly_fields = ('status_changed_on', 'completed_on',)

admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.Batch)
admin.site.register(models.OrderItem)
admin.site.register(models.User)
admin.site.register(models.Product)
admin.site.register(models.Option)
admin.site.register(models.ProductOption)
admin.site.register(models.OptionChoice)
admin.site.register(models.SelectedOption)
admin.site.register(models.DeliveryOption)
admin.site.register(models.DeliveryInformation)
admin.site.register(models.OnlineAddress)
admin.site.register(models.InvoiceAddress)

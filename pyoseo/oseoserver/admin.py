from django.contrib import admin
import models

class OptionChoiceInline(admin.StackedInline):
    model = models.OptionChoice
    extra = 1

class OptionGroupAdmin(admin.ModelAdmin):
    pass

class OrderAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('approved', 'order_type', 'status', 'option_group',
                       'status_changed_on', 'completed_on', 'user',
                       'reference', 'priority', 'packaging',)
        }),
        ('Further info',{
            'classes': ('collapse',),
            'fields': ('remark', 'additional_status_info',
                       'mission_specific_status_info')
        }),
    )
    list_display = ('id', 'order_type', 'status', 'status_changed_on',)
    readonly_fields = ('status_changed_on', 'completed_on',)


class OrderItemAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('item_id', 'batch', 'status', 'option_group',
                       'status_changed_on', 'identifier', 'collection_id',)
        }),
        ('Further info',{
            'classes': ('collapse',),
            'fields': ('remark',
                       'additional_status_info',
                       'mission_specific_status_info')
        }),
    )
    list_display = ('item_id', 'batch', 'status', 'status_changed_on',)
    readonly_fields = ('status_changed_on',)

class OptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'product', 'available_choices',)
    inlines = [OptionChoiceInline,]

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'collection_id',)

class BatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'status',)

class GroupOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'option', 'group',)

class SelectedOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'customizable_item', 'group_option', 'value',)

class GroupDeliveryOptionAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.OrderType)
admin.site.register(models.GroupOption, GroupOptionAdmin)
admin.site.register(models.GroupDeliveryOption, GroupDeliveryOptionAdmin)
admin.site.register(models.OnlineDataAccess)
admin.site.register(models.OnlineDataDelivery)
admin.site.register(models.MediaDelivery)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.Batch, BatchAdmin)
admin.site.register(models.OrderItem, OrderItemAdmin)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Option, OptionAdmin)
admin.site.register(models.OptionOrderType)
admin.site.register(models.DeliveryOptionOrderType)
admin.site.register(models.OptionGroup, OptionGroupAdmin)
admin.site.register(models.SelectedOption, SelectedOptionAdmin)
admin.site.register(models.SelectedDeliveryOption)
admin.site.register(models.DeliveryInformation)
admin.site.register(models.OnlineAddress)
admin.site.register(models.InvoiceAddress)

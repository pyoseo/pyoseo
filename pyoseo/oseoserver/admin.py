from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
import models

class OptionChoiceInline(admin.StackedInline):
    model = models.OptionChoice
    extra = 1

class OseoUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'disk_quota', 'order_availability_time',
                    'delete_downloaded_order_files',)
    fields = ('user', 'disk_quota', 'order_availability_time',
              'delete_downloaded_order_files')
    readonly_fields = ('user',)

class OptionGroupAdmin(admin.ModelAdmin):
    pass

class OrderAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('order_type', 'status', 'option_group',
                       'status_changed_on', 'completed_on', 'user',
                       'reference', 'priority', 'packaging',)
        }),
        ('Further info',{
            'classes': ('collapse',),
            'fields': ('remark', 'additional_status_info',
                       'mission_specific_status_info')
        }),
    )
    list_display = ('id', 'order_type', 'status', 'status_changed_on',
                    'show_batches',)
    list_filter = ('status', 'user',)
    readonly_fields = ('status_changed_on', 'completed_on',
                       'last_describe_result_access_request',)
    date_hierarchy = 'created_on'

class OrderItemAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('item_id', 'batch', 'status', 'option_group',
                       'status_changed_on', 'completed_on', 'downloads',
                       'identifier', 'collection_id', 'file_name',)
        }),
        ('Further info',{
            'classes': ('collapse',),
            'fields': ('remark',
                       'additional_status_info',
                       'mission_specific_status_info')
        }),
    )
    list_display = ('id', 'item_id', 'link_to_batch', 'link_to_order',
                    'status', 'status_changed_on',)
    readonly_fields = ('status_changed_on', 'completed_on', 'file_name',
                       'downloads',)

    def link_to_batch(self, obj):
        url = reverse('admin:oseoserver_batch_change', args=(obj.batch_id,))
        html = '<a href="{0}">{1}</a>'.format(url, obj.batch_id)
        return format_html(html)
    link_to_batch.short_description = 'Batch'
    link_to_batch.allow_tags = True

    def link_to_order(self, obj):
        url = reverse('admin:oseoserver_order_change',
                      args=(obj.batch.order_id,))
        html = '<a href="{0}">{1}</a>'.format(url, obj.batch.order_id)
        return format_html(html)
    link_to_order.short_description = 'Order'
    link_to_order.allow_tags = True

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
admin.site.register(models.OseoUser, OseoUserAdmin)
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

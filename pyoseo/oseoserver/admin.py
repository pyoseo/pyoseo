from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html

import models
from server import OseoServer


class ProcessorParameterInline(admin.StackedInline):
    model = models.ProcessorParameter
    extra = 1

class OseoFileInline(admin.StackedInline):
    model = models.OseoFile
    extra = 1

    def has_add_permission(self, request):
        return False


class OptionChoiceInline(admin.StackedInline):
    model = models.OptionChoice
    extra = 1


class OptionInline(admin.StackedInline):
    model = models.Option
    extra = 1


class SelectedOptionInline(admin.StackedInline):
    model = models.SelectedOption
    extra = 1


class SelectedDeliveryOptionInline(admin.StackedInline):
    model = models.SelectedDeliveryOption
    extra = 1


class SelectedPaymentOptionInline(admin.StackedInline):
    model = models.SelectedPaymentOption
    extra = 1


class SelectedSceneSelectionOptionInline(admin.StackedInline):
    model = models.SelectedSceneSelectionOption
    extra = 1


class ProductOrderConfigurationInline(admin.StackedInline):
    model = models.ProductOrderConfiguration
    extra = 1
    filter_horizontal = ('options', 'delivery_options', 'payment_options',
                         'scene_selection_options',)


class MassiveOrderConfigurationInline(admin.StackedInline):
    model = models.MassiveOrderConfiguration
    extra = 1
    filter_horizontal = ('options', 'delivery_options', 'payment_options',
                         'scene_selection_options',)


class SubscriptionOrderConfigurationInline(admin.StackedInline):
    model = models.SubscriptionOrderConfiguration
    extra = 1
    filter_horizontal = ('options', 'delivery_options', 'payment_options',
                         'scene_selection_options',)


class TaskingOrderConfigurationInline(admin.StackedInline):
    model = models.TaskingOrderConfiguration
    extra = 1
    filter_horizontal = ('options', 'delivery_options', 'payment_options',
                         'scene_selection_options',)


@admin.register(models.OseoGroup)
class OseoGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "authentication_class",)


@admin.register(models.OseoUser)
class OseoUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'oseo_group', 'disk_quota',
                    'delete_downloaded_order_files',)
    list_editable = ('oseo_group',)
    fields = ('user', 'disk_quota', 'delete_downloaded_order_files')
    readonly_fields = ('user',)


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (SelectedOptionInline, SelectedDeliveryOptionInline,)
    fieldsets = (
        (None, {
            'fields': ('order_type', 'status', 'status_changed_on',
                       'completed_on', 'user', 'reference', 'priority',
                       'packaging',)
        }),
        ('Further info', {
            'classes': ('collapse',),
            'fields': ('remark', 'additional_status_info',
                       'mission_specific_status_info')
        }),
    )
    list_display = ('id', 'status', 'status_changed_on', 'show_batches',)
    list_filter = ('status', 'user',)
    readonly_fields = ('status_changed_on', 'completed_on',
                       'last_describe_result_access_request',)
    date_hierarchy = 'created_on'


@admin.register(models.OrderPendingModeration)
class PendingOrderAdmin(admin.ModelAdmin):
    actions = ['approve_order', 'reject_order',]

    def get_queryset(self, request):
        qs = super(PendingOrderAdmin, self).get_queryset(request)
        return qs.filter(status=models.CustomizableItem.SUBMITTED)

    def get_actions(self, request):
        actions = super(PendingOrderAdmin, self).get_actions(request)
        del actions['delete_selected']
        if not request.user.is_staff:
            if 'approve_order' in actions:
                del actions['approve_order']
            if 'reject_order' in actions:
                del actions['reject_order']
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def approve_order(self, request, queryset):
        server = OseoServer()
        for order in queryset:
            server.moderate_order(order, True)
    approve_order.short_description = "Approve selected orders"

    def reject_order(self, request, queryset):
        server = OseoServer()
        for order in queryset:
            server.moderate_order(order, False)
    reject_order.short_description = "Reject selected orders"


@admin.register(models.ProductOrder)
class ProductOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status",)
    list_editable = ("status",)


@admin.register(models.SubscriptionOrder)
class SubscriptionOrderAdmin(admin.ModelAdmin):
    pass


@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    inlines = (SelectedOptionInline, SelectedDeliveryOptionInline,
               SelectedPaymentOptionInline,
               SelectedSceneSelectionOptionInline,
               OseoFileInline,)
    fieldsets = (
        (None, {
            'fields': ('item_id', 'batch', 'status',
                       'status_changed_on', 'completed_on',
                       'identifier', 'collection',)
        }),
        ('Further info',{
            'classes': ('collapse',),
            'fields': ('remark',
                       'additional_status_info',
                       'mission_specific_status_info')
        }),
    )
    list_display = ('id', 'item_id', 'link_to_batch', 'link_to_order',
                    'status', 'status_changed_on', 'additional_status_info',)
    readonly_fields = ('status_changed_on', 'completed_on',)

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


@admin.register(models.Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'available_choices',)
    inlines = [OptionChoiceInline,]


@admin.register(models.PaymentOption)
class PaymentOptionAdmin(admin.ModelAdmin):
    pass


@admin.register(models.SceneSelectionOption)
class SceneSelectionOptionAdmin(admin.ModelAdmin):
    pass


@admin.register(models.DeliveryOption)
class DeliveryOptionAdmin(admin.ModelAdmin):
    pass



@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    inlines = (ProductOrderConfigurationInline,
               MassiveOrderConfigurationInline,
               SubscriptionOrderConfigurationInline,
               TaskingOrderConfigurationInline,)
    list_display = ('name',
                    'collection_id',
                    'product_orders',
                    'massive_orders',
                    'subscription_orders',
                    'tasking_orders',)
    filter_horizontal = ('authorized_groups',)


#@admin.register(models.OrderConfiguration)
#class OrderConfigurationAdmin(admin.ModelAdmin):
#    pass


@admin.register(models.Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'price', 'created_on',
                    'completed_on', 'updated_on',)


@admin.register(models.MediaDelivery)
class MediaDeliveryAdmin(admin.ModelAdmin):
    list_display = ("package_medium", "shipping_instructions", "delivery_fee")

@admin.register(models.OrderType)
class OrderTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled", "automatic_approval",
                    "item_processor", "item_availability_days",
                    "notify_creation",)
    list_editable = ("enabled", "automatic_approval", "notify_creation",)
    readonly_fields = ("name",)
    fieldsets = (
        (None, {
            'fields': ("name", "enabled", "automatic_approval",
                       "notify_creation", "item_processor",
                       "item_availability_days",),
        }),
    )

    def has_add_permission(self, request):
        return False


@admin.register(models.ItemProcessor)
class ItemProcessorAdmin(admin.ModelAdmin):
    inlines = (ProcessorParameterInline,)


admin.site.register(models.OnlineDataAccess)
admin.site.register(models.OnlineDataDelivery)
admin.site.register(models.DeliveryInformation)
admin.site.register(models.OnlineAddress)
admin.site.register(models.InvoiceAddress)

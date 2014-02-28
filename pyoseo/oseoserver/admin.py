from django.contrib import admin
import models

admin.site.register(models.Order)
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

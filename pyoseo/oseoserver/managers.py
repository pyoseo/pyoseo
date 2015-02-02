from django.db import models

import models as oseoserver_models

class OrderPendingModerationManager(models.Manager):

    def get_queryset(self):
        return super(OrderPendingModerationManager,
                     self).get_queryset().filter(
            status=oseoserver_models.CustomizableItem.SUBMITTED)



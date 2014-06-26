'''
Custom order item processing
'''

import os

import giosystemcore.settings
import giosystemcore.files
import giosystemcore.catalogue.cswinterface
import giosystemcore.orders.orderpreparator as op

class IpmaGioProcessor(object):
    '''
    A custom order item processor that uses the giosystemcore library.

    Giosystem is IPMA's processing system for Copernicus/GIO products. It 
    defines a set of helper classes to deal with files and product generating 
    packages.
    '''

    GIOSYSTEM_SETTINGS_URL = 'http://gio-gl.meteo.pt/giosystem/settings/api/v1/'

    def identify_item(self, item_identifier):
        '''
        Get the giosystem's internal object representation of this order item.

        This method will return a GioFile object which has methods for
        searching and fetching the files from IPMA's archiving facilities.

        :arg item_identifier: Item's identifier in IPMA's gio CSW catalogue
        :type item_identifier: str
        :returns: a GioFile instance
        :rtype: giosystemcore.files.GioFile
        '''

        csw_interface = giosystemcore.catalogue.cswinterface.CswInterface()
        try:
            id, title = csw_interface.get_records([item_identifier])[0]
        except IndexError:
            logger.error('could not find order item %s in the catalogue' % \
                         order_item_id)
            raise 
        gio_file = giosystemcore.files.GioFile.from_file_name(title)
        return gio_file

    def get_online_access_output_dir(self, user_name, order_id, output_root_dir):
        '''
        Get the output directory on the filesystem where the item will be put.

        Order items that specify online access as a delivery method will be
        available for the client to come and get them from our server.

        :arg user_name: the name of the user who placed the order
        :type user_name: str
        :arg order_id: the order's unique id
        :type order_id: int
        :arg output_root_dir: The root directory for placing ordered items
                              according to the selected delivery protocol
        :type output_root_dir: str
        '''

        output_dir = os.path.join(output_root_dir, user_name,
                                  'order_{:02d}'.format(order_id))
        return output_dir

    def process_order_item_online_access(self, item_identifier, order_id,
                                         user_name, output_root_dir):
        '''
        Process an order item that specifies online access as delivery method.

        :arg item_identifier: Item's identifier in IPMA's gio CSW catalogue
        :type item_identifier: str
        :arg order_id: the order's unique id
        :type order_id: int
        :arg user_name: the name of the user who placed the order
        :type user_name: str
        :arg output_root_dir: The root directory for placing ordered items
                              according to the selected delivery protocol
        :type output_root_dir: str
        :returns: The full path to the processed order item
        :rtype: str
        '''

        giosystemcore.settings.get_settings(self.GIOSYSTEM_SETTINGS_URL,
                                            initialize_logging=False)
        gio_file = self.identify_item(item_identifier)
        out_dir = self.get_online_access_output_dir(user_name, order_id,
                                                    output_root_dir)
        preparator = op.OrderPreparator(out_dir)
        fetched = preparator.fetch(gio_file)
        # customization is not supported yet
        customized = preparator.customize(gio_file, fetched, options=None)
        moved = preparator.move(customized)
        return moved

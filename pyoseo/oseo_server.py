from ladon.ladonizer import ladonize

class OseoServer(object):

    @ladonize(rtype=unicode)
    def GetStatus(self):
        return 'this is it'

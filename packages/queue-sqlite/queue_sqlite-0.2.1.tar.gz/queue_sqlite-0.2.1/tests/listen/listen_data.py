from queue_sqlite.mounter.listen_mounter import listener


@listener()
def key_1(data):
    print(data)

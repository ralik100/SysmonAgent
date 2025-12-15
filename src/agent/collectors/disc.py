import psutil

def get_disc_usage():

    usage=psutil.disk_usage('/').percent

    return usage
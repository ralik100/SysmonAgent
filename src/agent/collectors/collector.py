import subprocess
import docker



def get_container_stats(container):

    stats = container.stats(stream=False)

    return stats
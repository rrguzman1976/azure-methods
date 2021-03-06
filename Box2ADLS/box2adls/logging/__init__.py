import logging


# Equivalent to:
# logging.basicConfig(format='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
#                     datefmt='%Y-%m-%d %I:%M:%S %p', level=logging.INFO)
root_logger = logging.getLogger(name=None)
root_logger.setLevel(logging.DEBUG)

# define a Handler which writes DEBUG messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s]: %(message)s')

# tell the handler to use this format
console.setFormatter(formatter)

# add the handler to the root logger
root_logger.addHandler(console)

# Box logging
logging.getLogger('boxsdk').setLevel(logging.ERROR)

# ADLS logging
logging.getLogger('azure.storage').setLevel(logging.ERROR)

# Azure logging
logging.getLogger('azure.core').setLevel(logging.ERROR)

# Misc logging
logging.getLogger('urllib3').setLevel(logging.ERROR)

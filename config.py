from os import getenv
import logging

class Config(object):
    API_ID = 16448144
    API_HASH = "1073665850700150caf0e0cbb68216a2"
    SESSION = "BQA_HzjQ11nSG1ZbPQB_oUoIJQ0L_XGKg9soUnvNK8KUiWaW1T-nntUbmzOgXvsJcXXqN0qFSxIeKwa1yXl80OvJUBqg3WyvlzOTiXnzZ46w-US5SYIXaZJvp8ytqHGO3hkZmWiRWAgDdezrCRdJF17mY32YUIhpvZ19WXMOk_qqW_Tg11JmXe_dQKiSKU96nMDjVZB7tdPYDV_kQSMAqT-XLmi8dXNJ2Sy0YfUHhBAq1-WI84l_YpAuf5U_xjmViC8ujkSA1Zo7yLOsOG4YYH8vBgp9vXXJmbGcRdd1POAyQfN3fIZPbty-synpmKJQv5WbiYpA7dtxnlTCTC7JpSveAAAAAXQYkX8A"
    CHANNEL_ID = -1001912424642

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

import sys
import os

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))

sys.path.insert(0, project_root)
# ==================================================================

from daaskit.sdk import sql, sqlhelper
from daaskit.sdk.log import logger

db = sql.DB()
result = sqlhelper.update(db, "delete from meta_test where id = ?", [1])
logger.info(f'{type(result)} result={result}')

# ENV_BACKEND_HOST='http://localhost:8080' ENV_EXT_API_HOST='http://localhost:8082' ENV_EXT_API_INDEXES='db.execute:476b3000-4dc8-49c3-afdf-2f0d82fb8256' python db_test.py

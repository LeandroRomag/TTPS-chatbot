import os
import sys
import locale
from dotenv import load_dotenv
load_dotenv()
print('sys.getdefaultencoding():', sys.getdefaultencoding())
print('sys.getfilesystemencoding():', sys.getfilesystemencoding())
print('locale.getpreferredencoding(False):', locale.getpreferredencoding(False))
print('cwd repr:', repr(os.getcwd()))
# show environment vars that psycopg2 may use
for k in ('PGHOST','PGPORT','PGUSER','PGPASSWORD','PGDATABASE','PGPASSFILE','HOME','USERPROFILE'):
    print(f"{k}: {repr(os.getenv(k))}")

# read the config-built URL
try:
    from src.core.config import DevelopmentConfig
    engine_url = DevelopmentConfig.SQLALCHEMY_ENGINES.get('default')
    print('engine_url repr:', repr(engine_url))
except Exception as e:
    print('Could not import DevelopmentConfig:', e)
    engine_url = None

# Try to connect with psycopg2
try:
    import psycopg2
    print('psycopg2 imported, version', psycopg2.__version__)
    if engine_url:
        print('\nAttempting psycopg2.connect() with engine_url as DSN...')
        try:
            conn = psycopg2.connect(engine_url)
            print('connected ok (surprising)')
            conn.close()
        except Exception as e:
            print('psycopg2.connect raised:', type(e), e)
            # if UnicodeDecodeError, show details
            if isinstance(e, UnicodeDecodeError):
                print('uname:', e.encoding, e.start, e.end, e.reason)
except Exception as e:
    print('psycopg2 import/connect attempt failed:', e)

print('\nDone')

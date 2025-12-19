import os
import sys
import traceback

from flask import session

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, admin_account_access


def main() -> None:
    print('Starting debug_account_access_page...')
    ctx = None
    try:
        ctx = app.test_request_context('/admin/account-access')
        ctx.push()
        session['logged_in'] = True
        session['role'] = 'admin'
        session['user_id'] = 1

        resp = admin_account_access()
        print('Returned type:', type(resp))
        print('Returned:', resp)
    except Exception:
        print('Exception occurred:')
        traceback.print_exc()
        return
    finally:
        try:
            if ctx is not None:
                ctx.pop()
        except Exception:
            pass


if __name__ == '__main__':
    main()

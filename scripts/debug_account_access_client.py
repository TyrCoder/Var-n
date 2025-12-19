import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app


def main() -> None:
    # In testing mode, Flask will propagate exceptions so we get the real traceback.
    app.testing = True

    with app.test_client() as c:
        with c.session_transaction() as s:
            s['logged_in'] = True
            s['role'] = 'admin'
            # Use whatever admin id exists in your DB; 1 is common.
            s['user_id'] = 1

        try:
            r = c.get('/admin/account-access')
            print('status:', r.status_code)
            print('location:', r.headers.get('Location'))
            body = r.get_data(as_text=True)
            print('body_head:', body[:500])
        except Exception:
            print('EXCEPTION during request:')
            traceback.print_exc()


if __name__ == '__main__':
    main()

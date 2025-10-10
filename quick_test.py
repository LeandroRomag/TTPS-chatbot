from app import app


def main():
    with app.test_client() as c:
        # Health endpoint
        h = c.get('/health')
        print('GET /health ->', h.status_code, h.json)
        assert h.status_code == 200
        assert h.json.get('status') == 'ok'

        # Example endpoint
        e = c.get('/api/message/example')
        print('GET /api/message/example ->', e.status_code, e.json)
        assert e.status_code == 200
        assert 'reply' in e.json

        # Post message OK
        m = c.post('/api/message', json={'message': ' Hola mundo '})
        print('POST /api/message ->', m.status_code, m.json)
        assert m.status_code == 200
        assert m.json.get('ok') is True
        assert m.json.get('cleaned') == 'Hola mundo'
        assert 'reply' in m.json

        # Post missing field
        mf = c.post('/api/message', json={})
        print('POST /api/message (missing) ->', mf.status_code, mf.json)
        assert mf.status_code == 400

        # Wrong content-type
        wc = c.post('/api/message', data='no json', headers={'Content-Type': 'text/plain'})
        print('POST /api/message (wrong content) ->', wc.status_code, wc.json)
        assert wc.status_code == 415

    # Chat page
    ch = c.get('/chat')
    print('GET /chat ->', ch.status_code, ch.content_type)
    assert ch.status_code == 200
    assert 'text/html' in (ch.content_type or '')

    # List chunks (may be empty in a fresh db)
    l = c.get('/api/chunks')
    print('GET /api/chunks ->', l.status_code)
    assert l.status_code == 200

    # Preview retrieval (empty query)
    p = c.get('/api/preview?q=hola')
    print('GET /api/preview ->', p.status_code)
    assert p.status_code == 200

    print('Smoke test OK')


if __name__ == '__main__':
    main()

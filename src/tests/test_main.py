from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from main import app
import db


@patch("sms.aero.send_bool", AsyncMock(return_value=True))
def test_signup(client, volunteer):
    query = f"""
    mutation {{
      signUp(phone: "{volunteer.phone}") {{
        status}}}}
    """
    with patch("gql.make_password", lambda: volunteer.password):
        response = client.post('/', json={"query": query})
        assert response.status_code == 200


def test_token_lifecycle(client, volunteer, dbe):
    refresh_token = None

    # 1) get token
    qget = f"""
    mutation {{
      getToken(phone: "{volunteer.phone}",
               password: "{volunteer.password}") {{
        accessToken
        expiresAt}}}}
    """
    response = client.post('/', json={"query": qget})
    assert response.status_code == 200
    assert "refresh_token" in response.cookies
    refresh_token = response.cookies["refresh_token"]

    # 2) refresh_token
    qrefresh = """
    mutation {
      refreshToken {
        accessToken
        expiresAt}}
    """
    response = client.post(
        '/',
        json={"query": qrefresh},
        cookies={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "refresh_token" in response.cookies
    assert response.cookies["refresh_token"] != refresh_token
    blacklisted = dbe.execute(db.miserables.select()).fetchone()
    assert blacklisted
    assert blacklisted[0] == refresh_token
    refresh_token = response.cookies["refresh_token"]

    # 3) logoff
    query = """mutation {logoff {status}}"""
    response = client.post('/',
                           json={"query": query},
                           cookies={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "refresh_token" not in response.cookies

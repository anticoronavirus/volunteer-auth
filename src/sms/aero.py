import logging
import conf
import aiohttp


logger = logging.getLogger(__name__)
auth = aiohttp.BasicAuth(conf.AERO_LOGIN, conf.AERO_TOKEN)


async def send(phonestr, from_, text):
    params = {
        "number": phonestr,
        "sign": from_,
        "text": text,
        "channel": "DIRECT"
    }

    logger.info("sending %s", params)

    async with aiohttp.ClientSession(auth=auth) as s,\
               s.post(f"{conf.AERO_URL}/sms/send/",
                      json=params) as resp:
        body = await resp.json()
        logger.info("response body: %s", body)
        return body


async def send_bool(phonestr, from_, text):
    resp = await send(phonestr, from_, text)
    return resp["success"] == True

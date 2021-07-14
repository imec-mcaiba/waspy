from typing import List

import asyncio
import logging
import app.hardware_controllers.http_helper as http

logging.basicConfig(level=logging.INFO, filename="debug.log")
faker = False
faker_time = 0.2


async def wait_for_request_done(url, request):
    if faker:
        await asyncio.sleep(faker_time)
        return
    while True:
        await asyncio.sleep(0.2)
        response = await http.get_json(url)
        error_message = response["error"]
        if error_message == "Success" or error_message == "No error":
            if response['request_finished'] and response["request_id"] == str(request["request_id"]):
                break
        else:
            raise Exception(url + ": " + error_message)


async def post_request(url, request):
    logging.info("post to: " + url + ", content: " + str(request))
    if faker:
        await asyncio.sleep(faker_time)
        return

    await http.post_dictionary(url, request)
    await wait_for_request_done(url, request)


async def set_motrona_target_charge(request_id, url, target_charge):
    motrona_request = {"request_id": request_id, "target_charge": target_charge}
    await post_request(url, motrona_request)


async def move_aml_first(request_id, url, position):
    aml_request = {"request_id": request_id, "set_m1_target_position": position}
    await post_request(url, aml_request)


async def move_aml_second(request_id, url, position):
    aml_request = {"request_id": request_id, "set_m2_target_position": position}
    await post_request(url, aml_request)


async def move_aml_both(request_id, url, positions):
    aml_request = {"request_id": request_id, "set_m1_target_position": positions[0],
                   "set_m2_target_position": positions[1]}
    await post_request(url, aml_request)


async def clear_start_motrona_count(request_id, url):
    """ When the motrona counting is active, a gate signal will enable the caen acquisition.
    For this to work, the caen acquisition has to be started aka 'armed' """
    motrona_request = {"request_id": request_id, "clear-start_counting": True}
    await post_request(url, motrona_request)


async def pause_motrona_count(request_id, url):
    motrona_request = {"request_id": request_id, "pause_counting": True}
    await post_request(url, motrona_request)


async def motrona_counting_done(url):
    if faker:
        await asyncio.sleep(faker_time)
        return
    while True:
        await asyncio.sleep(1)
        response = await http.get_json(url)
        if response["status"] == "Done":
            logging.info("motrona counting done")
            break


async def stop_clear_and_arm_caen_acquisition(request_id, url):
    request = {'request_id': request_id, 'stop_acquisition': True, 'clear': True, 'start_acquisition': True}
    await http.post_dictionary(url, request)
    await wait_for_request_done(url, request)


async def stop_caen_acquisition(request_id, url):
    request = {'request_id': request_id, 'stop_acquisition': True}
    await post_request(url, request)


async def get_caen_histogram(base_url, board: int, channel: int) -> List[int]:
    if faker:
        await asyncio.sleep(2)
    url = base_url + "/histogram/" + str(board) + "-" + str(channel)
    raw_data = await http.get_text(url)
    raw_data = raw_data.split(";")
    raw_data.pop()
    data = [int(x) for x in raw_data]
    return data

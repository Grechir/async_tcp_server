import asyncio
import random
from datetime import datetime

SERVER_ADDRESS = ('127.0.0.1', 9090)
TIMEOUT_SEC = 2  # random timeout


async def logger(log_file, request_time, request_message, response_time, response_message):
    with open(log_file, 'a', encoding='utf-8') as lf:
        if 'keepalive' in response_message:
            lf.write(f'{response_time}; {response_message}')
        else:
            try:
                lf.write(f'{request_time}; {request_message};'
                         f' {response_time}; {response_message}'.replace('\n', '', 1))
            except asyncio.TimeoutError:
                lf.write(f'{request_time};{request_message};'
                         f'{response_time};(таймаут)')


async def client(client_id):
    # clients and logs creating
    reader, writer = await asyncio.open_connection(*SERVER_ADDRESS)
    log_file = f"logs/client_{client_id}_log.txt"
    request_num = 0

    try:
        while True:
            await asyncio.sleep(random.uniform(0.3, 3))

            # sends a request
            request_message = f'[{request_num}] PING\n'
            request_time = datetime.now().strftime('%Y-%m-%d;%H:%M:%S.%f')[:-3]
            writer.write(request_message.encode('ascii'))
            await writer.drain()

            # receives a response
            try:
                data = await asyncio.wait_for(reader.readuntil(b'\n'), timeout=TIMEOUT_SEC)

                if data:
                    response_message = data.decode('ascii')
                    response_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    await logger(
                        log_file,
                        request_time,
                        request_message,
                        response_time,
                        response_message
                    )
                else:
                    break

            except asyncio.TimeoutError:
                await logger(
                    log_file,
                    request_time,
                    request_message,
                    TIMEOUT_SEC,
                    '(таймаут)\n'
                )

            request_num += 1
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    # running two clients in parallel
    await asyncio.gather(
        client(1),
        client(2),
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

import asyncio
import random
from datetime import datetime

SERVER_ADDRESS = ('127.0.0.1', 9090)


class Server:
    def __init__(self):
        self.client_counter = 0
        self.response_counter = 0
        self.response_counter_lock = asyncio.Lock()

    @staticmethod
    async def logger(request_time, request_message, response_time=None, response_message=None):
        with open('logs/server_log.txt', 'a', encoding='utf-8') as log_file:
            if response_message is None:
                log_file.write(f'{request_time}; {request_message}; (проигнорировано)\n')
            else:
                log_file.write(f'{request_time};{request_message};{response_time};{response_message}')

    async def client_connection(self, reader, writer):
        self.client_counter += 1
        client_id = self.client_counter

        request_counter = 0

        async def send_keepalive():
            while True:
                await asyncio.sleep(5)
                keepalive_message = f'[{self.response_counter}] keepalive\n'
                self.response_counter += 1
                writer.write(keepalive_message.encode('ascii'))
                await writer.drain()

        send_keepalive_message = asyncio.create_task(send_keepalive())

        try:
            # client request
            while True:
                data = await reader.read(1024)
                if not data:
                    break

                request_time = datetime.now().strftime('%Y-%m-%d;%H:%M:%S.%f')[:-3]
                request_message = data.decode('ascii').strip('\n')

            # client response
                if random.random() < 0.1:
                    await self.logger(request_time, request_message,)  # recording logs
                    request_counter += 1  # the request was ignored, but the fact of the request is recorded in the logs
                    continue

                await asyncio.sleep(random.uniform(0.1, 1))

                response_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                async with self.response_counter_lock:  # blocking before updating response_counter
                    response_message = f'[{self.response_counter}/{request_counter}] PONG ({client_id})\n'
                    self.response_counter += 1

                request_counter += 1

                writer.write(response_message.encode('ascii'))
                await writer.drain()

                await self.logger(  # recording logs
                    request_time,
                    request_message,
                    response_time,
                    response_message
                )
        except asyncio.CancelledError:
            pass
        finally:
            send_keepalive_message.cancel()
            writer.close()
            await writer.wait_closed()


async def main():
    server = Server()
    open_server = await asyncio.start_server(server.client_connection, *SERVER_ADDRESS)
    async with open_server:
        await open_server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

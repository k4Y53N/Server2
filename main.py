from src.Server import Server, ServerBuilder
import logging as log

if __name__ == '__main__':
    log.basicConfig(
        format='%(asctime)s %(levelname)s:%(message)s',
        datefmt='%Y/%m/%d %H:%M:%S',
        level=log.INFO
    )
    builder = ServerBuilder('./sys.ini')
    server = Server(builder)
    try:
        server.run()
    except (KeyboardInterrupt, Exception) as e:
        pass
    finally:
        server.close()
        server.close_phase()

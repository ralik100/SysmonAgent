import loop
import logger

def main():
    logger.init()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    finally:
        logger.close()


if __name__ == "__main__":
    main()

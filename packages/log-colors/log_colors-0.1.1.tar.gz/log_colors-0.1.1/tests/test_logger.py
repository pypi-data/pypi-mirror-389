from log_colors import log_colors 

def test_outputs(logger):
    logger.info("This is info")
    logger.error("This is error")
    logger.success("This is success")
    logger.warning("This is a warning")

def test_console_log():
    test_outputs(log_colors())

def test_file_log():
    with open("./tests/test_log.txt", "w"):
        test_outputs(log_colors(log_file="./tests/test_log.txt"))

if __name__ == "__main__":
    test_console_log()
    test_file_log()

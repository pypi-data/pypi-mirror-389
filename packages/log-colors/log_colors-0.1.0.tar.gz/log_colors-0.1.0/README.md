log_colors is a simple logging library that allows you to log in color.

### Creation
The logger can be instantiated in one of the following ways:
```python
# For the default use case
logger = log_colors()

# With a custom class name
logger = log_colors(filename="Custom Name")

# Setup to save to a file
logger = log_colors(log_file="/path/to/file")
```

### Usage
There are four logging methods
```python
# For a general message
logger.info("Info message")

# For an error message
logger.info("Error message")

# For a success message
logger.success("Success message")

#For a warning message
logger.warning("Warning message")
```

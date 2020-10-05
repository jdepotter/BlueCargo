# BlueCargo

## Requirements
I have used requests library to pull the content of a page and Beautiful soup (bs4) library to scrap it.

## Implementation
Jobs are implemented as classes that inherit a common class. These jobs are called by the main file bluecargo.py but they could also be deployed easily on an aws lambda.

## How to run
Execute `sh run.sh`
This will install bs4 and requests libraries and then run the program
If the librabries are already installed, you can run the pogram with `python3 bluecargo.py`

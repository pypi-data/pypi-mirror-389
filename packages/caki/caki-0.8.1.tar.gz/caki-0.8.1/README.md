Caki is a Python tool that automatically installs pip packages if you try to run them and they are missing.  

## Example

```bash
caki black --version
caki python main.py

## This should either log black's version, or install then log
## The second command will scan main's dependencies and then run
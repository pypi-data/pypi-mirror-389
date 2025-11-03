# tracebackSilencer
## A python package for silencing the anyoing tracebacks
### **Here is a coding example:**

```py

from Packages import tracebackSilencer

ts = tracebackSilencer.Silencer()
ts.activate(__file__)
sfdihjur
print("Hello, World")
```
**The Output Will Be:**
```
/home/th3ou1d3x/Hehe/.venv/bin/python /home/th3ou1d3x/Hehe/Haha.py 
Using Traceback Silencer
By: Anthony R. + Avash K.
Hello, World

Process finished with exit code 1
```
*You Can Also Optionaly Use ts.debug(True) before activation in that code that was given to get debug prints and a debug report*
#### This is very useful but because it uses its own code parser at the current time functions , variables and classes may have some trouble
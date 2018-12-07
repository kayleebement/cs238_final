# this will run 10 simulations of the hurricane
# you need to choose whether it's charley or andrew in the other file tho :// lame lame
filename = "hurricane.py"
for i in range(10):
    exec(compile(open(filename, "rb").read(), filename, 'exec'))
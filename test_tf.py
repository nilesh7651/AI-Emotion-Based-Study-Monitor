import sys

try:
    import tensorflow
except Exception as e:
    import traceback
    with open("tf_debug.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)

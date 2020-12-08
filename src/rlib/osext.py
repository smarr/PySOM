import os


def path_split(path):
    """This is a replacement for the combined use of os.path.split and
       os.path.splitext to decompose a relative path into its components.
    """
    path_and_file = path.rsplit(os.sep, 1)
    if len(path_and_file) <= 1:
        path = ""
    else:
        path = path_and_file[0]
    file_and_ext  = path_and_file[-1].rsplit(".", 1)
    if len(file_and_ext) <= 1:
        ext = ""
    else:
        ext = file_and_ext[-1]
    file_name = file_and_ext[0]
    return path, file_name, ext


def _read_raw(answer):
    buf = os.read(1, 32)
    if len(buf) == 0:
        return answer, False
    elif buf[-1] == "\n":
        return answer + buf[:-1], False
    else:
        return answer + buf, True


def raw_input(msg = ""):
    os.write(1, msg)
    answer, cont = _read_raw("")
    while cont:
        answer, cont = _read_raw(answer)
    return answer

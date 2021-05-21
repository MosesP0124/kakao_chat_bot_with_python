COMMAND_LIST = ['박모세']

def command_body(command_word,sub_cmd='',deco='',*args):
    cmd_response = ''
    if command_word == "박모세":
        if sub_cmd:
            cmd_response = cmd_moses(sub_cmd)
        else:
            cmd_response = cmd_moses()
    if cmd_response == '':
        return "해당하는 명령어가 없습니다.\n명령어 리스트: %s" % str(COMMAND_LIST)
    return cmd_response

def cmd_moses(*cmd):
    sub_cmd = "Default"
    if cmd:
        sub_cmd = cmd[0]
    return "박모세의 %s 함수입니다." % sub_cmd